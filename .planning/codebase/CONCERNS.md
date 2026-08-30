# Codebase Concerns

**Analysis Date:** 2026-08-30

---

## Tech Debt

### Contract Drift Between Backend Schemas and Frontend Types

The most significant structural debt is the **hand-maintained TypeScript contract** at `frontend/types/api.ts`. The export script `scripts/export_openapi.py` explicitly acknowledges this is NOT generated from the OpenAPI schema — it re-emits a static template verbatim so that CI diffs detect direct edits to the canonical copy, but it **cannot catch drift between the FastAPI schema and the TS interfaces** (`scripts/export_openapi.py` lines 17-23). Until real codegen (e.g., `openapi-typescript` or `datamodel-code-generator`) is adopted, schema-to-TS drift must be caught by human review of `contracts/openapi.json` diffs.

**Specific mismatches identified:**

- **`DataMode` type gap:** `frontend/types/api.ts` defines `DataMode = "live" | "recorded_demo" | "test_fixture" | "benchmark"`, but the `DataModeBadge` component (at `frontend/components/common/DataModeBadge.tsx` line 14) checks `mode === 'synthetic'`, which is **not a valid member** of the `DataMode` type. The backend `DataMode` enum (`backend/app/schemas/intelligence.py` line 8-13) also lacks `"synthetic"` — only `LIVE`, `RECORDED_DEMO`, `TEST_FIXTURE`, `BENCHMARK`. The frontend mapper (`frontend/lib/mappers.ts` line 139) sets `data_mode = 'test_fixture'` when `is_synth` is true, but this value may not be consistent with what the backend returns in all cases.

- **`ConfidenceType` enum asymmetry:** Backend has `CONTRADICTION = "nli_heuristic"` (line 19) while frontend defines `"nli_heuristic"` as a standalone value (line 14). The backend also defines `CLASSIFICATION = "classification"` but the frontend `ConfidenceType` union includes `"classification"` without the `CONTRADICTION` alias. Both resolve to the same string values at runtime, but enum name divergence creates confusion.

- **`ScoreBreakdown` legacy fields:** The frontend `ScoreBreakdown` interface includes legacy compatibility fields (`impact`, `urgency`, `evidence_strength`, `strategic_relevance`, `routing_relevance`, `total_score`) that are **not present in the backend `Signal` model** (`backend/app/models/__init__.py`). These fields appear in the TS type but have no corresponding backend columns.

- **`Signal` interface field divergence:** The frontend `Signal` interface includes fields like `id`, `summary`, `severity`, `status`, `score`, `detectedAt`, `tags`, `sources`, `stakeholders` that are **not present in the backend `Signal` SQLAlchemy model**. These are UI-computed or mapped properties, but the lack of a shared contract definition means the mapping in `frontend/lib/mappers.ts` is the sole source of truth for these fields, with no automated validation.

### Synthetic vs Live Data Gaps

- **`data_mode` / `is_synthetic` consistency:** The `Signal` model (`backend/app/models/__init__.py` line 252-253) has `data_mode = Column(String(50), default="live")` and `is_synthetic = Column(Boolean, default=False)`, but there is **no database constraint** ensuring these two fields are consistent. A row could have `data_mode="live"` AND `is_synthetic=True`, or vice versa.
- **`data_mode` validation gap:** The backend `DataMode` enum does not include `"synthetic"` as a valid value, but the frontend mapper sets `data_mode = 'test_fixture'` when `is_synth` is true. If a backend API response includes a `data_mode` value that the frontend `DataMode` type doesn't accept, TypeScript will produce a type error or silent fallback.
- **`pii_scrubbed` field mismatch:** The frontend `Signal` interface includes `pii_scrubbed?: boolean` (line 118 of `api.ts`), but the backend `Signal` model does **not** have a `pii_scrubbed` column. This field is likely derived from `RawSignalBronze.raw_payload`, but there is no explicit mapping documented.

---

## Performance Bottlenecks

