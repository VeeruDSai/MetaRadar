# Concerns
> Property of the developer to fix. Append-only.

## Active Concerns (grouped by severity, each with: description, evidence - file:line or path, impact, recommended action)

### Critical

**C1. Core intelligence pipeline, connectors, and ML stack do not exist — master plan §4/§5/§6/§13 are unimplemented.**
- Description: The repo contains a foundation skeleton (FastAPI + health endpoints + DB models + mock providers) but ZERO implementation of the actual product: no LangGraph 10-node workflow (`node_ingest` → … → `node_calibrate`), no source connectors (PubMed/NewsAPI/ClinicalTrials.gov/Synthetic/FDA/EMA/Congress/Reddit), no five intelligence mechanisms (Confluence, Lifecycle, Red-Team NLI, Missing-Signal/Watch, Stakeholder Calibration), no spaCy NER, no ontology enrichment, no embeddings, no Ask Athena, no APScheduler. `backend/requirements.txt` (12 lines) contains no `langgraph`, `langchain`, `spacy`, `transformers`, `torch`, `sentence-transformers`, `tenacity`, or `apscheduler` — the spec stack cannot even be installed.
- Evidence: `backend/requirements.txt`; `backend/app/connectors/base.py:38` (`fetch_latest` raises `NotImplementedError` — sole connector class, no concrete adapters); `backend/app/providers/*.py` (stubs, see C2); `backend/app/main.py:50` (only health router registered); `backend/app/services/` (only `deduplication.py` + mock `redteam.py`)
- Impact: The demo story in Master Plan §9 (Hemgenix durability signals → confluence → lifecycle → red-team → watch → Q1–Q4 → calibration) cannot run in any form. Five hackathon success metrics (§10) are all unmeasurable.
- Recommended action: Treat every §4/§5/§6/§13 item as work-to-do, not done. Priority order: (1) synthetic 500-signal connector + ingestion→validation→dedup path, (2) LangGraph skeleton with state contract (§14.6), (3) one intelligence mechanism end-to-end (Confluence), (4) real summarization via BART. Update `README.md`/`CLAUDE.md` claims to the §14.16 honest vocabulary (`PLANNED`/`SPECIFIED`, not `IMPLEMENTED`).

**C2. LLM provider chain is entirely simulated — Gemma, Grok, and BART are hardcoded string-returning stubs.**
- Description: "Local Gemma 3 4B" returns a template sentence `"Significant haemophilia signal identified across {n} evidence excerpts."` — no model load, no GPU, no inference. "Grok" returns an identical hardcoded structure with no HTTP call to xAI. "Degraded BART" is plain character truncation (first 297 chars). The provider-agnostic reasoning layer (§13) has never actually invoked a model.
- Evidence: `backend/app/providers/gemma.py:39` (`# Simulated local Gemma 3 4B execution`), `backend/app/providers/gemma.py:54-58` (hardcoded dict); `backend/app/providers/grok.py:55` (`# Simulated Grok JSON Schema structured output`), `grok.py:69-74`; `backend/app/providers/degraded.py:16-18` (truncation, not BART)
- Impact: Any claim of "reasoning", "suggested actions", model metadata, or fallback behavior is fiction. A judge asking "show me the Gemma output" gets a template. Also `tests/test_foundation.py:50` asserts `provider == "local_gemma"` — CI "verifies" the stub, not the model.
- Recommended action: Either (a) implement real local inference (transformers/llama-cpp + GGUF Q4, or torch) with real BART-large-CNN summarization, or (b) if the hackathon demo is intentionally mock-driven, relabel honestly (§14.16) — `IMPL` stubs must be marked `[MOCK]` in UI and code and README. Never present the template strings as model output.

**C3. `docker compose up --build` is guaranteed to fail — both Dockerfiles are missing.**
- Description: `docker-compose.yml` builds `backend` and `backend-gpu` from `./backend/Dockerfile` and `frontend` from `./frontend/Dockerfile` (compose lines 36-39, 65-68, 99-101). Neither file exists anywhere in the repo.
- Evidence: `docker-compose.yml:36-39, 65-68, 99-101`; repo glob for `**/Dockerfile*` → no files found; `README.md:693` documents a `backend/Dockerfile` and `README.md:793` instructs `docker compose up --build`
- Impact: The entire deployment story (README "Running the System", demo-day "docker compose up on clean machine") is broken out of the box.
- Recommended action: Author `backend/Dockerfile` (python:3.11-slim, uvicorn, `curl` for healthcheck, non-root user) and `frontend/Dockerfile` (node:20 + next standalone output), plus `.dockerignore`. Verify `docker compose up --build` end-to-end this week.

