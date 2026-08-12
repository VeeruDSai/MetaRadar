# MetaRadar: Pre-Implementation Architecture-Hardening Report (v5.1)

**Project:** MetaRadar — Near-Real-Time Competitive Intelligence Radar (Haemophilia within Rare Disease)
**Team:** Aura Pharmers — MSRIT (2 CSE + 3 B.Pharm) · **Team Lead: Sanjana Rathore B.**
**Date:** August 13, 2026
**Type:** Final architecture-hardening & scalability pass over the ENTIRE project plan and documentation set — **NOT a redesign**.
**Canonical source of all decisions:** [`METARADAR_MASTER_PLAN_v5.0.md`](METARADAR_MASTER_PLAN_v5.0.md) §14 (v5.1).
**Status of the repository:** documentation-only (specification-first). Every feature is **SPECIFIED** — nothing is claimed `IMPLEMENTED`/`TESTED`/`VERIFIED` (status vocabulary, Master Plan §14.16).

---

## 1. FILES CHANGED

| File | Change |
|---|---|
| `docs/METARADAR_MASTER_PLAN_v5.0.md` | Canonical spec bumped to **v5.1** — new §14 (14.0–14.17) hardening section; GPU deployment; single-scheduler decision; team identity; LangGraph state contract + explicit `node_calibrate → END`; connector interface; dedup/source-independence; health/CORS; versioned caching/scoring/calibration; observability/idempotency; evaluation/calibration data; migrations/indexing/Docker `/models`; frontend contract; status vocabulary |
| `docs/2_SRS_Software_Requirements_Specification.md` | v2.3 note; FR-2.1.3 rewritten (deterministic dedup) + FR-2.1.3A (source independence) + FR-2.1.5 (canonical entity model); new §2.9 FR-2.9.1–2.9.5 (scoring versioning · calibration versioning · health & observability · single scheduler · migrations & cache integrity); GPU deployment; env vars `LLM_DEVICE`/`LLM_DTYPE`/`MAX_CONTEXT_TOKENS`/`MAX_OUTPUT_TOKENS`; 4 health endpoints; schema entity-layer tables + `evidence`; fitusiran→Qfitlia glossary correction |
| `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` | **v2.4** — GPU stack entry; APScheduler-only (Celery removed); 4-service Docker Compose + `/models` volume + healthchecks; entity-layer SQL (`sources · companies · assets · trials · developments · events · evidence`); `scoring_model_version`/`scoring_config_version`/`score_breakdown` on `signals`; baseline-vs-calibrated + `calibration_version` on `signal_routing`/`calibration_history`; LangGraph state reducer contract + `set_finish_point`; health endpoints; Gemma-VRAM failure row; team line |
| `README.md` | Stack table (GPU Gemma, single APScheduler); env block (LLM device/dtype/context vars); reasoning-limitations GPU wording; team lead line |
| `CLAUDE.md` | Reasoning layer → local GPU; scheduler consolidated to APScheduler (Celery removed) |
| `.planning/codebase/STACK.md` | Scheduler section → single APScheduler; Gemma GPU + memory-budget wording; key vars |
| `.planning/codebase/ARCHITECTURE.md` | Diagram + scheduler entry → APScheduler-only; threading/GPU constraint wording |
| `.planning/codebase/STRUCTURE.md` | `workers/` described as APScheduler jobs (Celery removed) |
| `.planning/codebase/CONCERNS.md` | Performance bottleneck → GPU framing; Celery references replaced |
| `.planning/codebase/INTEGRATIONS.md` | Scheduler reference; Gemma GPU env vars |
| `docs/1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md` | NewsAPI 500→**100/day** (2 places incl. rate-limiter config); compose celery service removed + `/models` volume; memory estimates reframed to GPU VRAM; feasibility "no GPU" corrected; `LLM_DEVICE`-driven loader |
| `docs/5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md` | `google/gemma-2b` → `google/gemma-3-4b-it` (GPU); Celery references → APScheduler; 5→4 Docker services |
| `docs/7_PITCH_AND_PRESENTATION_NARRATIVE.md` | Celery references → single APScheduler; "CPU-executable models" → GPU/CPU split (Q16); scaling answer updated |
| `docs/6_NOVO_NORDISK_ANALYSIS_AND_HACKATHON_INTELLIGENCE.md` | Celery references → APScheduler; CPU → GPU (Q16); fitusiran approved-2023 → Qfitlia March 2025 |
| `docs/8_CORRECTED_UNIFIED_PLAN.md` | **v1.5** change note; team lead; remaining Celery references removed; NewsAPI tier text corrected; footer bumped |
| `docs/9_RISK_AND_GUARDRAILS.md` | **v1.3** — R6 updated (small-GPU); new **R30** (Gemma cannot fit/initialize on 4 GB VRAM → never-crash fallback); team lead footer |
| `docs/4_UI_DESIGN_DOCUMENT.md` | **v3.4** — canonical component contract + mapping table; source-freshness badges; health footer behavior; `ProviderBadge` → "Gemma · local GPU" |

