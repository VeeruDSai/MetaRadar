# Concerns
> Property of the developer to fix. Append-only.

## Active Concerns (grouped by severity, each with: description, evidence - file:line or path, impact, recommended action)

### Critical

**C1. Core intelligence pipeline, connectors, and ML stack do not exist — master plan §4/§5/§6/§13 are unimplemented.**
- Description: The repo contains a foundation skeleton (FastAPI + health endpoints + DB models + mock providers + a mock-driven frontend) but ZERO implementation of the actual product: no LangGraph 10-node workflow (`node_ingest` → … → `node_calibrate`), no source connectors (PubMed/NewsAPI/ClinicalTrials.gov/Synthetic/FDA/EMA/Congress/Reddit), no five intelligence mechanisms (Confluence, Lifecycle, Red-Team NLI, Missing-Signal/Watch, Stakeholder Calibration), no spaCy NER, no ontology enrichment, no embeddings, no Ask Athena, no APScheduler. `backend/requirements.txt` (12 lines) still contains no `langgraph`, `langchain`, `spacy`, `transformers`, `torch`, `sentence-transformers`, `tenacity`, or `apscheduler` — the spec stack cannot even be installed.
- Evidence: `backend/requirements.txt`; `backend/app/connectors/base.py:38` (`fetch_latest` raises `NotImplementedError` — sole connector class, no concrete adapters); `backend/app/main.py:50` (only health router registered); `backend/app/providers/*.py` (stubs, see C2); `frontend/lib/api.ts` (mock-only, see H7); `backend/app/services/redteam.py` (mock, see H3)
- Impact: The demo story in Master Plan §9 (Hemgenix durability signals → confluence → lifecycle → red-team → watch → Q1–Q4 → calibration) cannot run in any form. Five hackathon success metrics (§10) are all unmeasurable.
- Recommended action: Treat every §4/§5/§6/§13 item as work-to-do, not done. Priority order: (1) synthetic 500-signal connector + ingestion→validation→dedup path, (2) LangGraph skeleton with state contract (§14.6), (3) one intelligence mechanism end-to-end (Confluence), (4) real summarization via BART. Update `README.md`/`CLAUDE.md` claims to the §14.16 honest vocabulary (`PLANNED`/`SPECIFIED`, not `IMPLEMENTED`).

**C2. LLM provider chain is entirely simulated — Gemma, Grok, and BART are hardcoded string-returning stubs (unchanged).**
- Description: "Local Gemma 3 4B" returns a template sentence `"Significant haemophilia signal identified across {n} evidence excerpts."` — no model load, no GPU, no inference. "Grok" returns an identical hardcoded structure with no HTTP call to xAI. "Degraded BART" is plain character truncation. The provider-agnostic reasoning layer (§13) has never actually invoked a model.
- Evidence: `backend/app/providers/gemma.py:39` (`# Simulated local Gemma 3 4B execution`), `gemma.py:54-58` (hardcoded dict); `backend/app/providers/grok.py:55` (`# Simulated Grok JSON Schema structured output`), `grok.py:69-74`; `backend/app/providers/degraded.py:16-18` (truncation, not BART)
- Impact: Any claim of "reasoning", "suggested actions", model metadata, or fallback behavior is fiction. `tests/test_foundation.py:50` still asserts `provider == "local_gemma"` — CI "verifies" the stub, not the model.
- Recommended action: Either (a) implement real local inference (transformers/llama-cpp + GGUF Q4, or torch) with real BART-large-CNN summarization, or (b) if the hackathon demo is intentionally mock-driven, relabel honestly (§14.16) — `IMPL` stubs must be marked `[MOCK]` in UI and code and README. Never present the template strings as model output.