**C4. Alembic scaffolding incomplete — the only migration cannot run.**
- Description: A first migration exists (`backend/alembic/versions/001_initial_v51_schema.py`) but there is no `backend/alembic.ini`, no `backend/alembic/env.py`, and no `script.py.mako` — `alembic upgrade head` will fail immediately. Nothing creates the schema.
- Evidence: `backend/alembic/versions/001_initial_v51_schema.py` (present); `backend/alembic.ini` and `backend/alembic/env.py` → Test-Path False; `backend/requirements.txt` includes `alembic>=1.13.1` but no scaffold
- Impact: Postgres+pgvector is empty at startup; no tables, no sources/assets/companies rows; health `/ready` shows `degraded` and nothing downstream works.
- Recommended action: Add `alembic.ini` + `env.py` (async engine, import `app.models` metadata, migrate target), and commit. Consider docker-compose `alembic upgrade head` step gated on postgres healthy.

**C5. Health endpoints report fabricated status — honesty contract violated.**
- Description: `/api/v1/health/models` hardcodes `gemma_available=True` with a comment "Detected at runtime" (it is not detected), and `bart_degraded_available=True`. `/api/v1/health/connectors` reports pubmed/clinical_trials/newsapi as `status="active"` with `quota_remaining=100` despite zero connector classes existing. This directly contradicts Master Plan §14.7 ("Gemma (loaded/available) reported separately", "source health degrades independently — a failed optional source must not make the app appear dead") and §14.16's honest implementation-status vocabulary.
- Evidence: `backend/app/api/v1/endpoints/health.py:59` (`gemma_available=True,  # Detected at runtime`), `health.py:62` (`bart_degraded_available=True`), `health.py:73-116` (static connector list), `health.py:90` (`quota_remaining=100`)
- Impact: Judges/monitoring see "Gemma loaded, connectors active" when none exist — an integrity failure in a project whose entire pitch is "zero hallucinations, honest evidence."
- Recommended action: Return real state: query the provider factory / model registry for load status; read `Source` rows + connector objects for connector health; default `gemma_available=False` until actual init succeeds. Wire the dashboard to these values instead of hardcoding (`frontend/src/app/sources/page.tsx:12-18`).

**C6. All implementation code is uncommitted — no history, CI never runs.**
- Description: `git ls-files` = 31 files, all docs. `backend/`, `frontend/`, `config/`, `contracts/`, `scripts/`, `tests/`, `docker-compose.yml`, `.github/`, `.env.example`, `.gitignore` are all untracked (`git status` shows `??` for every one).
- Evidence: `git status --short` (all implementation dirs `??`); `git log --oneline -15` shows docs-only history
- Impact: Four weeks of hardening docs but zero source safety: no rollback point, CI (`.github/workflows/ci.yml`) has never executed, and a single `git clean`/laptop failure loses the foundation.
- Recommended action: Commit the foundation as one or two atomic commits on a feature branch, wire CI to run foundation tests + contract sync (already defined), then add a `.gitignore` check to ensure `__pycache__`/`.env` never land.

### High

**H1. No PII/PHI detection, redaction, or quarantine code exists — and the provider default classifies everything PUBLIC.**
- Description: Success metric 4 ("Confidential / patient data = 0") and §14.2/§12.7 prescribe a dedicated PII/PHI detection + redaction layer with reject/quarantine of low-confidence content. Nothing implements it: no scrubber service, no quarantine table/state. Worse, `ProviderFactory.execute_task` defaults `classification=DataClassification.PUBLIC` (`factory.py:23`), so the Grok privacy gate (§13.5) would approve any misclassified data for external transmission.
- Evidence: no PII/PHI module in `backend/app/services/`; `backend/app/providers/factory.py:23`; `backend/app/models/__init__.py` (no quarantine column/table)
- Impact: If real Reddit/news content ever flows, patient-identifiable text could be persisted and (if `LLM_PROVIDER=xai|auto` enabled) transmitted externally.
- Recommended action: Implement the PII/PHI scrubber as a validation-stage service before implementing any live connector; make classification explicit per-payload at ingestion (source whitelist + heuristic), never default PUBLIC; keep `ENABLE_GROK_FALLBACK=false` default (already done in `.env.example:14`).

