---
phase: 03-vector-search-llm-provider-execution
plan: "03"
subsystem: search-retrieval, llm-providers
tags: [fastembed, pgvector, hnsw, ollama, gemma, grok, langgraph, httpx, docker-compose]

# Dependency graph
requires:
  - phase: 02-langgraph-10-node-intelligence-engine
    provides: MetaRadarState contract, LangGraph node pattern (SUCCESS/DEGRADED/FAILED), 51-test suite, PipelineRunner
  - phase: 01-ingestion-connectors-data-pipeline-status-planned
    provides: Signal model with Vector(384) embedding column, signals_embedding_hnsw HNSW migration, chunk_text_for_embedding

provides:
  - fastembed EmbeddingService (384-dim, all-MiniLM-L6-v2, lazy singleton)
  - node_embed LangGraph pipeline step (11-node pipeline)
  - pgvector hybrid VectorQueryService + POST /api/v1/search endpoint
  - real Ollama-backed GemmaProvider with never-crash fallback contract
  - real xAI GrokProvider client with strict privacy gate
  - honest /health/models reporting + CLI backfill for NULL-embedding signals
  - Ollama sidecar in docker-compose; 61-test hermetic suite (10 new retrieval tests)
affects: [phase-04-frontend-api-integration, verify-work-uat, secure-phase]

actuals:
  tokens: 20805    # chars/4 over realized diff (1353 insertions, 34 deletions)
  tasks: 13
  commits: 13

tech-stack:
  added: [fastembed>=0.4.0, ollama/ollama sidecar (docker-compose), httpx MockTransport test pattern]
  patterns:
    - Lazy singleton service with run_in_executor CPU offload (EmbeddingService)
    - Replacement reducer for list channels re-emitted whole by LangGraph nodes
    - MockTransport-based hermetic provider tests (no network in CI)
    - Never-crash provider contract: exceptions map to provider-specific unavailable errors for factory fallback

key-files:
  created:
    - backend/app/services/embeddings.py
    - backend/app/workflows/nodes/embed.py
    - backend/app/services/vector_query.py
    - backend/app/api/v1/endpoints/search.py
    - backend/app/services/embeddings_backfill.py
    - tests/test_retrieval.py
    - tests/test_providers_live.py
  modified:
    - backend/requirements.txt
    - backend/app/core/config.py
    - backend/app/workflows/graph.py
    - backend/app/workflows/state.py
    - backend/app/workflows/nodes/__init__.py
    - backend/app/providers/gemma.py
    - backend/app/providers/grok.py
    - backend/app/schemas/__init__.py
    - backend/app/api/v1/endpoints/health.py
    - backend/app/main.py
    - scripts/export_openapi.py
    - contracts/openapi.json
    - frontend/types/api.ts
    - frontend/src/types/api.ts
    - docker-compose.yml
    - tests/test_provider_matrix.py
    - pytest.ini (moved from tests/)

key-decisions:
  - "D-01..D-17 honored from 03-CONTEXT.md: fastembed CPU runtime, ingestion-time embeddings via node_embed after node_validate, hybrid retrieval (metadata filters + pgvector cosine), Top-K 10, ef_search=40, Ollama sidecar for Gemma, real Grok client with privacy gate, CLI backfill"
  - "validated_signals channel uses replacement reducer — node_embed re-emits the whole list; operator.add would duplicate every signal in graph runs"
  - "Empty Grok api_key raises GrokUnavailableError BEFORE the privacy gate so a missing key reads as provider unavailability (D-16 CI path), while gate logic stays byte-identical"
  - "Search router registered in main.py (the repo's actual registration point) — the plan's router.py does not exist"
  - "pytest.ini consolidated at repo root so CI/local 'pytest -v' actually loads asyncio_mode=auto + live marker"
  - "export_openapi.py TS template extended with search contract types + ollama_host so the canonical TypeScript contract reflects the new schema"

patterns-established:
  - "Lazy singleton services (embedding_service, vector_query_service) with run_in_executor offload"
  - "LangGraph nodes returning whole list channels require replacement reducers"
  - "Hermetic provider tests via httpx.MockTransport; opt-in live tests behind @pytest.mark.live"
  - "Never-crash provider chain: OllamaUnavailableError/GrokUnavailableError -> ProviderFactory fallback"