**C3. `docker compose up --build` is guaranteed to fail — both Dockerfiles are still missing.**
- Description: `docker-compose.yml` builds `backend` and `backend-gpu` from `./backend/Dockerfile` and `frontend` from `./frontend/Dockerfile` (compose lines 39, 67, 101). Neither file exists anywhere in the repo.
- Evidence: `docker-compose.yml:36-39, 65-68, 99-101`; repo glob for `**/Dockerfile*` → no files found (re-verified 2026-08-13); `README.md:693` documents a `backend/Dockerfile` and instructs `docker compose up --build`
- Impact: The entire deployment story (README "Running the System", demo-day "docker compose up on clean machine") is broken out of the box.
- Recommended action: Author `backend/Dockerfile` (python:3.11-slim, uvicorn, `curl` for healthcheck, non-root user) and `frontend/Dockerfile` (node + next standalone output), plus `.dockerignore`. Verify `docker compose up --build` end-to-end this week.

**C4. Alembic scaffolding incomplete — the only migration cannot run (unchanged).**
- Description: A first migration exists (`backend/alembic/versions/001_initial_v51_schema.py`) but there is no `backend/alembic.ini`, no `backend/alembic/env.py`, and no `script.py.mako` — `alembic upgrade head` will fail immediately. Nothing creates the schema.
- Evidence: `backend/alembic/versions/001_initial_v51_schema.py` (present); `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako` → all Test-Path False (re-verified 2026-08-13)
- Impact: Postgres+pgvector is empty at startup; no tables, no sources/assets/companies rows; health `/ready` shows `degraded` and nothing downstream works.
- Recommended action: Add `alembic.ini` + `env.py` (async engine, import `app.models` metadata, migrate target), and commit. Consider docker-compose `alembic upgrade head` step gated on postgres healthy.

**C5. Health endpoints report fabricated status — honesty contract violated (unchanged).**
- Description: `/api/v1/health/models` hardcodes `gemma_available=True` with a comment "Detected at runtime" (it is not detected), and `bart_degraded_available=True`. `/api/v1/health/connectors` reports pubmed/clinical_trials/newsapi as `status="active"` with `quota_remaining=100` despite zero connector classes existing.
- Evidence: `backend/app/api/v1/endpoints/health.py:59` (`gemma_available=True,  # Detected at runtime`), `health.py:62`, `health.py:73-116` (static connector list), `health.py:90` (`quota_remaining=100`)
- Impact: Judges/monitoring see "Gemma loaded, connectors active" when none exist — an integrity failure in a project whose entire pitch is "zero hallucinations, honest evidence."
- Recommended action: Return real state: query the provider factory / model registry for load status; read `Source` rows + connector objects for connector health; default `gemma_available=False` until actual init succeeds. Wire the dashboard to these values instead of fabricating them.

### High

**H1. No PII/PHI detection, redaction, or quarantine code exists — and the provider default classifies everything PUBLIC (unchanged).**
- Description: Success metric 4 ("Confidential / patient data = 0") and §14.2/§12.7 prescribe a dedicated PII/PHI detection + redaction layer with reject/quarantine of low-confidence content. Nothing implements it: no scrubber service, no quarantine table/state. Worse, `ProviderFactory.execute_task` still defaults `classification=DataClassification.PUBLIC` (`factory.py:23`), so the Grok privacy gate (§13.5) would approve any misclassified data for external transmission.
- Evidence: `backend/app/providers/factory.py:23`; no PII/PHI module in `backend/app/services/`; `backend/app/models/__init__.py` (no quarantine table)
- Impact: If real Reddit/news content ever flows, patient-identifiable text could be persisted and (if `LLM_PROVIDER=xai|auto` enabled) transmitted externally.
- Recommended action: Implement the PII/PHI scrubber as a validation-stage service before implementing any live connector; make classification explicit per-payload at ingestion (source whitelist + heuristic), never default PUBLIC; keep `ENABLE_GROK_FALLBACK=false` default (done in `.env.example`).