**H2. The Gemma → Grok → BART fallback chain is dead code — no provider ever raises.**
- Description: §13.6/§14.1 mandate a never-crash fallback chain exercised by failure-injection tests (Gemma VRAM/init failure → Grok → BART degraded → source-only). Because every provider returns successfully (stubs), the `except` branches in the factory never execute; `DegradedProvider` is unreachable via `execute_task`. No failure-injection tests exist.
- Evidence: `backend/app/providers/factory.py:30-46` (fallback branches); `backend/app/providers/gemma.py` (never raises); `tests/test_foundation.py` (no failure-injection scenarios)
- Impact: The core resilience promise ("the application never crashes because Gemma does not fit") is unverified. On demo day with a real model, a VRAM failure path would trigger for the first time live.
- Recommended action: Add failure-injection unit tests (monkeypatch provider `generate_intelligence` to raise; assert chain order + degraded metadata + `degraded_mode=true`), and implement real init/lazy-load so `LLM_DEVICE`/VRAM failures actually propagate.

**H3. Red-Team service is a mock — NLI model, rule registry, and 19 evidence checks absent.**
- Description: `RedTeamNLIService` performs no NLI. It flags a contradiction only when two claims share an asset and differ in `type`, with a hardcoded `confidence: 0.85` and a single rule id `EVIDENCE_CONTRADICTION`. The `RedTeamRule` registry (§14.11) and all 19 evidence checks A–S (§12.7, SRS FR line 456) — causality, denominator, population mismatch, approval≠access, etc. — are not implemented.
- Evidence: `backend/app/services/redteam.py:46-53` (`# Mock pairwise check`), `redteam.py:51` (`"confidence": 0.85`)
- Impact: The differentiator mechanism ("system challenges evidence") is non-functional; judges' red-team demo (Hemgenix trial-vs-real-world contradiction) cannot produce real output.
- Recommended action: Implement BART-MNLI zero-shot entailment (CPU) behind the rule registry; seed at minimum checks A, B, D, E, H, I, J, M, N for the demo scenario; keep the candidate cap + caching (already good).

**H4. DB schema incomplete vs §14.2 — missing tables and columns the spec mandates (and code expects).**
- Description: Models/migration lack `contradictions`, `calibration_history`, `scoring_weights`, and the congress/publication/regulatory/access event tables. `SignalSchema.model_metadata` exists in the Pydantic layer (`backend/app/schemas/__init__.py:75`) but `Signal` ORM has no `model_metadata` column. `Event`/`LifecycleEvent` lack `source_id`, breaking the spec's `event_type · event_date · development_id · source_id` provenance (Master Plan §6 mechanism 2). HNSW vector index created (`001_initial_v51_schema.py:194-200`) but no embedding pipeline populates `signals.embedding`.
- Evidence: `backend/app/models/__init__.py` (full pass: no contradictions/calibration_history/scoring_weights/models_metadata), `backend/alembic/versions/001_initial_v51_schema.py` (same)
- Impact: Calibration loop (mechanism 5) cannot persist weight history; red-team flags cannot persist; evidence provenance chains are incomplete; schema/schema mismatch will break serialization if `SignalSchema` is used against ORM rows.
- Recommended action: Add the missing tables/columns in migration `002` (append-only style), or amend `001` before first deploy. Align `SignalSchema`/`Signal` field-for-field.

