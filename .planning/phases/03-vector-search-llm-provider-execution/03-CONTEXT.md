# Phase 3: Vector Search & LLM Provider Execution - Context

**Gathered:** 2026-08-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace simulated/scaffolded provider behavior with real execution. Deliver:
1. **REQ-P3-1** — Real 384-dimensional embeddings (`sentence-transformers/all-MiniLM-L6-v2`) for signals.
2. **REQ-P3-2** — pgvector HNSW cosine similarity search (`signals.embedding`) for candidate matching.
3. **REQ-P3-3** — Real local Gemma 3 4B inference (Q4, RTX 3050) for text reasoning.
4. **REQ-P3-4** — xAI Grok API integration validated with strict `validate_privacy_gate` enforcement.

Deliver an embedding service, a hybrid vector-search service + `/search` endpoint, real provider execution wired through `ProviderFactory`, and retrieval tests.

**Scope guardrail (user-locked):** Phase 3 is locked to the single flow `Ingestion → Embedding → Hybrid Retrieval → Local LLM → Optional Grok Validation → Structured Signal`. Explicitly deferred (no scope creep): fine-tuning, complex agent loops, multimodal pipelines, elaborate reranking models, distributed vector infrastructure, and autonomous agent features.

**Correction (user-locked):** Terminology must not conflate storage and index: pgvector/PostgreSQL is the storage layer; HNSW is the index/search method. Never describe the stack as "HNSW the vector database."

</domain>

<decisions>
## Implementation Decisions

### Area 1: Embedding Pipeline — Timing & Text Source
- **D-01:** Embeddings are generated **at ingestion time** (synchronously), NOT lazily/on-demand. This keeps search deterministic and makes the demo easy to reason about.
- **D-02:** Embedded text source = **`signal title + normalized summary + entities + signal category`**. Phase 3 consumes the stored 256-token chunks from Phase 1 (D-18: `chunk_text_for_embedding` at ingestion) — do NOT invent a new chunking strategy. `node_synthesize` already produces an evidence chunk via `chunk_text_for_embedding(f"{title}\n\n{content}")` (`backend/app/workflows/nodes/synthesize.py`).
- **D-03:** Embedding runtime is **fastembed (ONNX, CPU)** — a lightweight `~small` footprint, no full torch stack, keeps the 4 GB VRAM free for Gemma in Ollama. Deterministic and fast on CPU for MiniLM-L6-v2. Model identity remains `all-MiniLM-L6-v2` per REQ-P3-1 and existing `Settings.EMBEDDING_MODEL`; only the runtime engine changes.
- **D-04:** Embedding generation hooks into the pipeline as **a dedicated LangGraph step after `node_validate`** (before `node_nlp_extract`/`node_confluence`), so every promoted signal is embedded as part of the run.
- **D-05:** **Backfill** for existing signals with `NULL` embedding is a **CLI command** (e.g. `python -m app.services.embeddings.backfill`) that embeds existing rows in bounded batches. Embedded rows record `embedding_model_version` (`Settings.EMBEDDING_MODEL_REVISION`) for auditability.