**H2. The Gemma → Grok → BART fallback chain is dead code — no provider ever raises (unchanged).**
- Description: §13.6/§14.1 mandate a never-crash fallback chain exercised by failure-injection tests (Gemma VRAM/init failure → Grok → BART degraded → source-only). Because every provider returns successfully (stubs), the `except` branches in the factory never execute. No failure-injection tests exist.
- Evidence: `backend/app/providers/factory.py:30-46` (fallback branches); `backend/app/providers/gemma.py` (never raises); `tests/test_foundation.py` (no failure-injection scenarios)
- Impact: The core resilience promise ("the application never crashes because Gemma does not fit") is unverified. On demo day with a real model, a VRAM failure path would trigger for the first time live.
- Recommended action: Add failure-injection unit tests (monkeypatch provider `generate_intelligence` to raise; assert chain order + degraded metadata + `degraded_mode=true`), and implement real init/lazy-load so `LLM_DEVICE`/VRAM failures actually propagate.

**H3. Red-Team service is a mock — NLI model, rule registry, and 19 evidence checks absent (unchanged).**
- Description: `RedTeamNLIService` performs no NLI. It flags a contradiction only when two claims share an asset and differ in `type`, with a hardcoded `confidence: 0.85` and a single rule id `EVIDENCE_CONTRADICTION`. The `RedTeamRule` registry (§14.11) and all 19 evidence checks A–S (§12.7) are not implemented.
- Evidence: `backend/app/services/redteam.py:45-53` (`# Mock pairwise check`, `"confidence": 0.85`)
- Impact: The differentiator mechanism ("system challenges evidence") is non-functional; judges' red-team demo cannot produce real output.
- Recommended action: Implement BART-MNLI zero-shot entailment (CPU) behind the rule registry; seed at minimum checks A, B, D, E, H, I, J, M, N for the demo scenario; keep the candidate cap + caching (already good).

**H4. DB schema incomplete vs §14.2 — missing tables and columns the spec mandates (unchanged).**
- Description: Models/migration lack `contradictions`, `calibration_history`, `scoring_weights`, and the congress/publication/regulatory/access event tables. `SignalSchema.model_metadata` exists in the Pydantic layer (`backend/app/schemas/__init__.py:75`) but `Signal` ORM has no `model_metadata` column. `Event`/`LifecycleEvent` lack `source_id`, breaking the spec's provenance chain. HNSW vector index created in the migration but no embedding pipeline populates `signals.embedding`.
- Evidence: `backend/app/models/__init__.py` (full pass: 16 tables, no contradictions/calibration_history/scoring_weights); `backend/alembic/versions/001_initial_v51_schema.py`
- Impact: Calibration loop (mechanism 5) cannot persist weight history; red-team flags cannot persist; evidence provenance chains are incomplete; schema/schema mismatch will break serialization if `SignalSchema` is used against ORM rows.
- Recommended action: Add the missing tables/columns in migration `002` (append-only style), or amend `001` before first deploy. Align `SignalSchema`/`Signal` field-for-field.

**H5. API surface is only health endpoints — §14.7 business API unimplemented (unchanged).**
- Description: `/api/v1/` exposes only `health|health/ready|health/models|health/connectors` (and root `/`). No `/signals`, `/developments`, `/companies`, `/trials`, `/briefs`, `/feedback`, `/athena`.
- Evidence: `backend/app/main.py:50`; `contracts/openapi.json` (health paths only)
- Impact: The frontend has nothing to fetch. **This now matters more than before** — the new frontend (`frontend/app/`) was built entirely against mock data (see H7), so the integration gap became "no API exists AND the UI doesn't call one."
- Recommended action: Implement the signals/briefs/feedback endpoints over the existing ORM models with Pydantic response schemas, re-export the contract, then wire `frontend/lib/api.ts` to them.

