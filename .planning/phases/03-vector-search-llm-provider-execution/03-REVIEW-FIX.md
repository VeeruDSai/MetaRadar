---
phase: "03"
status: all_fixed
fixed: 8
skipped: 0
findings_in_scope: 8
iteration: 1
---

# Phase 3: Code Review Fix Report

**Fixed at:** 2026-08-15
**Source review:** `.planning/phases/03-vector-search-llm-provider-execution/03-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope: 8 (1 Critical, 7 Warning)
- Fixed: 8
- Skipped: 0

## Fixed Issues

### CR-01: GrokProvider.generate_summary transmits data to api.x.ai with NO privacy gate

**Files modified:** `backend/app/providers/grok.py`, `tests/test_retrieval.py`
**Commit:** `d364ed9`
**Applied fix:** Enforced `validate_privacy_gate` inside `_chat()` — the single choke point for all outbound Grok traffic — via a new `classification: DataClassification = DataClassification.UNKNOWN` parameter; the gate raises `PermissionError` before any HTTP POST when the classification is not PUBLIC/SYNTHETIC. `generate_summary` now calls `_chat(..., classification=DataClassification.UNKNOWN)`, which the gate blocks. `generate_intelligence` behavior is unchanged: it still performs its existing gate check up front and now passes its already-validated `classification` through to `_chat` (PUBLIC/SYNTHETIC still passes both checks; other classes are blocked at the pre-check exactly as before). Added boundary test `test_grok_generate_summary_blocked_by_privacy_gate` mirroring `test_privacy_gate_external_bypass_prevention` — asserts `PermissionError` when `generate_summary` receives PII-like text.
**Verification:** `py -3.13 -m pytest tests/test_retrieval.py tests/test_provider_matrix.py tests/test_privacy_boundary.py -v` → 20 passed.

### WR-01: Backfill CLI can loop forever when embedding persistently fails

**Files modified:** `backend/app/services/embeddings_backfill.py`
**Commit:** `b20e047`
**Applied fix:** Track per-batch progress (`batch_backfilled`) and, when a batch backfills 0 rows while rows remain NULL-embedding, log an error ("Backfill stalled: ... aborting to avoid infinite loop") and `break` instead of re-querying the same failing rows forever. Dry-run mode still breaks on its existing path before the stall check.
**Verification:** `ast.parse` syntax check OK; full suite green.

### WR-02: f-string interpolation of `ef_search` into SQL

**Files modified:** `backend/app/services/vector_query.py`
**Commit:** `9e56258`
**Applied fix:** Replaced `text(f"SET LOCAL hnsw.ef_search = {ef_search}")` with a bound-parameter query: `text("SELECT set_config('hnsw.ef_search', :ef_search, true)")` with `{"ef_search": str(ef_search)}`. `set_config(..., is_local=true)` preserves the transaction-scoped semantics of `SET LOCAL`.
**Verification:** `ast.parse` syntax check OK; full suite green.

### WR-03: Search endpoint only catches SearchError — DB failures surface as 500

**Files modified:** `backend/app/api/v1/endpoints/search.py`
**Commit:** `064f252`
**Applied fix:** Broadened the exception mapping: `SearchError` still maps to 503 with the bounded message; a new generic `except Exception` branch logs via `logger.exception` and returns HTTP 503 with detail "Search service unavailable: database error" — no SQL internals or tracebacks leak to the client.
**Verification:** `ast.parse` syntax check OK; full suite green.

### WR-04: `/health/models` leaks an httpx.AsyncClient on every call

**Files modified:** `backend/app/api/v1/endpoints/health.py`
**Commit:** `c413169`
**Applied fix:** Wrapped the `is_available()` probe in try/finally that closes the lazily-created `provider._client` (`await provider._client.aclose()` when not None), so every `/health/models` poll releases its connection pool.
**Verification:** `ast.parse` syntax check OK; full suite green.

### WR-05: node_embed failure path wipes all validated signals (interacts with new replace_list reducer)

**Files modified:** `backend/app/workflows/nodes/embed.py`
**Commit:** `4758880`
**Applied fix:** The unexpected-exception return no longer includes `"validated_signals": []` — it returns only `{"errors": ..., "node_statuses": {NODE_NAME: "FAILED"}}` so the `replace_list` reducer leaves the validated-signals channel unchanged on failure instead of silently destroying all validated data mid-pipeline.
**Verification:** `py -3.13 -m pytest tests/test_retrieval.py -v` → 11 passed (incl. node_embed tests); full suite green.

### WR-06: `SearchFilters.limit` is dead — never honored; API exposes two competing limit knobs

**Files modified:** `backend/app/services/vector_query.py`, `scripts/export_openapi.py`, `contracts/openapi.json`, `frontend/types/api.ts`, `tests/test_retrieval.py`
**Commit:** `8c81373`
**Applied fix:** Removed the `limit` field from `SearchFilters` (and the now-unused `Field` import) — `top_k` is the single result-limit knob. Updated the canonical contract source of truth `scripts/export_openapi.py` template (dropped `limit?: number`) and re-ran `py -3.13 scripts/export_openapi.py` to regenerate `frontend/types/api.ts`, `contracts/openapi.json`, and the legacy re-export stub (stub unchanged). Updated `test_search_filters_pydantic` to assert the field's removal rather than its constraints; dropped the now-unused `ValidationError` import.
**Verification:** Contract regeneration diff contained only the `limit` removal (+ docstring); `tests/test_retrieval.py` + `tests/test_provider_matrix.py` → 17 passed; `tests/test_contract_drift.py::test_contract_sync_drift` PASSED in full suite.

### WR-07: docker-compose GPU misconfiguration — inference runs on CPU while a GPU is reserved elsewhere

**Files modified:** `docker-compose.yml`
**Commit:** `5b913c5`
**Applied fix:** Moved the `deploy.resources.reservations.devices` nvidia GPU entry (`count: 1`, `capabilities: [gpu]`) from `backend-gpu` to the `ollama` service — the container that actually performs Gemma 3 4B inference — and removed it from `backend-gpu` (the backend delegates inference to Ollama over HTTP and does not use CUDA directly).
**Verification:** `docker compose config --quiet` → exit 0 (config valid).

## Verification Note

All fixes and the full test suite were executed inside the isolated git worktree
(`.claude/worktrees/rf-03-25660-1786743555`, branch `gsd-reviewfix/03-25660`); the worktree
was removed after the branch was fast-forwarded, so the numbers above are not directly
reproducible from the main checkout after teardown (Python deps are installed in the shared
user environment, not the repo). Full suite: **62 passed, 1 skipped** (the skip is the
opt-in `test_grok_live_structured_output` live test requiring `LIVE_XAI_KEY` — expected).

---

_Fixed: 2026-08-15_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 1_