### Area 2: Vector Search — Interface & Integration
- **D-06:** Search is **hybrid retrieval = metadata/keyword filtering + pgvector cosine similarity** — NOT pure vector search. Flow: user query → metadata filters → keyword candidates + vector candidates → merge/rank → Top-K signals → LLM synthesis. pgvector's own documented pattern (combine vector + PostgreSQL full-text/trigram) is the model.
- **D-07:** Phase 3 **exposes a REST endpoint** (e.g. `POST /api/v1/search` — filters + query → top-K signals with similarity scores). Phase 4 frontend consumes it directly; Ask Athena / `node_synthesize` call the same service internally. One contract, two consumers.
- **D-08:** Retrieval defaults (user-locked, don't over-tune): **Top-K = 10**, cosine similarity, HNSW index `signals_embedding_hnsw` with `m=16` / `ef_construction=64` (already in migration `001`), **adjustable `ef_search`** as a config/query parameter.

### Area 3: Gemma 3 4B — Runtime & VRAM Strategy
- **D-09:** Gemma 3 4B inference runtime is **Ollama sidecar** (`LLM_PROVIDER=ollama` path). App calls `OLLAMA_HOST` (default `http://localhost:11434`) via HTTP like the Grok path.
- **D-10:** **Deployment:** add an `ollama` service to `docker-compose.yml` with a persistent volume for model weights; app connects via `OLLAMA_HOST`. On startup, idempotently `ollama pull` the Gemma model if missing. `/health/models` reports real Ollama status + loaded model — no fabricated telemetry.
- **D-11:** Gemma's role is **local baseline extraction / classification / summarization** — NOT the "everything engine". Grok (when available & permitted) handles harder validation/enrichment. Architecture story: retrieved signals → Gemma local baseline (classify/summary/entities) → Grok validation+enrichment → structured JSON → Radar UI.
- **D-12:** Gemma 3 4B stays **Q4/int4** on the RTX 3050 (4 GB VRAM). Budget weights, KV cache, context (`MAX_CONTEXT_TOKENS=2048`), and output (`MAX_OUTPUT_TOKENS=512`) separately. **Never crash:** any model init/inference failure (incl. "does not fit in 4 GB VRAM") falls through the existing provider chain (Gemma → Grok → BART degraded → source-only display). No GPU logic hard-coded into LangGraph nodes.

### Area 4: Grok — Live Validation Scope & Privacy Gate
- **D-13:** The Grok privacy gate is an **explicit, unambiguous rule**: `IF approved public/mock/synthetic data → Grok API allowed; ELSE → Grok blocked → local model fallback`. Never send confidential or proprietary Novo Nordisk data to external LLM providers.
- **D-14:** The public claim for the prototype is: **"The prototype processes only public, mock, or synthetic information. No confidential or proprietary Novo Nordisk data is transmitted to external LLM providers."** (Reinforces the xAI 30-day default retention concern — Zero Data Retention is a separate config.)
- **D-15:** Live Grok is **NOT mandatory** — the system works in three modes: **Demo** (Embedding=Local, LLM=Gemma, External API=Optional), **Standard** (Embedding=Local, LLM=Gemma→Grok, External API=Allowed), **Restricted** (Embedding=Local, LLM=Gemma, External API=Blocked). The radar must remain functional when external AI services are unavailable or restricted — this is a core demo/privacy story.
- **D-16:** **Testing:** Grok code paths are tested in CI with a **mocked client** (deterministic, hermetic, no key). A separate **opt-in live integration test** (marker `@pytest.mark.live` + `LIVE_XAI_KEY` env var) exercises the real API only when a key is present. CI stays green without a key.

### Follow-on: BART Degraded Path
- **D-17:** With Gemma moving to Ollama, the **BART degraded mode stays as-is** (`DegradedProvider` via transformers, `facebook/bart-large-cnn`). It is CPU-friendly, already verified in the provider matrix (Cases A-F), and only fires when both Gemma and Grok fail. No reason to disturb a working, verified path.

### Developer's Discretion
- Exact file layout within `backend/app/services/` for the embedding service, vector query service, and backfill CLI (names/structure at agent discretion, consistent with existing service patterns).
- `ef_search` tuning default value (configurable; pick a sensible HNSW default like 40).
- Exact query parameter names for the `/api/v1/search` endpoint.
- Test-scaffolding details for retrieval tests (framework = pytest; strategy at agent's discretion).

</decisions>

<canonical_refs>
## Canonical References

**Downstream planning and execution agents MUST consult these authorities:**

### Master specification & engineering rules
- `docs/METARADAR_MASTER_PLAN_v5.0.md` §13 (Provider-Agnostic Reasoning Layer: §13.1 modes, §13.2 provider interface, §13.4 Grok structured output, §13.5 external LLM privacy gate, §13.6 failure/fallback, §13.7 model metadata, §13.8 canonical model table) & §14.1 (Local Model Execution — Gemma on RTX 3050, Q4/int4, never-crash flow)
- `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` §2.4 (Provider Abstraction)
- `docs/rules/DATA_AND_PRIVACY_STANDARDS.md` (payload classification & privacy boundary)
- `docs/rules/SECURITY_STANDARDS.md` (zero secret leaks, PII/PHI scrubbing, privacy gate)
- `docs/rules/ENGINEERING_STANDARDS.md` (quality/type-safety/honest telemetry)
- `docs/rules/DEFINITION_OF_DONE.md` (DoD verification matrix)
- `docs/rules/TESTING_STRATEGY.md` (mandatory test gates)
- `docs/rules/ARCHITECTURE_RULES.md` (approved stack, canonical entity model)
- `docs/rules/OBSERVABILITY_STANDARDS.md` (honest health/readiness modeling)
- `docs/10_ARCHITECTURE_HARDENING_REPORT.md` (hardening decisions shaping the baseline)

### Domain & configuration
- `config/haemophilia.yaml` (assets, synonyms, signal types, baseline routing)
- `backend/app/core/config.py` (`EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `EMBEDDING_MAX_SEQ_LENGTH`, `EMBEDDING_MODEL_REVISION`, `LLM_PROVIDER`, `LOCAL_LLM_MODEL`, `LLM_DEVICE`, `LLM_DTYPE`, `MAX_CONTEXT_TOKENS`, `MAX_OUTPUT_TOKENS`, `ENABLE_GROK_FALLBACK`, `XAI_API_KEY`, `OLLAMA_HOST` — add if absent)

### Existing code implementing the contracts
- `backend/app/providers/base.py` — `LLMProvider`, `ProviderCapability`, `DataClassification`
- `backend/app/providers/factory.py` — `ProviderFactory` fallback chain (Gemma → Grok → BART)
- `backend/app/providers/gemma.py` — currently **simulated**; Phase 3 wires real Ollama-backed inference
- `backend/app/providers/grok.py` — `validate_privacy_gate` (PUBLIC/SYNTHETIC only); Phase 3 wires real client + validation
- `backend/app/providers/degraded.py` — BART degraded factual mode (kept as-is, D-17)
- `backend/app/models/__init__.py` — `Signal.embedding` (`Vector(384)`), `embedding_model_version`
- `backend/alembic/versions/001_initial_v51_schema.py` — `signals_embedding_hnsw` HNSW index (`m=16, ef_construction=64`, cosine ops)
- `backend/app/services/deduplication.py` — `chunk_text_for_embedding` (256-token Phase 1 chunks)
- `backend/app/workflows/nodes/synthesize.py` — evidence chunking; Phase 3's retrieval consumer (Athena)
- `backend/app/api/v1/endpoints/signals.py` — `/signals`, `/overview`, `/athena` (currently synthetic fallback)
- `backend/app/api/v1/endpoints/health.py` — `/health/models`, `/health/ready` (report real model status)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ProviderFactory` (`providers/factory.py`): fallback chain already wired — Gemma → Grok (gated) → BART degraded. Phase 3 replaces simulated provider internals, not the chain.
- `validate_privacy_gate` (`providers/grok.py`): strict PUBLIC/SYNTHETIC-only gate already tested (Cases A-F) — reuse for Grok live wiring (D-13).
- `Signal.embedding` + `signals_embedding_hnsw` HNSW index: schema and index already in migration `001` (REQ-P3-2 foundation).
- `Settings.EMBEDDING_MODEL` / `_REVISION` / `_DIMENSION` / `MAX_SEQ_LENGTH`: embedding model identity already configured.
- `chunk_text_for_embedding` (`services/deduplication.py`): Phase 1 stored chunks — Phase 3 embedding text source (D-02).
- `pytest` suite patterns in `tests/` (config, endpoints, provider matrix, privacy gate, contract drift) — model new retrieval tests on these.

### Established Patterns
- Async everything: `async def` + async SQLAlchemy (`db/session.py`), `httpx` async client, `redis.asyncio`.
- Pydantic v2 schemas + `pydantic-settings` env config with `extra="ignore"` (add `OLLAMA_HOST` here).
- Honest health modeling: `/health/models`, `/health/ready` report real status — no fabricated telemetry (D-10).
- LangGraph node pattern: isolated error boundaries, `SUCCESS/DEGRADED/FAILED` statuses, `state['errors']` accumulation (embedding step follows this, D-04).
- Alembic async migrations if any schema change is needed.

### Integration Points
- New embedding service + vector query service in `backend/app/services/` (fastembed-based).
- New `/api/v1/search` endpoint (hybrid retrieval, Top-K 10, adjustable `ef_search`).
- `GemmaProvider` rewired to call Ollama HTTP API; `OLLAMA_HOST` in config.
- `GrokProvider` real client + JSON-schema structured outputs + mocked-CI/opt-in-live tests.
- `docker-compose.yml` gains an `ollama` service (persistent volume, auto-pull).
- `/health/models` reports Ollama + embedding model real status.
- Pipeline embedding step after `node_validate`; CLI backfill for NULL-embedding rows.

</code_context>

<specifics>
## Specific Ideas

- **"HNSW is not the database"** — user explicitly corrected the terminology: pgvector/PostgreSQL is the storage layer; HNSW is the index/search method. CONTEXT.md and downstream docs must respect this distinction.
- **Three-mode operation (Demo / Standard / Restricted)** — the radar stays functional when external AI is unavailable/restricted; this is both a demo story and the privacy/security story. Live Grok is optional, never mandatory.
- **Gemma = local baseline; Grok = validation/enrichment** — user repositioned Gemma from "the everything engine" to baseline extraction/classification/summarization, with the stronger provider handling harder synthesis when available.
- **One-month constraint** — user emphasized not over-engineering; locked flow and explicit deferrals reflect this.
- All seven discussed gray areas were settled via the recommended options (see D-01 through D-17).

</specifics>

<deferred>
## Deferred Ideas

- **Fine-tuning** of local models — explicitly deferred, own effort/phase.
- **Complex agent loops / autonomous agents** — explicitly out of Phase 3 scope.
- **Multimodal pipelines** — explicitly deferred.
- **Elaborate reranking models** — hybrid top-K is sufficient for the demo.
- **Distributed vector infrastructure** (sharded vector stores, external vector DBs) — pgvector in PostgreSQL 16 is the locked store.
- **Scheduler/polling autonomy** — embedding/search run on-demand and in the pipeline; autonomous scheduling belongs to a later phase.

</deferred>

---

*Phase: 3-Vector Search & LLM Provider Execution*
*Context gathered: 2026-08-15*