**H7. Frontend is 100% mock-driven — no API call exists anywhere in the new UI (escalated from prior H7).**
- Description: `frontend/lib/api.ts` imports from `frontend/lib/mock-data.ts` and wraps everything in `delay()` promises (360ms). `getHealth()` returns a hardcoded `{ api: 'healthy', latencyMs: 142, sourceCount: 1264 }`; `askAthena()` returns a canned template answer with fixed `confidence: 87`; KPIs ("Active signals 38", "+12.4%"), "Last sync 08:42:18 UTC", "nav-count 12", and `overview.health.lastSync` are all fabricated constants. The dashboard DOES show a "DEMO DATA — All intelligence shown is synthetic" banner (`components/metaradar.tsx:51`) — partial disclosure, good — but the fabricated health/latency/timestamps are presented as live telemetry, and the OLD committed page `frontend/src/app/sources/page.tsx:12-29` still hardclaims "Active" / "Quota: 100/day" / "500 Signals Loaded" with no disclosure (see H-FE1 for which tree actually renders).
- Evidence: `frontend/lib/api.ts:4-10`; `frontend/lib/mock-data.ts:17-30`; `frontend/components/metaradar.tsx:36,40,49,51,55,57`; `frontend/src/app/sources/page.tsx:12-29`
- Impact: The demo shows a beautiful, plausible "live" dashboard that is 100% hardcoded — a judge asking "which endpoint feeds this?" gets "none." Inconsistent with §14.16 honest labeling.
- Recommended action: Wire `lib/api.ts` to real endpoints (`/api/v1/health/*`, `/api/v1/signals`) with TanStack Query or plain fetch once H5 lands; keep the mock as an explicit offline fallback behind an env flag, with the DEMO DATA banner shown whenever mocks are active.

**H8. Postgres/Redis exposed with fixed, committed credentials (unchanged).**
- Description: `docker-compose.yml` publishes ports 5432/6379 with `metaradar:metaradar_pass` (compose lines 9-11, 43, 71) and `backend/app/core/config.py:19` hardcodes the same default URL. `.env.example` repeats it.
- Evidence: `docker-compose.yml:9-11, 43, 71`; `backend/app/core/config.py:19`; `.env.example:2`
- Impact: Anyone on the demo network can connect to the database/cache with known credentials. Acceptable for a local laptop demo, unacceptable for any shared judge machine.
- Recommended action: Make credentials env-driven with non-default dev values, bind DB/Redis to `127.0.0.1` unless needed, note these are dev-only defaults.

**H9. `scripts/export_openapi.py` generates TS from a hardcoded literal, and the CI contract check now protects a DEAD file.**
- Description: The TypeScript contract is written as a static string inside the script — it is not derived from `app.openapi()` (only the JSON export is). CI's drift check (`ci.yml:30-35`) diffs `frontend/src/types/api.ts` against that literal — **but the new frontend imports `@/types/api` which resolves to `frontend/types/api.ts` (hand-rolled, 13 lines, entirely different shapes like `Signal.severity: 'critical'|'high'|...` vs the generated `Signal.priority: "CRITICAL"|...`)**. So CI enforces sync on a file no component imports, while the types the UI actually uses drift freely.
- Evidence: `scripts/export_openapi.py:30-135` (literal `ts_content`); `.github/workflows/ci.yml:30-35`; `frontend/types/api.ts:1-13` vs `frontend/src/types/api.ts:1-105` (two divergent type systems)
- Impact: Contract drift between backend and frontend is guaranteed; "generated" changes require hand-editing. The two `api.ts` files will fight whoever works on either side.
- Recommended action: Generate `frontend/types/api.ts` from `openapi_schema` programmatically (e.g., `openapi-typescript`), point CI at the imported file, and delete the stale `src/types/api.ts` (or keep both trees reconciled — see H-FE1).

**H10. README status claims stale — repo says "Pre-Implementation" while substantial code now exists.**
- Description: `README.md:9` badge "Status-Pre-Implementation", `README.md:~22` "Documentation complete — implementation begins with Week 1" — yet a backend foundation AND a full frontend dashboard exist. The README's promised `docker compose up --build` still fails (C3).
- Evidence: `README.md:9, 22` (badge + status block, re-verified 2026-08-13)
- Impact: Onboarding/executor agents and judges read incorrect state; commands in the README crash.
- Recommended action: Update README status + runnable commands to match reality after C3 is fixed.