### Local LLM on CPU (Gemma 3 4B)

The primary inference path runs `google/gemma-3-4b-it` locally via either Ollama daemon or llama-cpp-python with a GGUF quantized model. In the default docker-compose configuration (`docker-compose.yml` line 44), `LLM_DEVICE=cpu` is set for the backend service, meaning inference runs entirely on CPU.

**Constraints identified in `backend/app/providers/gemma.py`:**
- `n_threads = min(os.cpu_count() or 8, 12)` — capped at 12 threads for CPU inference (line 118).
- `MAX_CONTEXT_TOKENS=2048` and `MAX_OUTPUT_TOKENS=512` — these are extremely small windows that limit the complexity of analysis the model can perform (config.py lines 56-57).
- The GGUF loader uses `n_batch=512` and `f16_kv=True` (line 129), which are reasonable defaults but may not be optimal for all CPU architectures.
- When `LLM_DEVICE="auto"` or `"cuda"`, `n_gpu_layers` defaults to `-1` (all layers on GPU) only if `LLM_GPU_LAYERS` env var is set or `settings.LLM_DEVICE in ("cuda", "gpu", "auto")` — otherwise `n_gpu=0`, meaning **all layers stay on CPU even when a GPU is available** unless explicitly configured.

**Embedding service** (`backend/app/services/embeddings.py`) uses fastembed (ONNX runtime, CPU-only). Every embedding call offloads to `asyncio.get_running_loop().run_in_executor`, which means CPU-bound embedding work competes with the async event loop for thread pool resources. With `pool_size=10, max_overflow=20` (session.py line 16), there are at most 30 DB connections but the thread pool for embedding executor is unbounded by default.

### External API Rate Quotas

**NewsAPI** (`backend/app/connectors/newsapi.py`): The dev cap is ~100 requests/day (line 23). The quota governor checks `quota_remaining < 15` in the scheduler (scheduler.py line 141) and forces a 90-minute backoff. However, the `_read_quota` method (line 155) falls back to `default_quota = 100` if the cursor is missing or unparseable, meaning **a fresh state assumes full quota even if the real quota has been partially consumed**. The quota tracking relies on the `X-RateLimit-Remaining` response header — if NewsAPI changes this header or it's absent, the fallback decrement logic (`quota_remaining = max(0, (quota_remaining or 100) - 1)` on line 112) only decrements by 1 per call, which may not match the actual API's counting.

**NCBI PubMed** (`backend/app/connectors/pubmed.py`): PubMed E-utilities are "quota-free" but enforce rate limits implicitly. The `BATCH_DELAY_S=0.35` between batches (line 36) is a polite delay but does not prevent NCBI from throttling requests if the rate exceeds their undocumented limits. The `NCBI_API_KEY` is optional but recommended for higher limits (line 78).

**Grok/xAI**: No rate limit handling in the provider itself. The `httpx.Timeout(60.0, connect=5.0)` (grok.py line 53) provides a 60-second read timeout but no retry logic with backoff is implemented at the provider level — it relies on the `_fetch_with_retry` in the base connector.

### Scheduler Concurrency and Resource Contention

The `SourceScheduler` (`backend/app/services/scheduler.py`) creates one `asyncio.Task` per connector (line 91-95), all running concurrently. There is **no semaphore or global concurrency limit** on how many connectors can fetch simultaneously. With 8 connectors (pubmed, clinical_trials, ema, fda, newsapi, fierce_pharma, et_pharma, biopharmadive), all could be fetching at the same time, consuming:
- Multiple concurrent HTTP connections to external APIs
- Multiple concurrent DB sessions (each `_connector_worker_loop` creates its own `async_session_factory()` session on every cycle)
- Pipeline runner triggers (`PipelineRunner(session=pipe_session)`) after each connector finds new records — if multiple connectors discover new data simultaneously, **multiple overlapping pipeline runs** could execute concurrently with no coordination

---

## Security Considerations