requirements-completed: []

coverage:
  - id: D1
    description: "fastembed EmbeddingService producing 384-dim vectors (REQ-P3-1, D-02/D-03)"
    requirement: REQ-P3-1
    verification:
      - kind: unit
        ref: "tests/test_retrieval.py#test_embed_text_returns_384_dims"
        status: pass
      - kind: unit
        ref: "tests/test_retrieval.py#test_embed_signal_composites_text"
        status: pass
      - kind: other
        ref: "py -3.13 -c 'from app.services.embeddings import embedding_service; ...' -> 384"
        status: pass
    human_judgment: false
  - id: D2
    description: "node_embed pipeline step embedded after node_validate (D-04); signal duplication prevented via replacement reducer"
    verification:
      - kind: unit
        ref: "tests/test_retrieval.py#test_node_embed_attaches_embedding_to_signal"
        status: pass
      - kind: unit
        ref: "tests/test_retrieval.py#test_node_embed_degraded_on_partial_failure"
        status: pass
      - kind: other
        ref: "end-to-end PipelineRunner run: 2 signals validated, 2 embedded, all 11 nodes SUCCESS, 0 errors"
        status: pass
    human_judgment: false
  - id: D3
    description: "Hybrid vector search: VectorQueryService + POST /api/v1/search (D-06/D-07/D-08, REQ-P3-2)"
    requirement: REQ-P3-2
    verification:
      - kind: unit
        ref: "tests/test_retrieval.py#test_search_filters_pydantic"
        status: pass
      - kind: other
        ref: "py -3.13 -c 'from app.api.v1.endpoints.search import router' + openapi path /api/v1/search"
        status: pass
    human_judgment: true
    rationale: "The SQL query path (SET LOCAL hnsw.ef_search + cosine_distance ranking) executes only against a live PostgreSQL/pgvector database, which CI does not provision; live-DB verification is deferred to Phase 3 VERIFICATION.md UAT."
  - id: D4
    description: "Real Gemma 3 4B via Ollama HTTP client with never-crash contract (D-09/D-12, REQ-P3-3)"
    requirement: REQ-P3-3
    verification:
      - kind: unit
        ref: "tests/test_provider_matrix.py#test_case_a_gemma_available"
        status: pass
      - kind: unit
        ref: "tests/test_retrieval.py#test_gemma_raises_on_connection_refused"
        status: pass
      - kind: unit
        ref: "tests/test_retrieval.py#test_gemma_is_available_false_on_error"
        status: pass
    human_judgment: true
    rationale: "Live Gemma inference requires the physical RTX 3050 GPU + Ollama sidecar; verified in VERIFICATION.md UAT via /api/v1/health/models reporting gemma_available: true."
  - id: D5
    description: "Real xAI Grok API client with strict privacy gate (D-13/D-14/D-16, REQ-P3-4)"
    requirement: REQ-P3-4
    verification:
      - kind: unit
        ref: "tests/test_provider_matrix.py#test_case_c_gemma_unavailable_grok_enabled"
        status: pass
      - kind: unit
        ref: "tests/test_privacy_boundary.py#test_privacy_gate_external_bypass_prevention"
        status: pass
      - kind: unit
        ref: "tests/test_retrieval.py#test_grok_blocks_without_api_key"
        status: pass
    human_judgment: true
    rationale: "A real Grok API call is opt-in only (@pytest.mark.live + LIVE_XAI_KEY, D-16); runs locally when a key is provided."
  - id: D6
    description: "Honest /health/models reporting + CLI backfill + Ollama docker-compose service (D-05/D-10)"
    verification:
      - kind: unit
        ref: "tests/test_api_endpoints.py#test_health_endpoints"
        status: pass
      - kind: other
        ref: "live HTTP check: /api/v1/health/models -> gemma_available:false (honest), ollama_host present"
        status: pass
      - kind: other
        ref: "py -3.13 -c 'from app.services.embeddings_backfill import async_main' + docker compose config --quiet"
        status: pass
    human_judgment: false

# Metrics
duration: 95min
completed: 2026-08-15
status: complete
---

# Phase 3 Plan 03: Tracer — Embedding Service -> Vector Search -> Provider Wiring Summary