**H-FE1. Duplicate frontend trees — `frontend/app/` (new, v0-generated) vs `frontend/src/app/` (old skeleton, committed).**
- Description: The repo now contains TWO Next.js app trees. The new v0-style UI lives at `frontend/app/` (untracked) with `layout.tsx`, `[section]/page.tsx`, and `components/metaradar.tsx`; the old skeleton lives at `frontend/src/app/sources/page.tsx` (committed in `ddf4f97`). Next.js resolves exactly one app directory (root `app/` takes precedence over `src/app` in Next 16), so one tree is dead code — but which one renders is not documented or verified in this repo, and the tsconfig `include: ["**/*.tsx"]` type-checks both. The same duplication exists for types (`frontend/types/api.ts` vs `frontend/src/types/api.ts`, see H9).
- Evidence: `frontend/app/layout.tsx` + `frontend/app/[section]/page.tsx` + `frontend/components/metaradar.tsx` (new); `frontend/src/app/sources/page.tsx` (old, still tracked); `frontend/tsconfig.json:25-31` (includes both trees)
- Impact: If `src/app` wins resolution on some machine/version, `/` has no `page.tsx` in that tree and the demo serves the old bento-card page. If root `app` wins, the old tree is confusing dead code. Either way the CI contract check (H9) sits on the wrong side of the split.
- Recommended action: Delete `frontend/src/` (or migrate its two files into the new tree), confirm `pnpm dev` renders `/dashboard`, and run `next build` in CI to lock in the resolution.

**H-FE2. Frontend build quality is unverifiable and unverified — `ignoreBuildErrors`, broken lint, no CI step.**
- Description: (a) `next.config.mjs:3-5` sets `typescript: { ignoreBuildErrors: true }` — `next build` never type-checks, so any type error sails through. (b) `package.json:9` defines `"lint": "eslint ."` but there is NO eslint config file (`eslint.config.*`/`.eslintrc*` absent, verified by glob) — eslint ^10 requires a flat config, so `pnpm lint` fails out of the box; `eslint-config-next` is installed but never wired. (c) `.github/workflows/ci.yml` has no frontend job at all — no `pnpm install/build/lint`, so nothing in CI exercises the frontend. (d) Local verification was impossible in this environment (no node/pnpm installed), and `frontend/node_modules` does not exist — the 216KB `frontend/pnpm-lock.yaml` was generated elsewhere (v0 sandbox).
- Evidence: `frontend/next.config.mjs:3-5`; `frontend/package.json:5-9,26-36`; `.github/workflows/ci.yml:9-33`; glob `frontend/eslint.config.*` → none
- Impact: The new UI may not build at all (also unverified: `globals.css:3` imports `'shadcn/tailwind.css'`, which depends on the `shadcn` package shipping that path), and the team would not know until demo day. Type errors and lint violations accumulate invisibly.
- Recommended action: Add a CI frontend job (`pnpm install --frozen-lockfile && pnpm build && pnpm lint`), add a flat `eslint.config.mjs` importing `eslint-config-next`, and flip `ignoreBuildErrors` off once `pnpm build` is green.

**H-FE3. The entire new frontend implementation is uncommitted.**
- Description: Git history shows only the old skeleton committed (`ddf4f97`); `git status` shows `M frontend/package.json` plus `?? frontend/app/`, `?? frontend/components/`, `?? frontend/lib/`, `?? frontend/types/`, `?? frontend/tsconfig.json`, `?? frontend/next.config.mjs`, `?? frontend/pnpm-lock.yaml`, `?? frontend/postcss.config.mjs`, `?? frontend/components.json`, `?? frontend/public/` — i.e., the entire new frontend (including its lockfile) has no commit, no history, and would be lost to a `git clean` or a laptop failure. The lockfile being untracked also means dependency resolution is unreproducible for the team.
- Evidence: `git status --short` (re-verified 2026-08-13)
- Impact: The biggest single deliverable since the last audit has zero source safety.
- Recommended action: Commit the new frontend as one atomic commit (with `frontend/.gitignore` verified against `node_modules`/`.next`), then wire H-FE2's CI job so the commit is validated.