---

## 2. ARCHITECTURE CHANGES

| # | Decision | Classification |
|---|---|---|
| A1 | **One scheduler: in-process APScheduler + Redis; Celery removed.** Rationale documented (Master Plan §14.9): jobs are lightweight; two schedulers = duplicate paths + unnecessary infra on a 4 GB VRAM laptop. Reintroduction path documented (additive, not a rewrite). | **HIGH** (removes duplicate scheduling paths; simplifies Docker to 4 services) |
| A2 | **Formal LangGraph state contract**: explicit state fields, initial state, typed reducers for accumulating fields (raw_signals/validated_signals/evidence/errors under parallel connectors), replacement semantics for scalars, node read/write ownership, **explicit `node_calibrate → END`**, recursion/failure limits. No uninitialized `state["signals"].append(...)`. | **HIGH** (prevents subtle parallel-state corruption; guarantees termination) |
| A3 | **Canonical entity model** — stable IDs (`signal_id · source_id · company_id · asset_id · trial_id · development_id · event_id · publication_id · congress_event_id · regulatory_event_id · access_event_id`); `Signal → Development → Asset → Company` and `Development → Trial → Congress → Publication → Regulatory → Access → Post-market`; one development accumulates many signals; immutable source provenance; canonical nullable Signal schema; explicit evidence relationships. | **CRITICAL** (foundation for Confluence/Lifecycle; expensive to retrofit) |
| A4 | **One `SourceConnector` interface** returning normalized `RawSignal` (PubMed/NewsAPI/ClinicalTrials/FDA/EMA/Congress/Reddit/Synthetic adapters); adding a source never rewrites `node_ingest`; freshness classes per connector (real_time/near_real_time/delayed/batch/adapter_ready/synthetic). | **HIGH** (scalability + honest freshness) |
| A5 | **Deterministic deduplication + source-independence model BEFORE Confluence** (fingerprints: PMID/NCT/FDA/congress IDs, else normalized title+publisher+date+company+asset+URL; `source_class/publisher/syndication_group/parent_source_id`). Confluence counts independent evidence, not articles. | **HIGH** (fixes duplicate/syndication inflation) |
| A6 | **Domain configuration layer** (`config/haemophilia.yaml`) — core engine is therapy-area agnostic (Haemophilia → other Rare Diseases → multiple TAs without touching DB, API, LangGraph, provider layer, or frontend). | **HIGH** (the primary scalability mechanism) |
| A7 | **Versioned operational surface**: `/api/v1/*` only; `/api/v1/health/ready|models|connectors`; configurable `CORS_ORIGINS`; Alembic migrations; versioned Redis cache keys + invalidation; versioned scoring/calibration (baseline preserved); prompt versioning; observability (`run_id`/`signal_id`/`model_request_id`); idempotency. | **HIGH** (prevents API/DB/cache breakage after implementation) |
| A8 | Final canonical pipeline flow re-confirmed (§14.17) — no additional pipeline. Ten nodes, five mechanisms, six functions, calibration loop, Ask Athena, provider abstraction all retained. | — (no change; verified) |

## 3. DATABASE CHANGES

- New entity-layer tables (SDD §2.5, SRS §4.3): `sources` (freshness_class, syndication_group, parent_source_id) · `companies` · `assets` (ontology quality-gate fields) · `trials` · `developments` · `events` (publication/congress/regulatory/access event IDs) · `evidence` (claim→evidence relationships, raw_content_hash, content_version).
- `signals` gains `scoring_model_version` · `scoring_config_version` · `score_breakdown`.
- `signal_routing` gains `baseline_primary_function` · `baseline_relevance_scores` · `baseline_suggested_action` · `calibration_version` · `feedback_id` (baseline never overwritten).
- `calibration_history` gains `calibration_version`.
- **Alembic migrations** replace `drop_all()/create_all()`; first migration anticipates all tables. **Indexing plan** for frequent queries (signal_id, development_id, company_id, asset_id, trial_id, published_at, retrieved_at, signal_type, primary_function, priority, evidence_maturity); vector indexes only where semantic search requires them. | **HIGH**