**H5. API surface is only health endpoints — §14.7 business API unimplemented.**
- Description: `/api/v1/` exposes only `health|health/ready|health/models|health/connectors` (and root `/`). No `/signals`, `/developments`, `/companies`, `/trials`, `/briefs`, `/feedback`, `/athena`. `contracts/openapi.json` contains only health paths.
- Evidence: `backend/app/main.py:50`; `contracts/openapi.json` (paths list)
- Impact: The frontend has nothing to fetch; the Four-Question UI, calibration widget, Watch alerts, and Ask Athena cannot be built against real data.
- Recommended action: Implement the signals/briefs/feedback endpoints over the existing ORM models (they're already defined) with Pydantic response schemas, then re-export the contract.

**H6. Frontend cannot build — missing Next.js scaffolding and config.**
- Description: `frontend/` contains only `package.json`, `src/types/api.ts`, and `src/app/sources/page.tsx`. Missing: `tsconfig.json`, `next.config.*`, `tailwind.config.*`, `postcss.config.*`, `src/app/layout.tsx`, `src/app/globals.css`, any eslint/prettier config, and `eslint` devDependency. `next build` fails without tsconfig/layout; `next lint` fails without eslint. The `bento-card` class used in `sources/page.tsx:20` is defined nowhere. Tailwind is `^3.4.1` while CLAUDE.md/STACK.md claim TailwindCSS 4; no shadcn/ui (`components.json` absent).
- Evidence: glob `frontend/**` → 3 files; `frontend/package.json:13-30` (deps); `frontend/src/app/sources/page.tsx:20`
- Impact: Docker frontend build fails; even `npm run dev` cannot render. Combined with C3, both containers are non-functional.
- Recommended action: Scaffold the Next.js app properly (`create-next-app`-equivalent configs), add `layout.tsx`/`globals.css`, pin Tailwind declared version, add `components.json` if shadcn/ui is used. Verify `npm run build` in CI.

**H7. Frontend shows fabricated connector status — no API call exists.**
- Description: `sources/page.tsx` hardcodes "Quota: 100/day", "500 Signals Loaded", statuses "Active/Ready" for seven connectors. TanStack Query is installed but unused. There is no data-fetching code anywhere in the frontend.
- Evidence: `frontend/src/app/sources/page.tsx:12-29`; `frontend/package.json:19` (`@tanstack/react-query`)
- Impact: Dashboard presents unverified claims as live — inconsistent with the "honest labeling" requirement (§5 freshness classes, §14.16).
- Recommended action: Replace with TanStack Query calls to `/api/v1/health/connectors` + `/api/v1/signals`; derive status/freshness from the API. This is the first real frontend↔backend integration.

**H8. Postgres/Redis exposed with fixed, committed credentials.**
- Description: `docker-compose.yml` publishes ports 5432/6379 to `0.0.0.0` with `metaradar:metaradar_pass` (compose lines 8-14, 24-28, 43) and `backend/app/core/config.py:19` hardcodes the same default URL. `.env.example` repeats it.
- Evidence: `docker-compose.yml:9-11, 43, 71`; `backend/app/core/config.py:19`; `.env.example:2`
- Impact: Anyone on the demo network can connect to the database/cache with known credentials and read/alter signals. Acceptable for a local laptop demo, unacceptable for any shared judge machine.
- Recommended action: Make credentials env-driven with non-default dev values, bind DB/Redis to `127.0.0.1` unless needed, add a note that these are dev-only defaults. Never commit a real `.env` (`.gitignore` already covers it).

**H9. `scripts/export_openapi.py` generates TS types from a hardcoded literal, not the OpenAPI schema.**
- Description: The TypeScript contract in `frontend/src/types/api.ts` is written as a static string inside the script — it is not derived from `app.openapi()`. CI's drift check (`ci.yml:33-35`) diffs the committed file against this literal only, so adding a field to a Pydantic schema (e.g., `inhibitor_status`, `factor` from §12.1) would silently drop it from the frontend contract with CI still green.
- Evidence: `scripts/export_openapi.py:30-135` (literal `ts_content`), `.github/workflows/ci.yml:30-35`
- Impact: Contract drift between backend and frontend is guaranteed as the schema grows; future "generated" changes require hand-editing two files.
- Recommended action: Generate TS from `openapi_schema` programmatically (e.g., `openapi-typescript`), or at minimum add a test asserting every property in `SignalSchema` appears in `api.ts`.

**H10. README status claims stale — repo says "Pre-Implementation" while code now exists (and is broken).**
- Description: `README.md:9` badge "Status-Pre-Implementation", `README.md:22` "Documentation complete — implementation begins with Week 1" — yet a foundation skeleton exists. Meanwhile the docs' promised `docker compose up --build` (README:793) fails (C3).
- Evidence: `README.md:9, 22, 26, 693, 793`
- Impact: Onboarding/executor agents and judges read incorrect state; commands in the README crash.
- Recommended action: Update README status + runnable commands to match reality after C3/H6 are fixed.

### Medium

**M1. No scheduler exists.** APScheduler jobs (2-hour fetch, nightly digest, on-demand recalibration, §14.9) are unbuilt and `apscheduler` is not in `backend/requirements.txt`. No `pipeline_runs` writer exists either (table defined but never written — observability/`run_id` per §14.12 is absent). Evidence: `backend/requirements.txt`; `backend/app/main.py` (no startup scheduler); `backend/app/models/__init__.py:13-27` (`PipelineRun` defined, unused).

**M2. Requirements unpinned + missing ML deps.** `backend/requirements.txt` uses `>=` (LangGraph drift risk flagged in previous audit) and omits the entire ML layer. Local interpreter is Python 3.13.5 while CI targets 3.11 — `datetime.utcnow` (used 10+ places in `backend/app/models/__init__.py`) emits DeprecationWarnings on 3.12+. Evidence: `backend/requirements.txt:1-12`; `python --version` → 3.13.5; `backend/app/models/__init__.py:17` and others.

**M3. Naive datetimes in timezone-aware columns.** `DateTime(timezone=True)` columns receive naive `datetime.utcnow()` defaults; comparing with aware `published_at` values (from connectors) via asyncpg can raise "can't subtract offset-naive and offset-aware" errors in real use. Evidence: `backend/app/models/__init__.py:17, 91, 111, 132, 173, ...`. Fix: `datetime.now(timezone.utc)` throughout.

**M4. Test suite is one self-validating script.** `tests/test_foundation.py` is a `print`-based script (run via `python` in CI, not pytest), asserts the stub providers "verified", and covers 0% of the DB models, health endpoints, dedup upsert, red-team, or fallback chain. There is no pytest config/`pyproject.toml`, no coverage, no failure-injection tests, no EV-1..EV-14 harnesses (classification ≥85%, source-link 100%, F-I-S labels, Q1–Q4 completeness). Evidence: `tests/test_foundation.py:43-64`; `.github/workflows/ci.yml:26-28`.

**M5. Domain config quality gate absent.** `config/haemophilia.yaml` loads but nothing validates `approval_status`/`approval_date`/`last_verified` per the §14.5 ontology quality gate, and there is no unit test enforcing the three verified mappings (fitusiran→Qfitlia, concizumab→Alhemo, marstacimab→Hympavzi). The test assertion `len(config.assets) >= 7` (`tests/test_foundation.py:25`) is brittle — it breaks on any unrelated YAML edit. Evidence: `backend/app/core/domain_config.py:60-78`; `tests/test_foundation.py:23-28`.

**M6. `ProviderFactory` instantiates all providers at import time.** `provider_factory = ProviderFactory()` runs module import (factory constructs Gemma/Grok/Degraded). Harmless today (stubs), but once Gemma actually loads weights it will block app startup and defeat lazy fallback. Evidence: `backend/app/providers/factory.py:49`. Recommend lazy singleton or async init in `lifespan`.

**M7. Freshness-class labelling errors.** `health.py:74-78` labels PubMed `near_real_time` but Master Plan §5 defines PubMed as `delayed`/`batch`; ClinicalTrials.gov should be `near_real_time` (correct in code) but PubMed is not. Evidence: `backend/app/api/v1/endpoints/health.py:74-78` vs `docs/METARADAR_MASTER_PLAN_v5.0.md` §5.

**M8. Grok provider details inconsistent with spec.** `grok-beta` is hardcoded (not configurable per §14.1 `GROK_MODEL`), no JSON-Schema structured outputs, no three-layer validation (§13.4), and `generate_summary` is mocked (`grok.py:42`). Evidence: `backend/app/providers/grok.py:23, 41-43`.

**M9. Signal-type values unvalidated / access signals missing.** `signal_type` is a free string in both schema and ORM — §3 canonical values (CONGRESS/PUBLICATION subtypes, §12.4 `ACCESS_*` types) are not enumerated or validated anywhere. Evidence: `backend/app/schemas/__init__.py:67`; `config/haemophilia.yaml:108-122` (no CONGRESS/ACCESS subtypes defined).

**M10. `upsert_signal` commits inside the helper.** `deduplication.py:82` calls `session.commit()` — a caller wrapping multiple signals in one transaction will get partial commits per row. Evidence: `backend/app/services/deduplication.py:52-83`. Fix: move commit responsibility to the caller/service boundary.

**M11. `docker-compose.yml` uses obsolete `version: "3.8"` key** (now informational in Compose v2; harmless but noisy) and healthchecks rely on `curl` inside backend images that don't exist yet (C3). Evidence: `docker-compose.yml:1, 57-61`.

**M12. Compiled `__pycache__` artifacts present in the tree** (cpython-313 for `app`, `db`, `api`, `providers`, `services`, `models`, `schemas`) — gitignored so untracked, but indicate dirty local runs and Python-3.13 execution mismatched with CI 3.11. Evidence: repo glob `backend/**/*` shows `__pycache__/*.pyc` entries.

**M13. Domain-config discovery is layout-relative.** `domain_config.py:67` computes `Path(__file__).resolve().parents[3]` → assumes repo-root/config layout; in Docker this silently resolves to `/app/config` only if the image mirrors the layout — unverifiable until a Dockerfile exists. Evidence: `backend/app/core/domain_config.py:65-68`.

### Low

**L1. `chunk_text_for_embedding` approximates tokens as `max_tokens * 4` characters** (`deduplication.py:45-49`) — crude heuristic; acceptable pre-embedding but should be replaced with the tokenizer's real `max_seq_length` once `sentence-transformers` lands.

**L2. Gemma `generate_summary` slices by characters (`gemma.py:29-30`), not tokens**, and ignores `MAX_OUTPUT_TOKENS` entirely.

**L3. `SignalSchema.version` fields duplicated as constants** (`5.1.0` in `config.py:16`, `schemas/__init__.py:111`) — single source (e.g., `importlib.metadata` or settings) recommended.

**L4. Health connector entries never carry `last_success`/`last_error`** — always None (`health.py:73-116`), so the "last success/error" honesty fields are decorative until real connectors exist.

**L5. No `.python-version`/`runtime.txt` pinning Python** — CI 3.11 vs local 3.13 drift (see M2).

## Resolved Concerns (note what was fixed, when)

- **No CI/CD pipeline (old CONCERNS.md, Resolved 2026-08-13):** `.github/workflows/ci.yml` now exists — installs backend deps, runs `tests/test_foundation.py`, and enforces `scripts/export_openapi.py` contract sync on push/PR to main/develop.
- **No automated test suite (partially resolved 2026-08-13):** `tests/test_foundation.py` added — covers domain-config loading, fingerprint/chunking, and the provider capability matrix (against mocks). Still no pytest harness, DB/API/fallback-injection tests (see M4).
- **Deployment target (partially resolved):** `docker-compose.yml` + seeded volumes (pgvector/pg16, redis:7, `/models` cache volume) added with healthchecks — but blocked by missing Dockerfiles (C3) and alembic scaffold (C4).
- **No runtime code → foundation skeleton (transformed):** the previous audit's "#1 concern" (docs-only repo) is now inverted — code exists but is uncommitted (C6), stubbed (C2/H3), and unwired (C1/H5). The risk moved from "nothing built" to "built things that claim more than they do."

## Trend Notes (how concerns have evolved)

- **Docs → code shift:** The 2026-08-13 pre-implementation audit found a docs-only repo (15 spec docs, ~14.6k lines, zero code). Since then a foundation has been scaffolded: FastAPI app, health endpoints, ORM models matching §14.2 entity design, one Alembic migration, dedup service, provider abstraction, minimal frontend page, CI. The delta between could-have (unimplemented pipeline) and what's claimed-by-README is now the dominant risk class.
- **Honesty risk replaced completeness risk:** Previously "nothing is implemented" was obvious. Now mocks return plausible-looking data (Gemma "reasoning", connector "active", quota "100/day") — which is more dangerous because it takes an active code review to detect. The §14.16 honest vocabulary is the guardrail being violated most.
- **Scaffolding gaps emerged:** Dockerfiles, alembic.ini/env.py, Next.js config, and git commits are all missing — "solve the boring plumbing first" items that block every demo path before any feature work matters.
- **Next expected move:** commit the foundation, add the two Dockerfiles + alembic scaffold so `docker compose up` + `alembic upgrade head` work, then build the first real end-to-end slice (Synthetic connector → validation/dedup → signal listing API → frontend list) before touching real providers or models.

---

*Concerns audit: 2026-08-13*