### Medium

**M1. No scheduler exists (unchanged).** APScheduler jobs (2-hour fetch, nightly digest, on-demand recalibration, §14.9) are unbuilt and `apscheduler` is not in `backend/requirements.txt`. No `pipeline_runs` writer exists either — the table is defined but never written (observability/`run_id` per §14.12 is absent). Evidence: `backend/requirements.txt`; `backend/app/main.py` (no startup scheduler); `backend/app/models/__init__.py:13-27` (`PipelineRun` defined, unused).

**M2. Requirements unpinned + missing ML deps (unchanged).** `backend/requirements.txt` uses `>=` and omits the entire ML layer. `datetime.utcnow` is used in 18 timezone-aware model columns (`backend/app/models/__init__.py:17, 64, 91-92, 111, 122, 132, 149, 173, 193, 221, 234, 247, 258`) and 4 more in `base.py`/`schemas` — DeprecationWarning on Python 3.12+, and CI targets 3.11.

**M3. Naive datetimes in timezone-aware columns (unchanged).** `DateTime(timezone=True)` columns receive naive `datetime.utcnow()` defaults; comparing with aware `published_at` values (from connectors) via asyncpg can raise "can't subtract offset-naive and offset-aware" errors in real use. Evidence: `backend/app/models/__init__.py:17, 91, 111, 132, 173, ...`. Fix: `datetime.now(timezone.utc)` throughout.

**M4. Test suite is one self-validating script (unchanged).** `tests/test_foundation.py` is a `print`-based script (run via `python` in CI, not pytest), asserts the stub providers "verified" (`test_foundation.py:50-51`), and covers 0% of the DB models, health endpoints, dedup upsert, red-team, fallback chain, or any frontend artifact. No pytest config, no coverage, no failure-injection tests. Evidence: `tests/test_foundation.py:43-64`; `.github/workflows/ci.yml:26-28`.

**M5. Domain config quality gate absent (unchanged).** `config/haemophilia.yaml` loads but nothing validates `approval_status`/`approval_date`/`last_verified` per the §14.5 ontology quality gate, and no unit test enforces the three verified mappings (fitusiran→Qfitlia, concizumab→Alhemo, marstacimab→Hympavzi). The test assertion `len(config.assets) >= 7` (`tests/test_foundation.py:25`) is brittle. Evidence: `backend/app/core/domain_config.py:60-78`.

**M6. `ProviderFactory` instantiates all providers at import time (unchanged).** `provider_factory = ProviderFactory()` runs at module import (`backend/app/providers/factory.py:49`), constructing Gemma/Grok/Degraded eagerly. Harmless today (stubs), but once Gemma actually loads weights it will block app startup and defeat lazy fallback.

**M7. Freshness-class labelling errors (unchanged).** `health.py:74-78` labels PubMed `near_real_time` but Master Plan §5 defines PubMed as `delayed`/`batch`. Evidence: `backend/app/api/v1/endpoints/health.py:74-78` vs `docs/METARADAR_MASTER_PLAN_v5.0.md` §5.

**M8. Grok provider details inconsistent with spec (unchanged).** `grok-beta` is hardcoded (not `GROK_MODEL`-configurable per §14.1), no JSON-Schema structured outputs, no three-layer validation (§13.4), and `generate_summary` is mocked (`backend/app/providers/grok.py:23, 41-43`).

**M9. Signal-type values unvalidated / access signals missing (unchanged).** `signal_type` is a free string in both schema and ORM — §3 canonical values (CONGRESS/PUBLICATION subtypes, §12.4 `ACCESS_*` types) are not enumerated or validated anywhere. Evidence: `backend/app/schemas/__init__.py:67`; `config/haemophilia.yaml` (no CONGRESS/ACCESS subtypes).