## 4. SCALABILITY CHANGES

- Engine is therapy-area agnostic (domain config, not hard-coded haemophilia). | **HIGH**
- `SourceConnector` interface → new data sources are additive adapters. | **HIGH**
- Entity model → multiple signals per development without duplication; stable identifiers support cross-source linking at scale. | **HIGH**
- Single-scheduler decision + documented reintroduction path (Celery) when throughput exceeds ~1,000 signals/cycle. | **MEDIUM**
- Reusable frontend component contract (canonical names) — no per-signal-type one-offs. | **MEDIUM**

## 5. AI / MODEL CHANGES

- **Gemma 3 4B Instruct Q4/int4 — local GPU (NVIDIA RTX 3050, 4 GB VRAM)** replaces all "Gemma — CPU" claims. | **CRITICAL**
- **4 GB VRAM is not assumed to guarantee inference.** Weights (~2.6 GB Q4), KV cache, runtime overhead, and context length budgeted separately; configurable `LLM_DEVICE` · `LLM_DTYPE` · `MAX_CONTEXT_TOKENS` · `MAX_OUTPUT_TOKENS`. | **HIGH**
- **Never-crash fallback chain:** GPU init/inference failure → Grok (if configured & privacy-gated) → BART degraded factual → source-grounded factual signal + human-review flag. No GPU logic in LangGraph nodes (provider abstraction owns execution). | **CRITICAL**
- Two output schemas preserved (FULL INTELLIGENCE vs DEGRADED FACTUAL SUMMARY); BART never reasoning-equivalent; model metadata on every output; Grok structured-output + semantic validation; external-LLM privacy gate unchanged. | — (already v5.0; verified + re-stated)
- New risk **R30** (VRAM/model-fit failure) added to the register. | **HIGH**

## 6. SOURCE / CONNECTIVITY CHANGES

- NewsAPI quota corrected from "500/day" to **100/day** (Developer/free tier, dev/testing only, 24h article delay) in the one remaining stale location (Gap Analysis rate-limiter + summary); quota-aware batching + cache; no accidental quota burn in dev loops. | **HIGH**
- All connectors behind the shared `SourceConnector` interface with normalized `RawSignal` + freshness classes. | **HIGH**
- A failed optional source never makes the whole application report dead (`/api/v1/health/connectors` per-source reporting). | **HIGH**

## 7. RELIABILITY CHANGES

- Single scheduler (no duplicate scheduling paths). | **HIGH**
- Healthchecks (`pg_isready`, `redis-cli ping`, `/health/ready`) complement `depends_on`. | **HIGH**
- Idempotency keys / stable external IDs (no duplicate signals, feedback, or lifecycle events on re-run). | **HIGH**
- Redis: canonical JSON serialization (datetime/UUID/Decimal/Enum/Pydantic), versioned keys (`signal:{id}:v1`), TTL + schema version + source timestamp + model/config version; stale intelligence never silently served after scoring/calibration changes. | **HIGH**
- Per-node error boundaries; one source/node failure never kills the pipeline. | — (verified; already specified)
- `/models` volume: app starts without re-downloading GB of weights; model weights not baked into the app image. | **MEDIUM**

## 8. SECURITY / PRIVACY CHANGES

- `CORS_ORIGINS` environment allowlist (never hard-coded `"*"`). | **MEDIUM**
- No secrets in code / browser code; all config env-driven (incl. new model vars). | — (verified)
- External-LLM privacy gate, PII/PHI redaction layer, public/synthetic-only rule, WORM `audit_log` (no 21 CFR Part 11 claim) — unchanged and re-verified consistent across all docs. | — (verified)
- Observability: no confidential or patient data ever logged (`run_id`/`signal_id`/`model_request_id` only). | **MEDIUM**

## 9. DOMAIN / ONTOLOGY CORRECTIONS

- **Verified FDA mappings locked** (Master Plan §14.5): **fitusiran → Qfitlia** (FDA Mar 2025) · **concizumab → Alhemo** (FDA Dec 2024) · **marstacimab → Hympavzi** (2024; Jun 2026 expansion to 6+). Not swapped anywhere. | **HIGH**
- Ontology quality gate fields (`generic_name · brand_name · company · mechanism · disease · factor · inhibitor_population · approval_status · approval_date · jurisdiction · source · last_verified`); approval tracked as an updateable fact, not static. | **HIGH**
- Stale "fitusiran approved 2023" corrected to Qfitlia March 2025 (SRS glossary, Doc 6). Roctavian (June 2023) and concizumab (EU Feb 2023 / FDA Dec 2024 / US expansion Jul 2025) statuses verified consistent with research docs. | **MEDIUM**
- Historical gap records (G15/G16/C8: "fitusiran ≠ Alhemo") retained as historical QA documentation — they describe the error class, not current ontology state. | — (intentional)