### Session Cookie Security

**`SESSION_COOKIE_SECURE: bool = False`** is the default in `backend/app/core/config.py` line 37. This means session cookies are transmitted over unencrypted HTTP in the default development configuration. The cookie is set in `backend/app/api/v1/endpoints/auth.py` line 47-54 via `response.set_cookie(..., secure=settings.SESSION_COOKIE_SECURE, ...)`. In production with `SESSION_COOKIE_SECURE=True`, the cookie would only be sent over HTTPS — but the default `False` means cookies can be intercepted on HTTP.

**`SECRET_KEY: str = "dev-secret-change-in-production"`** — hardcoded default (line 34). This key is used for:
1. Signing session tokens via `itsdangerous.TimestampSigner` (`security.py` line 40-43)
2. Generating CSRF tokens via HMAC-SHA256 (`security.py` line 55-60)
3. Session validation in `auth_service.py`

If this default key is not changed in production, **anyone who knows the default can forge session tokens and CSRF tokens**.

**Demo mode credentials:** `DEMO_MODE: bool = True` (line 38) and `DEMO_AUTO_SEED_USERS: bool = True` (line 39) are defaults. Demo passwords are auto-generated at runtime (`auth_service.py` line 60-68) and printed to stdout (`print(f"[MetaRadar Security] Demo password generated...")`), which leaks credentials to logs. The demo personas have hardcoded emails in `auth_service.py` lines 22-55.

### Third-Party LLM Data Privacy