**Real execution wired through the whole retrieval chain: fastembed 384-dim embeddings embedded in the LangGraph pipeline, pgvector hybrid search exposed at POST /api/v1/search, Gemma 3 4B served via an Ollama sidecar, and a real xAI Grok client behind the strict privacy gate — all with honest telemetry and a hermetic 61-test suite.**

## Performance

- **Duration:** ~95 min
- **Started:** 2026-08-14T20:55:20Z
- **Completed:** 2026-08-15T02:45:00Z
- **Tasks:** 13
- **Files modified:** 27 (12 created, 15 modified)

## Accomplishments

- EmbeddingService (fastembed ONNX CPU, all-MiniLM-L6-v2, 384-dim, lazy singleton, `run_in_executor` offload) — verified returning `384`.
- `node_embed` inserted between `node_validate` and `node_nlp_extract`; the LangGraph pipeline is now 11 nodes and runs end-to-end (2 signals -> 2 embeddings, all SUCCESS, 0 errors, no duplication).
- VectorQueryService: metadata filters + pgvector cosine similarity + `SET LOCAL hnsw.ef_search` (default 40), Top-K 10, HNSW index `signals_embedding_hnsw`.
- `POST /api/v1/search` registered at exactly `/api/v1/search`; `SearchError` maps to HTTP 503.
- GemmaProvider rewired to real Ollama HTTP (`/api/generate`, model `gemma3:4b`); any failure raises `OllamaUnavailableError` so ProviderFactory falls through to Grok -> BART (never-crash, D-12). `is_available()` probes `/api/tags` and never raises.
- GrokProvider rewired to real `api.x.ai/v1/chat/completions` (grok-beta, json_object response format); `validate_privacy_gate` preserved byte-identical; empty key raises `GrokUnavailableError` (D-16 CI path).
- `/health/models` reports real Ollama status (no fabricated `gemma_available=True`) and exposes `ollama_host`.
- CLI backfill `python -m app.services.embeddings_backfill [--batch-size 50] [--dry-run]` for NULL-embedding signals (D-05).
- Ollama sidecar added to docker-compose (persistent volume, healthcheck, `OLLAMA_HOST=http://ollama:11434` wiring for backend/backend-gpu).
- 10 hermetic retrieval tests + opt-in live Grok test; full suite: **61 passed, 1 skipped (live), 0 failures**. OpenAPI contract sync: **0 drift**. docker compose: **validated**.

## Task Commits

Each task was committed atomically:

1. **A-1: fastembed + Ollama settings** - `ae657db` (chore)
2. **A-2: EmbeddingService** - `dca78e5` (feat)
3. **A-3: node_embed** - `f7d9ebe` (feat)
4. **A-4: wire node_embed into 11-node graph** - `392c365` (feat)
5. **A-5: VectorQueryService** - `fbdd63f` (feat)
6. **A-6: POST /api/v1/search** - `245d3d1` (feat)
7. **A-7: real Gemma via Ollama** - `6ba8b4a` (feat)
8. **A-8: real Grok client** - `d769991` (feat)
9. **A-9: /health/models real status + contract sync** - `a82c49f` (feat)
10. **A-10: retrieval + live provider tests** - `639b39d` (test)
11. **A-11: CLI backfill** - `6ee1cdb` (feat)
12. **A-12: Ollama docker-compose service** - `388bb09` (chore)
13. **A-13: full verification + pytest config consolidation** - `7278508` (test)

## Files Created/Modified

