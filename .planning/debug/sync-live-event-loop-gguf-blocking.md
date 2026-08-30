---
status: resolved
trigger: "/gsd-debug [TELEMETRY] Backend: STARTING... after /api/v1/ingestion/sync-live. UI stuck at refreshing / Priority Signals (0)."
created: 2026-08-28
updated: 2026-08-28
---

# Debug Session: Live Ingestion Pipeline Sync Event Loop Blocking & GGUF Threading

## Symptoms
1. Triggering live web sync (`POST /api/v1/ingestion/sync-live`) completed connector fetching in ~33s, but subsequent LangGraph intelligence pipeline execution caused the backend process to become unresponsive.
2. The `start.py` launcher telemetry reported repeated `[TELEMETRY] Backend: STARTING...` after health check requests timed out against the blocked process.
3. The frontend UI remained stuck on skeleton loader cards (`Priority Signals (0)` / `Refreshing signals...`).

## Root Cause Analysis
1. **Synchronous C++ GGUF Inference in Main Asyncio Event Loop**:
   - In `backend/app/providers/gemma.py`, `_generate()` discovered the local 2.5 GB model `models/gemma-3-4b-it-Q4_K_M.gguf` and executed `_generate_with_local_gguf()` directly on the main thread.
   - Because `llama-cpp-python` CPU inference is compute-intensive and synchronous, running it on the main asyncio thread completely locked the event loop during `node_synthesize` multi-signal reasoning.
   - As a result, Uvicorn was unable to process incoming health check requests (`/api/v1/health`), causing `start.py` to flag the backend as unresponsive.
2. **Missing Thread Lock for Model Loading**:
   - `_load_llama_instance` lacked synchronization guards, risking race conditions if multiple async tasks initialized the model concurrently.

## Key Changes & Fixes Applied
1. **Thread Pool Offloading in [gemma.py](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/providers/gemma.py)**:
   - Offloaded `_generate_with_local_gguf()` to a worker thread using `loop.run_in_executor(None, self._generate_with_local_gguf, gguf_model, prompt)`.
   - The main asyncio event loop now remains 100% free and responsive to concurrent health probes and HTTP requests while GGUF generation runs in the background.
2. **Thread-Safe Model Loading**:
   - Added `self._load_lock = threading.Lock()` around `_load_llama_instance()` to guarantee atomic model loading across worker threads.

## Verification Evidence
- **Provider & Retrieval Tests**: 25 passed, 0 failed (`pytest tests/test_retrieval.py tests/test_provider_matrix.py tests/test_truthfulness_and_invariants.py -v`).