## 10. DOCUMENTATION CORRECTIONS (repository-wide consistency audit)

All stale occurrences corrected per Master Plan §14: Gemma "CPU" → GPU; Celery removed from every doc; NewsAPI 500/day → 100/day; `google/gemma-2b` → `google/gemma-3-4b-it`; missing END node → explicit; unversioned APIs → `/api/v1`; hard-coded model names → env-config; absolute resilience claims → acceptance targets; unversioned scoring/calibration → versioned; direct frontend/DB coupling → Pydantic contract; missing migrations/health/CORS → specified; duplicate schedulers → one; missing dedup/development_id/evidence relationships → specified. Team identity (Aura Pharmers · Sanjana Rathore B.) consistent in Master Plan, README, SDD, 8_UNIFIED, 9_RISK. Implementation status honest (**SPECIFIED** everywhere — docs-only repo).

## 11. TESTS ADDED / REQUIRED (all PLANNED — nothing exists yet)

- **Required (planned in TESTING.md/8_UNIFIED):** provider-chain failure-injection tests incl. **Gemma GPU init/VRAM failure** → Grok → BART degraded → source-only (EV-19 extension); NewsAPI quota-exhaustion tests at 100/day; dedup fingerprint tests (PMID/NCT/syndication); source-independence tests (3 sites reproducing one release ≠ 3 signals); LangGraph state reducer/concurrency tests (parallel connectors); `node_calibrate → END` termination test; scoring/calibration versioning tests (baseline preserved; BEFORE→feedback→AFTER); health-endpoint tests (`/health`, `/ready`, `/models`, `/connectors`); Redis serialization/cache-key-version tests; idempotency tests (re-run pipeline/feedback); migrations test (Alembic upgrade/downgrade); ontology quality-gate tests (Qfitlia/Alhemo/Hympavzi mappings as must-not-regress); ground-truthed evaluation dataset with the §14.13 ground-truth fields for ≥85% classification.
- No test code exists in the repository; everything above is **PLANNED**.

## 12. REMAINING RISKS (unresolved — not hidden)

| Risk | Severity | Notes |
|---|---|---|
| R30 — Gemma may not fit/execute on 4 GB VRAM in practice (esp. with long context) | **HIGH** | Mitigated by configurable budgets + never-crash chain, but the actual device must be validated on the demo machine before rehearsal; Grok fallback requires a key + privacy gate approval. |
| Celery removal means jobs do not survive backend restarts and runs are in-process | **MEDIUM** | Acceptable for a 4-week demo; documented reintroduction path exists. Re-verify with the 1000-signal load test. |
| BART degraded mode quality floor | **MEDIUM** | Factual summaries only — acceptable demo degradation; not reasoning-equivalent. |
| NewsAPI 100/day quota can still be consumed by demo-day live refreshes | **MEDIUM** | Quota-aware connector + caching specified; enforce in Phase 1 acceptance. |
| SDD/8_UNIFIED still carry historical gap/decision records that name Celery, CPU, and 500/day as *historical context* | **LOW** | Intentional — they document resolved contradictions; the canonical Master Plan §14 governs. |
| Research docs (Ishaaq/Sanjana/Usha) contain legacy/metabolic content and some product facts that predate Qfitlia/Hympavzi naming | **LOW** | Research files are domain reference only; never source requirements; ontology QA layer gates product facts. |
| No implementation exists; all hardening is on paper | **HIGH** | Every acceptance target (fallback chain, ≥85% classification, health, migrations) must be demonstrated during Weeks 1–4 per 8_UNIFIED Phase 0–10. |

---

**FINAL PRINCIPLE (unchanged):** Build the current Haemophilia pilot on a therapy-area-agnostic engine — evolving from Haemophilia → another Rare Disease → multiple Rare Disease therapy areas without rewriting the database, API contracts, LangGraph architecture, provider layer, or frontend foundation. Only domain configuration should require substantial modification.

*Architecture-Hardening Report · August 13, 2026 · MetaRadar v5.1 · Team: Aura Pharmers (MSRIT) · Team Lead: Sanjana Rathore B.*