- `backend/app/services/embeddings.py` - EmbeddingService (fastembed, 384-dim, lazy singleton, async executor offload)
- `backend/app/workflows/nodes/embed.py` - node_embed (D-04): embeds validated signals, SUCCESS/DEGRADED/FAILED
- `backend/app/services/vector_query.py` - VectorQueryService + SearchFilters/SignalSearchResult (hybrid pgvector retrieval)
- `backend/app/api/v1/endpoints/search.py` - POST /api/v1/search endpoint (503 on SearchError)
- `backend/app/services/embeddings_backfill.py` - CLI backfill (bounded batches, dry-run, audit revision)
- `backend/app/providers/gemma.py` - real Ollama HTTP client + OllamaUnavailableError + is_available()
- `backend/app/providers/grok.py` - real xAI client + GrokUnavailableError (privacy gate unchanged)
- `backend/app/workflows/graph.py` / `nodes/__init__.py` / `state.py` - 11-node pipeline, node_embed export, replacement reducer
- `backend/app/api/v1/endpoints/health.py` + `schemas/__init__.py` - real gemma_available + ollama_host
- `backend/app/main.py` - search router registration
- `scripts/export_openapi.py` + `contracts/openapi.json` + `frontend/types/api.ts` - search contract types + ollama_host synced
- `docker-compose.yml` - ollama service + backend wiring
- `tests/test_retrieval.py` - 10 hermetic tests; `tests/test_providers_live.py` - opt-in live Grok
- `tests/test_provider_matrix.py` - mocked cases A/C for real providers
- `pytest.ini` - consolidated at repo root (marker + asyncio auto mode)

## Decisions Made

- Followed D-01..D-17 from 03-CONTEXT.md (fastembed CPU, ingestion-time embedding after validate, hybrid retrieval, ef_search=40, Ollama sidecar, real Grok, CLI backfill, BART unchanged).
- `validated_signals` reducer switched from `operator.add` to replacement semantics (see deviations).
- Grok empty-key check precedes the privacy gate so missing-key reads as provider unavailability while gate logic stays byte-identical.
- Search router registered in `main.py` (no router.py exists in this repo).
- pytest config consolidated at repo root (tests/pytest.ini was invisible to root-level `pytest -v`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] validated_signals channel duplicates every signal in graph runs**
- **Found during:** Task A-4 (wiring node_embed into the graph)
- **Issue:** `node_embed` returns the whole `validated_signals` list, but the state channel used `operator.add` — the enriched list would be APPENDED to the already-validated list, doubling every signal and corrupting downstream scoring/synthesis.
- **Fix:** Changed the channel to a replacement reducer (`replace_list`) in `state.py`; verified end-to-end via PipelineRunner (2 signals in, 2 embedded, 0 duplicates).
- **Files modified:** backend/app/workflows/state.py
- **Verification:** Full 11-node pipeline run: validated count == 2, embedded count == 2, all SUCCESS.
- **Committed in:** 392c365 (Task A-4)

**2. [Rule 3 - Blocking] Plan references non-existent backend/app/api/v1/router.py**
- **Found during:** Task A-6 (search endpoint registration)
- **Issue:** The plan's "router.py [MODIFY]" file does not exist — this repo registers routers directly in `main.py`.
- **Fix:** Registered `search.router` in `main.py` with prefix `/api/v1/search` (same pattern as health/signals/pipeline).
- **Files modified:** backend/app/main.py
- **Verification:** OpenAPI shows `/api/v1/search` path; router imports OK.
- **Committed in:** 245d3d1 (Task A-6)

**3. [Rule 3 - Blocking] Existing provider-matrix tests hit real external services after rewiring**
- **Found during:** Tasks A-7/A-8 (real Gemma/Grok clients)
- **Issue:** `test_case_a_gemma_available` would connect to localhost:11434 and `test_case_c_gemma_unavailable_grok_enabled` would call api.x.ai with a mock key — both fail without live services.
- **Fix:** Updated both tests to inject `httpx.AsyncClient(transport=httpx.MockTransport(...))` — hermetic, no network. Providers use lazy clients so tests can inject mocks without constructing a real client.
- **Files modified:** tests/test_provider_matrix.py, backend/app/providers/gemma.py, backend/app/providers/grok.py
- **Verification:** All 9 provider/privacy tests pass in 0.21s.
- **Committed in:** 6ba8b4a, d769991 (Tasks A-7, A-8)