**M10. `upsert_signal` commits inside the helper (unchanged).** `backend/app/services/deduplication.py:82` calls `session.commit()` — a caller wrapping multiple signals in one transaction gets partial commits per row. Fix: move commit responsibility to the caller/service boundary.

**M11. `docker-compose.yml` uses obsolete `version: "3.8"` key (unchanged)** (informational in Compose v2; harmless but noisy) and healthchecks rely on `curl` inside backend images that don't exist yet (C3). Evidence: `docker-compose.yml:1, 58, 93`.

**M12. Compiled `__pycache__` artifacts present in the tree (unchanged)** — cpython-313 `.pyc` for `app`, `db`, `api`, `providers`, `services`, `models`, `schemas` (gitignored but proof of dirty Python-3.13 local runs mismatched with CI 3.11). Evidence: `backend/**/__pycache__/*.cpython-313.pyc`.

**M13. Domain-config discovery is layout-relative (unchanged).** `backend/app/core/domain_config.py:65-68` computes `Path(__file__).resolve().parents[3]` → assumes repo-root/config layout; in Docker this silently resolves to `/app/config` only if the image mirrors the layout — unverifiable until a Dockerfile exists.

**M-FE4. `NEXT_PUBLIC_API_BASE_URL` is dead configuration.** `docker-compose.yml:105` passes `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` to the frontend, but no frontend file reads any env var — grep of `frontend/**/*.{ts,tsx,mjs}` for `NEXT_PUBLIC|API_URL|8000|localhost` finds zero matches outside `components.json` (a schema URL). The env var is the only trace of the intended backend wiring. Evidence: `docker-compose.yml:105`; `frontend/lib/api.ts` (no env reads).

**M-FE5. Frontend provenance is a v0.dev export, not a deliberate build.** `package.json:2` name is `"my-project"` (create-next-app/v0 default), `app/layout.tsx:8` metadata `generator: 'v0.app'`, and `frontend/.gitignore` is a "v0 sandbox internal files" template (`__v0_runtime_loader.js`, `__v0_devtools.tsx`, `.snowflake/`, `.vercel/`). The `@vercel/analytics` package phones home on production builds (`app/layout.tsx:45`). None of this is wrong per se, but it signals the UI was generated outside the repo and pasted in — consistent with H-FE3 (nothing committed) and H7 (mock data). Also, no node version pinning (no `packageManager` field, no `.nvmrc`) for a Next 16 codebase. Evidence: `frontend/package.json:2,37-41`; `frontend/app/layout.tsx:8,45`; `frontend/.gitignore:1-6`.

### Low

**L1. `chunk_text_for_embedding` approximates tokens as `max_tokens * 4` characters** (`backend/app/services/deduplication.py:45-49`) — crude heuristic; replace with the tokenizer's real `max_seq_length` once `sentence-transformers` lands.

**L2. Gemma `generate_summary` slices by characters (`backend/app/providers/gemma.py:29-30`), not tokens**, and ignores `MAX_OUTPUT_TOKENS` entirely.

**L3. `SignalSchema.version` fields duplicated as constants** (`5.1.0` in `backend/app/core/config.py:16`, `backend/app/schemas/__init__.py:111`) — single source recommended.

**L4. Health connector entries never carry `last_success`/`last_error`** — always None (`health.py:73-116`), so the "last success/error" honesty fields are decorative until real connectors exist.

**L5. No `.python-version`/`runtime.txt` pinning Python** — CI 3.11 vs local 3.13 drift (see M2). **Add `.nvmrc` (or `packageManager` in `frontend/package.json`) for the Node side too** (see M-FE5).

**L-FE6. Public placeholder assets shipped** — `frontend/public/placeholder.jpg|svg|logo|user.jpg` are verbatim v0 defaults and unused by the new UI; harmless but clutter. The `GenericPage` components that show "Connected evidence will appear here." (`components/metaradar.tsx:59`) are honestly-labeled placeholders — acceptable, and a good model for further mock labeling.

## Resolved Concerns (note what was fixed, when)

