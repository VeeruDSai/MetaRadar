---
phase: "03"
status: issues_found
findings_count: 15
reviewed: 2026-08-15T00:00:00Z
depth: standard
files_reviewed: 21
files_reviewed_list:
  - backend/app/services/embeddings.py
  - backend/app/services/vector_query.py
  - backend/app/services/embeddings_backfill.py
  - backend/app/workflows/nodes/embed.py
  - backend/app/workflows/graph.py
  - backend/app/workflows/state.py
  - backend/app/workflows/nodes/__init__.py
  - backend/app/providers/gemma.py
  - backend/app/providers/grok.py
  - backend/app/schemas/__init__.py
  - backend/app/api/v1/endpoints/search.py
  - backend/app/api/v1/endpoints/health.py
  - backend/app/main.py
  - backend/app/core/config.py
  - tests/test_retrieval.py
  - tests/test_providers_live.py
  - tests/test_provider_matrix.py
  - scripts/export_openapi.py
  - docker-compose.yml
  - backend/requirements.txt
  - pytest.ini
findings:
  critical: 1
  warning: 7
  info: 7
  total: 15
---

# Phase 3: Code Review Report

**Reviewed:** 2026-08-15
**Depth:** standard
**Files Reviewed:** 21
**Status:** issues_found

## Summary

Reviewed all 21 production/test files changed in Phase 3 (embedding service, node_embed, pgvector search, search/health endpoints, real Gemma/Grok providers, backfill CLI, docker-compose, contracts, tests), plus cross-referenced supporting modules (Signal model, db session, deduplication, ProviderFactory, privacy-boundary tests) to trace call chains and verify contracts.

The phase delivers solid work overall: the reducer fix for `validated_signals`, the hermetic MockTransport test pattern, and the honest `/health/models` telemetry are genuine quality wins. However, one **critical security defect** was introduced: `GrokProvider.generate_summary` was rewired from a simulated stub to a real network call to api.x.ai with **no privacy gate** — directly contradicting the phase's own gate contract ("enforced before ANY external transmission"). Additional warnings cover an infinite-loop risk in the backfill CLI, f-string SQL interpolation of `ef_search`, an uncaught-DB-error path in the search endpoint, an httpx client resource leak in `/health/models`, a state-wiping failure path in `node_embed` interacting with the new replacement reducer, a dead `SearchFilters.limit` field, and a GPU misconfiguration in docker-compose (the Ollama inference container has no GPU reservation while `backend-gpu` reserves one it never uses).

## Critical Issues

### CR-01: GrokProvider.generate_summary transmits data to api.x.ai with NO privacy gate

**File:** `backend/app/providers/grok.py:105-111`
**Issue:** This phase rewired `generate_summary` from a simulated local stub (`return f"[Grok Summary]: {text[:200]}..."` — no network) to a real HTTP POST to `https://api.x.ai/v1/chat/completions` via `_chat()`. The privacy gate (`validate_privacy_gate`) is enforced **only** in `generate_intelligence` (line 125). `generate_summary` accepts arbitrary `text` with no classification parameter and transmits it unconditionally. This violates:
- The module's own docstring (line 3): "Strict privacy gate ... is enforced before ANY external transmission: only PUBLIC / SYNTHETIC payloads may reach api.x.ai."
- PLAN Task A-8 requirement 1: "Privacy gate remains exactly as-is: validate_privacy_gate(classification) before any API call."
- The project's SECURITY_STANDARDS (zero PII/PHI leakage; Grok privacy gate is the core data-boundary control).

`_chat()` (line 72) is the single choke point for all outbound Grok traffic and is the correct place to enforce the gate. Today nothing in the codebase calls `grok.generate_summary`, but it is a public method on a class implementing `LLMProvider` (the same interface `DegradedProvider` uses internally for its `generate_intelligence`), so any future caller — including the Ask Athena / summarize path Phase 4 is about to build — would leak CONFIDENTIAL/PATIENT_IDENTIFIABLE payloads to a third party.

