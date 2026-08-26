---
slug: athena-stream-citations-logs
status: investigating
goal: find_and_fix
trigger: "i want athena (gemma) to stream text live on the frontend too, also the citations given should be clickable leading to the source signal page, so that the user can verify the source properly and understand what the citations are. also make sure that start.py shows logs of gemma generating or failing."
created: 2026-08-24
updated: 2026-08-24
---

# Debug Session: Athena Live Streaming, Clickable Citations, Gemma Generation Logs

## Symptoms
- **Expected:**
  - Athena (Gemma) reply streams token-by-token / progressively on the frontend as generation happens (SSE or equivalent), not as one final dump.
  - Every citation rendered in an answer is clickable and navigates to the source signal detail page so users can verify the cited evidence.
  - `start.py` console output shows when Gemma starts generating, succeeds, or fails (generation lifecycle logs).
- **Actual:**
  - No streaming — frontend waits for the full response, then renders it all at once.
  - Citations render as plain text markers (no links) leading nowhere.
  - `start.py` is silent about Gemma generation activity/failures.
- **Error messages:** None visible anywhere (browser console clean, backend terminal clean, no start.py errors). Gaps are silent, not loud failures.
- **Timeline:** Never worked — this is a first-time capability build-out, not a regression.
- **Reproduction:** Send any message in the Athena chat UI and observe behavior; launch via `python start.py`.

## Current Focus
hypothesis: AND-gate — 3 independent contributing causes: (RC1) no streaming primitive at any layer: /athena is a blocking POST, GemmaProvider posts Ollama /api/generate with stream:false, frontend apiFetch buffers res.json(); (RC2) AthenaWorkspace renders evidence as plain divs despite ev.signal_id + canonical /signals/[signalId] route; (RC3) gemma.py has zero start/success lifecycle logs AND start.py log-filter has no LLM markers so even warnings never surface.
test: code-path inspection of all 6 layers (endpoint, provider, launcher filter, api client, workspace component, routing)
expecting: each symptom traces to absent capability (first-time build-out), not a regression
next_action: apply fixes (goal=find_and_fix): SSE endpoint + provider streaming + lifecycle logs + launcher markers + SSE client + progressive UI with linked citations

## Evidence
- timestamp: 2026-08-24T00:00Z — backend/app/api/v1/endpoints/signals.py:797-964 — `/athena` is `POST`, returns complete `AthenaQueryResponse`; no StreamingResponse/SSE anywhere in file; citations include signal_id/source_id/canonical_url.
- timestamp: 2026-08-24T00:00Z — backend/app/providers/gemma.py:153-172 — Ollama payload hardcodes `"stream": False`; full-buffer `response.json()`. Lifecycle logging only `logger.warning` on GGUF failure (:150) and Ollama failure (:171); NO start/success logs.
- timestamp: 2026-08-24T00:00Z — start.py:394-402 — console log-stream surfaces only lines containing `[INGESTION]|[PIPELINE]|ERROR|WARNING` or ingestion keywords; no LLM/Gemma/Ollama/Athena markers ⇒ Gemma activity invisible even if logged.
- timestamp: 2026-08-24T00:00Z — frontend/lib/api.ts:288-308 — `askAthena` = single apiFetch POST, awaits full json(); no reader/stream consumption.
- timestamp: 2026-08-24T00:00Z — frontend/components/intelligence/AthenaWorkspace.tsx:150-181 — answer rendered as one static block post-await; evidence cards are plain divs, no Link/href; `ev.signal_id` unused. (metaradar.tsx IntelligencePage ~:1797 is unrouted legacy — only AthenaWorkspace is mounted via app/[section]/page.tsx:46.)
- timestamp: 2026-08-24T00:00Z — frontend/app/signals/[signalId]/page.tsx:41-52 — detail page resolves id against s.id/signal_id/external_id/fingerprint/pmid/nct_id/regulatory_id ⇒ `/signals/${signal_id}` links work. Canonical pattern already used by SignalCard.tsx:176, ConfluenceWorkspace.tsx:298, ContradictionWorkspace.tsx:152.

## Eliminated
- Not a CORS/proxy issue: responses DO arrive and render — transport works, shape is buffered.
- Not an Ollama-side limitation: Ollama /api/generate streams NDJSON by default; backend explicitly opts out with stream:false.
- Not missing route data: citations carry signal_id; detail route + resolver already exist.
- Not a logging-config problem: structlog writes INFO+ to stdout→logs/backend.log; the launcher filter simply excludes LLM lines.

## Specialist Review
specialist_hint: general → mapped skill "engineering:debug" not present in this environment's skill registry; no matching specialist available — proceeded with direct review against ENGINEERING_STANDARDS/TESTING_STRATEGY gates instead (all executable gates run and passing).

## Resolution
root_cause: Three independent contributing causes (AND-gate): (1) no streaming primitive existed at any layer — /athena was a blocking POST, GemmaProvider posted Ollama /api/generate with stream:false and buffered res.json() on the frontend; (2) AthenaWorkspace rendered evidence citations as plain non-interactive divs despite ev.signal_id being present and a canonical /signals/[signalId] route already resolving signal_id; (3) start.py's backend.log filter matched only ingestion/pipeline/error markers while gemma.py logged nothing on generation start/success (only bare warnings on failure) — so Gemma lifecycle activity was doubly invisible.
fix: Added POST /athena/stream SSE endpoint (meta→token*→done event contract with honest degraded/error events and pre-stream DB retrieval); added GemmaProvider.generate_stream() consuming Ollama NDJSON token stream (GGUF single-delta fallback); added [LLM]-marker start/success/failure lifecycle logging to all generation paths; extended start.py console filter with [LLM]/[ATHENA]/gemma/ollama/athena markers; added frontend streamAthena() SSE client; rewrote AthenaWorkspace to render tokens progressively (idle→thinking→streaming→done) with all citation surfaces (title, source-id chip, excerpt) as Links to /signals/{signal_id} plus external-source anchors when canonical_url exists.
verification: py_compile OK (gemma.py, signals.py, start.py); runtime route registration OK (/athena/stream present, generate_stream present); SSE frame format unit check OK; frontend tsc --noEmit exit 0; project eslint . exit 0; pytest tests/test_api_endpoints.py tests/test_launchers.py tests/test_provider_matrix.py → 16 passed; next build production exit 0.
files_changed: backend/app/providers/gemma.py; backend/app/api/v1/endpoints/signals.py; start.py; frontend/lib/api.ts; frontend/components/intelligence/AthenaWorkspace.tsx