The `GrokProvider` (`backend/app/providers/grok.py`) implements a privacy gate (`validate_privacy_gate`) that only allows `PUBLIC` or `SYNTHETIC` classified data to reach `api.x.ai` (line 64). `CONFIDENTIAL` and `UNKNOWN` classifications are blocked. However:
- The `DataClassification` enum (`backend/app/providers/base.py`) determines what can be sent externally. If the classification logic in `PIIPHIScrubber.classify_payload` (`backend/app/services/pii.py` line 35-46) misclassifies PII-containing text as `PUBLIC` (e.g., if the PII patterns don't match), that data could be transmitted to xAI.
- The regex patterns in `PIIPHIScrubber` (line 5-11) are basic and may not catch all PII variants (e.g., international phone formats, complex addresses, medical record numbers with different formats).
- The `effective_xai_api_key` property (`config.py` line 65-66) resolves from multiple sources (`XAI_API_KEY`, `GROK_API_KEY`, `effective_xai_api_key`), and if any of these environment variables are set to a real key, the `GrokProvider` will use it when the factory's `has_grok_key` check passes. There is **no audit log** of when external API calls are made.

**The `_chat` method in `GrokProvider` (line 70-115) sends the full evidence payload as a JSON body to `https://api.x.ai/v1/chat/completions`.** If any evidence contains PII that was not caught by the scrubber, it is transmitted externally. The privacy gate is a single point of failure — if `classification` is wrong, the gate is bypassed.

### CSRF and Pre-Auth Security

The auth system uses HMAC-SHA256 bound CSRF tokens (`security.py` line 55-60), which is cryptographically sound. The pre-auth origin check (`backend/app/api/deps.py` — referenced in `auth.py` line 139) validates `Origin`/`Referer` headers. However:
- The `CORS_ORIGINS` defaults to `http://localhost:3000` (config.py line 42) — this is HTTP, not HTTPS.
- The `SecurityHeadersMiddleware` (`middleware.py` line 76-97) sets `script-src 'self' 'unsafe-inline'` which allows inline scripts — a CSP weakness that could be exploited via XSS if any template injection vulnerability exists.

---

## Fragile Areas

### Multi-Worker Scheduler Singleton Pattern

The `SourceScheduler` uses a singleton pattern (`_instance: Optional["SourceScheduler"]`, scheduler.py line 48, `get_instance()` lines 57-61). This creates a critical fragility in multi-worker deployments:

- **Problem:** If the application is served with multiple uvicorn/gunicorn workers (e.g., `workers=4`), each worker process creates its **own independent `SourceScheduler` instance** with its own `asyncio.Task` loop. The PostgreSQL advisory lock (`try_advisory_lock`) prevents duplicate execution of the same connector, but **each worker still spawns a full set of asyncio tasks** that immediately compete for the lock. The `SKIPPED_LOCKED` status means workers waste event loop cycles acquiring and releasing locks.
- **Impact:** In a multi-worker setup, N workers × 8 connectors = 8N concurrent task loops, all hammering the DB with advisory lock attempts on every cycle interval.
- **Fix approach:** The scheduler should be started in exactly one worker process, or replaced with a proper distributed task queue (e.g., Celery with Redis, or SQLAlchemy-based advisory lock leader election).

### Pipeline Runner Overlap

When a connector discovers new records, the scheduler triggers `PipelineRunner.run(batch_size=50)` (scheduler.py lines 183-187). If multiple connectors find new records simultaneously, or if the same connector's cycle triggers while a previous pipeline run is still executing, **concurrent pipeline runs** could overlap. There is no pipeline run concurrency guard. The `PipelineRunner` itself (`backend/app/workflows/runner.py`) should be checked for thread-safety, but the scheduler has no mechanism to prevent overlapping invocations.

### Session Concurrency

The `get_session_user` function (`auth_service.py` lines 166-209) reads and updates `last_activity_at` in the same session without an explicit row lock. Under concurrent requests from the same session (e.g., multiple tab pages), this could lead to **lost updates** on `last_activity_at`, causing premature session expiration. The `expire_on_commit=False` setting in `async_sessionmaker` (session.py line 23) means the session object stays in memory after commit, but concurrent requests each create their own session, so they each read the same `last_activity_at` and then overwrite it.

### Provider Fallback Chain Race

The `ProviderFactory.execute_task` method (factory.py lines 19-48) implements a fallback chain: Gemma → Grok → BART Degraded. Each provider is instantiated at factory construction time (`self.gemma = GemmaProvider()`, etc.). The `GemmaProvider._client` is lazily created but **shared across all calls**. If one call is in progress and the client times out, subsequent calls may reuse the same `httpx.AsyncClient` that is in a bad state. The `aclose` method (line 85-89) exists but is not called in the fallback chain — the client is never explicitly closed.

---

## Scaling Limits

### pgvector Vector Storage Capacity

The `Signal` model (`backend/app/models/__init__.py` line 294) stores embeddings as `Vector(settings.EMBEDDING_DIMENSION)` where `EMBEDDING_DIMENSION=384`. The HNSW index `signals_embedding_hnsw` is used for cosine similarity search. Known scaling limits:

- **Memory:** pgvector HNSW indexes load into shared_buffers and working_set. At 384 dimensions with float32, each vector is ~1.5KB. With 1M signals, the index alone requires ~1.5GB + overhead. With 10M signals, this exceeds typical shared_buffers defaults (128MB-1GB).
- **Query performance:** Cosine distance searches degrade as the dataset grows beyond the HNSW's effective memory resident set. The `ef_search` parameter (default 40, max 1000 per the search endpoint) trades recall for speed — higher values are slower on large datasets.
- **No partitioning strategy:** The `Signal` table has no partitioning by date, source, or any other dimension. A single massive table will slow all queries including the vector search, the keyword search, and the numerous indexes (14 indexes defined on `Signal`, lines 303-316).
- **Embedding staleness:** There is no mechanism to re-embed signals when the embedding model changes. The `embedding_model_version` column tracks the version, but no background job recomputes embeddings on model updates.

### Database Connection Pool

`backend/app/db/session.py` configures `pool_size=10, max_overflow=20` (total 30 connections). Each scheduler worker cycle creates a new session via `async_session_factory()`, and the pipeline runner creates another. With multiple concurrent connectors and pipeline runs, the pool can be exhausted, causing connection wait timeouts.

### External API Hard Limits

- **NewsAPI:** ~100 requests/day (dev plan). At `SCHEDULER_NEWS_INTERVAL_MINUTES=15` (config.py line 108), the scheduler checks every 15 minutes (96 checks/day). With quota awareness at `< 15`, the effective usable quota is ~85 requests. If each connector cycle uses 1 request, that's ~85 usable cycles per day before hitting the quota wall.
- **PubMed/NLM:** No hard documented limit for non-commercial use, but aggressive polling (60-minute intervals with 200-result batches) may trigger rate limiting.
- **Local LLM:** `MAX_CONTEXT_TOKENS=2048` limits input to ~2K tokens. For multi-document evidence analysis, this severely constrains the amount of context the model can process in a single call.

---

## Test Coverage Gaps

### Live Network Integration Testing

- `tests/test_providers_live.py` (`test_grok_live_structured_output`) requires `LIVE_XAI_KEY` env var and makes a real API call to xAI. It is skipped in CI by default (`@pytest.mark.skipif(not os.getenv("LIVE_XAI_KEY"), ...)`). There is **no automated live test for the local Gemma provider** — all Gemma tests use mocking (`test_gemma_stream.py`).
- `scripts/test_live_ingestion_e2e.py` is a standalone script, not a pytest test. It requires a running full stack and makes real network calls to PubMed, clinical_trials, FDA, and EMA. It is not invoked by any CI pipeline.
- `tests/test_connector_health.py` tests connector parsing with mocked responses (e.g., `test_biopharmadive_rss_parsing` uses synthetic XML). No connector is tested against its live API.

### Multi-Worker Scheduler Testing

There are **no tests** for the `SourceScheduler` behavior in multi-worker or concurrent execution scenarios. The existing test in `test_connector_health.py` (`test_newsapi_quota_governor_logic`) only checks that the scheduler instance exists and has the expected job keys — it does not verify lock contention behavior, concurrent cycle prevention, or the `SKIPPED_LOCKED` path.

### Session Cookie Security Testing

- `tests/test_security.py` tests CSRF, pre-auth origin checks, and rate limiting, but does **not** test the `SESSION_COOKIE_SECURE` flag behavior (i.e., cookies not being sent over HTTP when `secure=True`).
- No test verifies that session cookies are not accessible via `document.cookie` (testing `HttpOnly` flag effectiveness).
- No test for the `DEMO_MODE` credential exposure scenario (password printed to stdout).

### Contract Drift Testing

`tests/test_contract_drift.py` checks that specific TypeScript interface names and OpenAPI paths exist, but it does **not** validate schema parity. It verifies structure (names exist) but not content (types match). A field could change type in the backend without being caught.

### Data Mode Consistency Testing

No test verifies that `Signal.data_mode` and `Signal.is_synthetic` are consistent. No test checks that the `DataModeBadge` component's `'synthetic'` check aligns with the actual `DataMode` type definition. No test validates that the `PIIPHIScrubber.classify_payload` function correctly prevents confidential data from reaching the Grok privacy gate boundary.

---

## Dependencies at Risk

- **`llama-cpp-python`** (`gemma.py` line 97): Conditionally imported — if not installed, GGUF engine is unavailable. The `ImportError` catch raises `OllamaUnavailableError`, which falls through to Ollama, then to BART degraded mode. If both llama-cpp-python and Ollama are unavailable, the entire LLM capability is lost.
- **`httpx.AsyncClient` lifecycle:** The `_client` in `GemmaProvider` and `GrokProvider` is lazily created and never explicitly closed in the normal flow. The `aclose` method exists but is not called by `ProviderFactory`. This could lead to resource leaks in long-running processes.
- **`itsdangerous`** (`security.py`): Used for session token signing. This library is not actively maintained and has had CVEs in the past. The `TimestampSigner` with `max_age` is used for absolute session expiration, but the signing itself relies on `SECRET_KEY` entropy.