- **All implementation code uncommitted (prior C6, resolved 2026-08-13 for the backend):** `ddf4f97` "feat: initial project structure, backend foundational services, configuration, and codebase documentation" commits the backend foundation (16 backend files), CI workflow, and the old frontend skeleton. **Remaining gap:** the entire new frontend is still untracked — tracked as H-FE3.
- **No CI/CD pipeline (resolved 2026-08-13):** `.github/workflows/ci.yml` exists — installs backend deps, runs `tests/test_foundation.py`, enforces OpenAPI→TS contract sync on push/PR to main/develop. It still has no frontend job (H-FE2) and its contract check guards a dead file (H9), but the pipeline exists and ships.
- **Frontend cannot build — missing Next.js scaffolding (prior H6, resolved 2026-08-13):** `frontend/tsconfig.json`, `next.config.mjs`, `postcss.config.mjs`, `components.json`, `app/layout.tsx`, `app/globals.css` (~22KB, Tailwind 4 + dark theme), and `app/[section]/page.tsx` are all present, and Tailwind is now v4 (`@tailwindcss/postcss` in `frontend/package.json:27`). The structural scaffold concern is replaced by H-FE1/H-FE2 (dual trees, unverified build, broken lint) — verify `pnpm build` before calling this fully done.
- **Deployment target (partially resolved):** `docker-compose.yml` + seeded volumes (pgvector/pg16, redis:7, `/models` cache) and healthchecks exist — still blocked by missing Dockerfiles (C3) and alembic scaffold (C4).
- **Docs-only repo (transformed):** the original "#1 concern" is fully inverted — there is now a backend foundation AND a substantial frontend, both of which claim more than they deliver (C2/C5 stubs on the backend, H7 mock-only UI on the frontend).

## Trend Notes (how concerns have evolved)

- **Two surfaces now claim more than they do.** The 2026-08-13 pre-implementation audit found a docs-only repo; the mid-day audit found a stubbed backend; now BOTH halves of the stack exist and BOTH overclaim: the backend health endpoints report Gemma "available" and connectors "active", and the frontend shows a live-looking dashboard with "Last sync 08:42:18 UTC" and "1,264 synthetic records" — one half fabricates at the API layer, the other at the UI layer. The §14.16 honest-vocabulary guardrail is the single most-violated discipline in the repo.
- **Good sign: the frontend labels itself.** The new dashboard's "All intelligence shown is synthetic and for interface demonstration only" banner (`frontend/components/metaradar.tsx:51`) and "Demo environment · Synthetic data" footer are exactly the §14.16 posture — the team knows how to be honest when they choose to be. The gap is deliberate: the banner covers the mock signals but not the fabricated health/latency/timestamps.
- **Frontend arrived as a downloaded artifact, not an integration.** v0.dev provenance ("my-project", `generator: 'v0.app'`, v0 `.gitignore`), zero `fetch()` calls, and the leftover `src/` skeleton suggest the UI was generated outside the repo and pasted over the old tree without reconciliation. The highest-value near-term work is now **integration, not generation**: delete the dead tree, commit the new tree, add a CI frontend job, and wire `lib/api.ts` to the first real endpoints (health + signals).
- **Backend concerns held almost perfectly steady** between the two audits — the only backend delta is that the foundation got committed. C1–C5, H1–H5, H8, and M1–M13 are all re-verified unchanged; the risk is not regression but non-movement. The clock to demo day burns mostly on the pipeline (C1) and connectors.
- **Next expected move (updated):** (1) commit the new frontend + delete `frontend/src/`, (2) add CI frontend job + flat eslint config + flip `ignoreBuildErrors`, (3) author the two Dockerfiles + alembic scaffold so `docker compose up` + `alembic upgrade head` work, (4) build the first real end-to-end slice (Synthetic connector → validation/dedup → `/signals` API → real `lib/api.ts` fetch), and (5) only then touch real providers/models.

---

*Concerns audit: 2026-08-13*