**Fix:** Enforce the gate inside `_chat()` (or add a classification parameter to `generate_summary` and gate before transmission). Minimal fix:

```python
async def _chat(self, messages: List[Dict[str, str]], classification: DataClassification = DataClassification.UNKNOWN) -> str:
    if not self.api_key:
        raise GrokUnavailableError("No XAI_API_KEY configured")
    if not self.validate_privacy_gate(classification):
        raise PermissionError(
            f"Privacy gate rejected external API transmission for classification '{classification}'"
        )
    ...

async def generate_summary(self, text: str) -> str:
    # Summaries of unclassified text are UNKNOWN by default -> gate blocks
    # unless callers explicitly pass PUBLIC/SYNTHETIC.
    messages = [...]
    return await self._chat(messages, classification=DataClassification.UNKNOWN)
```

Add a boundary test mirroring `test_privacy_gate_external_bypass_prevention` for `generate_summary` (assert `PermissionError` on CONFIDENTIAL text).

## Warnings

### WR-01: Backfill CLI can loop forever when embedding persistently fails

**File:** `backend/app/services/embeddings_backfill.py:46-88`
**Issue:** The `while True:` loop re-queries `SELECT ... WHERE embedding IS NULL LIMIT batch_size` until no NULL rows remain. Rows that raise `EmbeddingError` are skipped (line 63-65) but **never marked or removed** — they stay NULL and are re-selected on the next iteration. If embedding fails persistently for any row (e.g., a malformed row that always produces empty chunked text, or a transient model-load/network failure affecting the whole batch), the loop logs warnings forever with zero progress and no termination condition. There is no progress tracking, max-iteration guard, or consecutive-failure counter.

**Fix:** Track per-batch failure count and break when a batch makes no progress:

```python
if batch_backfilled == 0:
    logger.error(
        f"Backfill stalled: {len(rows)} signals remain NULL-embedding and "
        f"{len(rows) - batch_backfilled} failed; aborting to avoid infinite loop."
    )
    break
```

### WR-02: f-string interpolation of `ef_search` into SQL