**4. [Rule 3 - Plan-Spec Conflict] Empty-key Grok path raised PermissionError instead of GrokUnavailableError**
- **Found during:** Task A-10 (test #10 spec: `GrokProvider(api_key="").generate_intelligence` must raise GrokUnavailableError)
- **Issue:** The privacy gate returns False on a missing key, so generate_intelligence raised PermissionError — contradicting the plan's D-16 test contract.
- **Fix:** Moved the empty-key check BEFORE `validate_privacy_gate` in generate_intelligence. Gate logic itself unchanged (privacy-boundary tests still pass).
- **Files modified:** backend/app/providers/grok.py
- **Verification:** test_grok_blocks_without_api_key passes; test_privacy_gate_external_bypass_prevention still passes.
- **Committed in:** 639b39d (Task A-10)

**5. [Rule 2 - Missing Critical] pytest.ini in tests/ never loaded by root-level `pytest -v`**
- **Found during:** Task A-13 (full verification)
- **Issue:** CI and local runs invoke `pytest -v` from the repo root; pytest config discovery does not descend into tests/, so the `live` marker produced PytestUnknownMarkWarning and `asyncio_mode=auto` was NOT applied — the async live test would silently run unawaited (false pass) if not skipped.
- **Fix:** Consolidated config into a root `pytest.ini` (asyncio_mode=auto, testpaths, pythonpath, live marker); deleted tests/pytest.ini. Full suite re-run: 61 passed, 1 skipped, 0 warnings.
- **Files modified:** pytest.ini (new), tests/pytest.ini (deleted)
- **Verification:** `py -3.13 -m pytest -v` -> 61 passed, 1 skipped, no marker warning.
- **Committed in:** 7278508 (Task A-13)

**6. [Rule 2 - Missing Critical] Canonical TS contract out of sync with new search schema**
- **Found during:** Task A-9 (ollama_host added to HealthModelsResponse)
- **Issue:** `export_openapi.py` writes a static TS template; the new search endpoint and ollama_host field would not appear in the canonical contract.
- **Fix:** Extended the template with `ollama_host` + `SignalSearchResult`/`SearchFilters`/`SearchRequest`/`SearchResponse` interfaces; regenerated contracts. `git diff` after re-run = empty (0 drift).
- **Files modified:** scripts/export_openapi.py, contracts/openapi.json, frontend/types/api.ts
- **Verification:** export script re-run -> `contract-drift-exit=0`.
- **Committed in:** a82c49f (Task A-9)

---

**Total deviations:** 6 auto-fixed (3 Rule 2 missing-critical, 3 Rule 3 blocking/plan-conflict)
**Impact on plan:** All fixes were necessary for correctness, honest telemetry, and keeping the existing 51-test suite green. No scope creep; no architectural changes beyond the plan.

## Issues Encountered

- fastembed model download took ~80s on first load (HuggingFace) — model now cached; subsequent loads are fast.
- `py -3.13 -c` verification commands need `workdir=backend` (repo root has no `app` package on sys.path) — matches pytest's `pythonpath = backend .` behavior.
- TypeScript gate: skipped — `frontend/node_modules` not present (plan-conditional step); pnpm bootstrap blocked by EPERM (no admin rights to `C:\Program Files\nodejs`). Frontend sources were untouched by this plan; the only TS change is additive, well-formed generated interfaces. CI (ubuntu, pnpm) runs `tsc --noEmit` as before.
- Grok live test skipped locally (no `LIVE_XAI_KEY`) — by design (D-16).

## Known Stubs

None — no placeholder implementations, fabricated telemetry, or unwired components introduced. `gemma_available` now reports honest `false` when Ollama is not running.

## Next Phase Readiness

- Phase 4 frontend can consume `POST /api/v1/search` (contract synced to `frontend/types/api.ts`) and `/api/v1/health/models` (real status + `ollama_host`).
- Ask Athena / node_synthesize can switch to `VectorQueryService` internally (one contract, two consumers, D-07).
- Human UAT deferred to Phase 3 VERIFICATION.md: live Ollama Gemma inference (RTX 3050 GPU), live Grok call (`LIVE_XAI_KEY`), and live-pgvector search exercise (needs a running Postgres with the HNSW index).

---
*Phase: 03-vector-search-llm-provider-execution*
*Completed: 2026-08-15*

## Self-Check: PASSED

- All 8 new files exist on disk (embeddings.py, nodes/embed.py, vector_query.py, endpoints/search.py, embeddings_backfill.py, test_retrieval.py, test_providers_live.py, pytest.ini).
- All 13 task commits present in git history: ae657db, dca78e5, f7d9ebe, 392c365, fbdd63f, 245d3d1, 6ba8b4a, d769991, a82c49f, 639b39d, 6ee1cdb, 388bb09, 7278508.