**File:** `backend/app/services/vector_query.py:69`
**Issue:** `await db.execute(text(f"SET LOCAL hnsw.ef_search = {ef_search}"))` interpolates a caller-supplied value directly into a SQL string. The HTTP endpoint validates `ef_search` as `int` (ge=1, le=1000) so the current exposure is limited, but the service is a public API also intended for internal consumers (Ask Athena / node_synthesize, per the plan's "one contract, two consumers"), and nothing in `VectorQueryService.search` coerces or validates the parameter. Any future non-int caller becomes an SQL-injection vector. This is also a deviation from the parameterized-query pattern used everywhere else in the codebase.

**Fix:** Use `set_config` with a bound parameter (Postgres `SET` does not accept bind params):

```python
await db.execute(
    text("SELECT set_config('hnsw.ef_search', :ef_search, true)"),
    {"ef_search": str(ef_search)},
)
```

### WR-03: Search endpoint only catches SearchError — DB failures surface as 500

**File:** `backend/app/api/v1/endpoints/search.py:47-60`
**Issue:** Only `SearchError` is caught. Any database-level failure — pgvector extension not installed, HNSW GUC `hnsw.ef_search` unknown (pgvector < 0.5.0), missing `signals` table / `embedding` column, DB connection down — propagates out of `vector_query_service.search` as an uncaught `OperationalError`/`ProgrammingError` → HTTP 500 with a stack trace in server logs, and the client gets no meaningful diagnostic. The endpoint's contract promises 503 "Search service unavailable" for pipeline failures; DB failures should map to the same or a 4xx/5xx with a bounded message, never leak SQL internals via tracebacks.

**Fix:** Broaden the mapping:

```python
except SearchError as e:
    raise HTTPException(status_code=503, detail=f"Search service unavailable: {e}")
except Exception as e:
    logger.exception("Search endpoint: unexpected failure")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Search service unavailable: database error",
    )
```

### WR-04: `/health/models` leaks an httpx.AsyncClient on every call

**File:** `backend/app/api/v1/endpoints/health.py:67-69`
**Issue:** `get_health_models()` constructs a fresh `GemmaProvider()` per request; `is_available()` → `_ensure_client()` creates a new `httpx.AsyncClient` (connection pool) that is never `aclose()`d and goes out of scope when the provider is discarded. Every poll of `/api/v1/health/models` (monitors, Kubernetes probes, the Phase 4 dashboard polling this endpoint) leaks a client with its connection pool until GC — generating "Unclosed client" warnings and accumulating sockets/descriptors over time.

**Fix:** Close the client after the probe, or reuse a module-level client:

```python
provider = GemmaProvider()
try:
    gemma_available = await provider.is_available()
finally:
    if provider._client is not None:
        await provider._client.aclose()
```

Better: make `is_available()` close its client, or hoist a shared provider/client at module scope.

### WR-05: node_embed failure path wipes all validated signals (interacts with new replace_list reducer)

**File:** `backend/app/workflows/nodes/embed.py:91-94`
**Issue:** The outer `except` handler returns `"validated_signals": []`. With the phase's new `replace_list` reducer on that channel, an unexpected exception in `node_embed` **replaces the entire validated-signal list with an empty list** — silently destroying all validated data mid-pipeline. Downstream nodes (nlp_extract, ontology, confluence, synthesize...) then run against zero signals and the run "completes" with FAILED status but no data. This contradicts the node's own documented contract ("Signals that fail embedding are kept ... never silently dropped") and turns a transient unexpected error into total batch data loss. (Per-signal `EmbeddingError` is handled correctly; this path is for any other exception — which is precisely when a node should preserve state.) Note `node_validate` (validate.py:115) has the same `[]`-on-error pattern, but it runs first against an empty channel, so it was harmless under `operator.add` and stays harmless — the destructive interaction is new to `node_embed` under replacement semantics.

**Fix:** Omit the `validated_signals` key from the exception return so LangGraph leaves the channel unchanged:

```python
return {
    "errors": errors,
    "node_statuses": {NODE_NAME: "FAILED"},
}
```

### WR-06: `SearchFilters.limit` is dead — never honored; API exposes two competing limit knobs

**File:** `backend/app/services/vector_query.py:34` (field) and `backend/app/services/vector_query.py:52-79` (search)
**Issue:** `SearchFilters` declares `limit: int = Field(default=10, ge=1, le=100)`, and `SearchRequest` also exposes `top_k`. `VectorQueryService.search` applies only `top_k` to the `LIMIT` clause and never reads `filters.limit`. A client setting `filters={"limit": 5}` gets `top_k` (default 10) results — silently wrong. The dead field also leaks into the canonical TS contract (`SearchFilters.limit` in frontend/types/api.ts). This is a confusing, contradicting API surface.

**Fix:** Either remove `limit` from `SearchFilters`, or make `search()` prefer `filters.limit` when `top_k` is not explicitly provided. Removing is cleaner since `top_k` already covers the plan's Top-K design:

```python
class SearchFilters(BaseModel):
    signal_type: Optional[str] = None
    disease: Optional[str] = None
    priority: Optional[str] = None
```

### WR-07: docker-compose GPU misconfiguration — inference runs on CPU while a GPU is reserved elsewhere

**File:** `docker-compose.yml:82-88, 118-131`
**Issue:** The `ollama` sidecar — the container that actually performs Gemma 3 4B inference — has **no** `deploy.resources.reservations.devices` entry, so it runs on CPU. Meanwhile `backend-gpu` reserves an NVIDIA GPU (`count: 1, capabilities: [gpu]`) that no component of the backend container uses for LLM work (inference is delegated to Ollama over HTTP at `OLLAMA_HOST=http://ollama:11434`). The plan narrative ("Gemma 3 4B ... fits RTX 3050 4 GB", D-09) promises GPU inference, but the delivered config silently runs 4B inference on CPU (extremely slow) with the GPU idle. On GPU hosts this is a functional mismatch; on CPU-only hosts `backend-gpu` will fail to start while `ollama` works.

**Fix:** Move the GPU reservation to the `ollama` service:

```yaml
  ollama:
    image: ollama/ollama:latest
    ...
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

and either drop the reservation from `backend-gpu` or keep it only if the backend image genuinely needs CUDA (it does not today).

## Info

### IN-01: Stale "10-node" docstring in state.py

**File:** `backend/app/workflows/state.py:27-31`
**Issue:** `MetaRadarState` docstring still says "Canonical 10-node LangGraph IntelligenceState contract" — the graph is now 11 nodes (node_embed added).
**Fix:** Update to "11-node".

### IN-02: Dead code / unused imports

**File:** `backend/app/services/embeddings.py:31`; `backend/app/services/vector_query.py:17`; `backend/app/services/embeddings_backfill.py:15`
**Issue:** (a) Module-level `_model: Optional[TextEmbedding] = None` in embeddings.py is never read or written — the instance attribute `self._model` is the live cache. (b) `settings` imported in vector_query.py is unused. (c) `List` imported in embeddings_backfill.py is unused.
**Fix:** Remove the dead module-level `_model` and the unused imports.

### IN-03: Incorrect comment on cosine_distance range

**File:** `backend/app/services/vector_query.py:96`
**Issue:** Comment claims "cosine_distance is in [-2, 2] for normalized vectors". For normalized vectors, cosine similarity ∈ [-1, 1], so cosine distance ∈ [0, 2]. The clamping logic (`max(0.0, min(1.0, 1.0 - dist))`) is mathematically correct regardless; only the comment is wrong.
**Fix:** Correct the comment to "[0, 2] for normalized vectors" (or note unnormalized fastembed output can produce negative similarity → clamp).

### IN-04: `is_available()` exact-tag match may report false negative

**File:** `backend/app/providers/gemma.py:154-156`
**Issue:** `settings.OLLAMA_MODEL in model_names` requires an exact name match. If the model is pulled/registered as `gemma3:4b:latest` (or any aliased tag), `/api/tags` returns that name and `gemma_available` reports `false` even though the model is present — the phase's "honest telemetry" requirement cuts the other way here.
**Fix:** Match on tag prefix: `any(m.split(":")[0] == settings.OLLAMA_MODEL.split(":")[0] or m == settings.OLLAMA_MODEL for m in model_names)`.

### IN-05: GrokProvider default api_key bound at import time

**File:** `backend/app/providers/grok.py:43`
**Issue:** `def __init__(self, api_key: str = settings.XAI_API_KEY or "")` evaluates the default once at module import. Runtime changes to `settings.XAI_API_KEY` (e.g., test monkeypatching or env reload) are not reflected in a default-constructed `GrokProvider()`.
**Fix:** Resolve inside `__init__`: `def __init__(self, api_key: Optional[str] = None): self.api_key = api_key or settings.XAI_API_KEY or ""`.

### IN-06: Deprecated `.isnot()` in SQLAlchemy 2.0

**File:** `backend/app/services/vector_query.py:77`
**Issue:** `Signal.embedding.isnot(None)` uses the pre-2.0 name; SQLAlchemy 2.0 renamed it to `.is_not()` and deprecates `isnot` (requirement is `sqlalchemy>=2.0.28`), producing deprecation warnings.
**Fix:** Use `Signal.embedding.is_not(None)`.

### IN-07: Lazy model load not thread-safe on first concurrent call

**File:** `backend/app/services/embeddings.py:50-59`
**Issue:** `_get_model()`'s check-then-load is unsynchronized; two concurrent requests (both offloaded via `run_in_executor`) can both observe `self._model is None` and each construct a `TextEmbedding` — double model load/download on first request and one orphaned instance. Self-heals afterward; cost is only startup-time.
**Fix:** Guard with a module-level `asyncio.Lock` around the lazy init, or initialize the model in the FastAPI lifespan/startup event before serving traffic.

---

_Reviewed: 2026-08-15_
_Reviewer: gsd-code-reviewer (adversarial)_
_Depth: standard_