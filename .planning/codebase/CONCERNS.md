# Codebase Concerns

**Analysis Date:** 2026-08-13

## Tech Debt

**Docs-only repository — no implementation exists yet:**
- Issue: The repo contains 15 spec/research documents (14.6k lines) but zero source code. Everything is `[SOURCE-DERIVED]` / specified, nothing built.
- Files: [`README.md`](README.md), [`docs/`](docs/) (all)
- Impact: Implementation must start from scratch inside a 4-week hackathon window; every spec item is a potential scope risk
- Fix approach: Follow [`docs/8_CORRECTED_UNIFIED_PLAN.md`](docs/8_CORRECTED_UNIFIED_PLAN.md) roadmap (week 1: Docker Compose + FastAPI + Next.js + DB + connectors); lock MVP scope per [`docs/METARADAR_MASTER_PLAN_v5.0.md`](docs/METARADAR_MASTER_PLAN_v5.0.md) §3

**Document drift across the doc set:**
- Issue: Historical docs (SRS, SDD, UI design, Refined Architecture) partially disagree with the canonical master plan; some carry old decisions (e.g., summarizer model `sshleifer/distilbart-cnn-12-6` vs canonical `facebook/bart-large-cnn`; BART vs Gemma as reasoning LLM; `Veeva`-style industry references in doc 6).
- Files: [`docs/2_SRS_Software_Requirements_Specification.md`](docs/2_SRS_Software_Requirements_Specification.md), [`docs/3_SOFTWARE_DESIGN_DOCUMENT.md`](docs/3_SOFTWARE_DESIGN_DOCUMENT.md), [`docs/5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md`](docs/5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md), [`docs/6_NOVO_NORDISK_ANALYSIS_AND_HACKATHON_INTELLIGENCE.md`](docs/6_NOVO_NORDISK_ANALYSIS_AND_HACKATHON_INTELLIGENCE.md)
- Impact: Planner/executor may follow stale guidance (C5/C6 conflicts documented in [`docs/8_CORRECTED_UNIFIED_PLAN.md`](docs/8_CORRECTED_UNIFIED_PLAN.md) §5)
- Fix approach: Treat master plan as sole authority; apply the CUP resolution rule when docs disagree

**Research docs contain large volumes of legacy/contextual content:**
- Issue: `Ishaaq_research-1.md` (3,152 lines) mixes metabolic-disease (semaglutide) history with haemophilia content; doc 6 retains metabolic examples as "historical context"
- Impact: Reading time + risk of scope creep from outdated context
- Fix approach: Keep as reference; never pull requirements from research files — only from master plan/SRS

## Known Bugs

**None** — no runtime code exists yet. (Anticipated bug classes are catalogued in the risk register, see Security/Resilience below.)

## Security Considerations

**PII / confidential-data leak (R14) — HIGHEST PRIORITY:**
- Risk: Scraped content containing patient names/case data entering the pipeline
- Files: ingestion connectors (planned in `backend/app/agents/`), [`docs/9_RISK_AND_GUARDRAILS.md`](docs/9_RISK_AND_GUARDRAILS.md) R14
- Current mitigation: prescribed **dedicated PII/PHI detection + redaction layer** before persistence (spaCy NER contributes to entity detection; it is not claimed as a guaranteed scrubber), redaction `[REDACTED:LABEL]`, reject/quarantine on low detection confidence, public/synthetic source whitelist, EV-4 audit target = 0 (evaluation target, not a mathematical guarantee)
- Recommendations: `.env` must stay gitignored; run secret scan before any commit

**Secrets in repo:**
- Risk: `README.md` documents real-looking example values (`postgresql://metauser:metapass@...`, `NEWSAPI_KEY=your_newsapi_key`) and SDD shows `DATABASE_URL=postgresql://user:pass@postgres:5432/metaradar` / `NEWSAPI_KEY=xxx`
- Files: [`README.md`](README.md) §Configuration, [`docs/3_SOFTWARE_DESIGN_DOCUMENT.md`](docs/3_SOFTWARE_DESIGN_DOCUMENT.md) (docker-compose env block)
- Current mitigation: these are placeholders, not live credentials; never commit a real `.env`
- Recommendations: keep `.env.example` as the only committed env template (SRS NFR line ~553)

**External-LLM privacy gate (hosted reasoning, R28):**
- Risk: if `LLM_PROVIDER=xai|auto` is enabled, only public/synthetic prototype data may be sent to Grok; xAI retains requests/responses ~30 days (encrypted, abuse auditing) and does not train without explicit permission
- Files: [`docs/METARADAR_MASTER_PLAN_v5.0.md`](docs/METARADAR_MASTER_PLAN_v5.0.md) §13.5, [`docs/9_RISK_AND_GUARDRAILS.md`](docs/9_RISK_AND_GUARDRAILS.md) R28
- Current mitigation (prescribed): mandatory gate (public/synthetic → PII/PHI → confidentiality → ALLOW/BLOCK) before any external call; blocked → local Gemma → BART degraded → source-only; EV-20 acceptance scenarios
- Recommendations: default `LLM_PROVIDER=local`; never enable hosted mode without the gate implemented and tested

**Prompt/ontology drift (R15):**
- Risk: manual ontology edits or prompt changes silently degrade classification (known error class: fitusiran/Alhemo confusion)
- Mitigation prescribed: ontology versioning (`updated_by`), regression tests on evaluation set, change log in WORM `audit_log`

## Performance Bottlenecks

**Local CPU model inference:**
- Problem: Gemma 3 4B (Q4, **estimated** ~2.6 GB weights / ~4.5–7.5 GB RAM — estimates, not guaranteed; actual use depends on runtime, quantization, context length, config) is the slowest link on constrained hardware
- Files: [`docs/2_SRS_Software_Requirements_Specification.md`](docs/2_SRS_Software_Requirements_Specification.md), `docs/9_RISK_AND_GUARDRAILS.md` R6
- Cause: CPU-bound transformer inference + quantization trade-offs
- Improvement path: BART fallback for batch summarization (< 60s/100 signals); lighter Gemma 3 1B option; cache hot signals (Redis 2h TTL)

**Dashboard latency target < 500 ms:**
- Problem: cached views must render fast while AI workflows run async
- Cause: heavy synthesis on request path would blow the budget
- Improvement path: serve cached results; run intelligence async via Celery; verify with load test (1000 signals, CUP §11)

## Fragile Areas

**Relevance-based routing + calibration (R10/R12/R16):**
- Files: [`docs/9_RISK_AND_GUARDRAILS.md`](docs/9_RISK_AND_GUARDRAILS.md) R10/R12/R16
- Why fragile: sparse feedback can overfit to one persona; weight-drift unmonitored; seed matrix is B.Pharm opinion, not data
- Safe modification: minimum feedback threshold before recalibration, damped updates, WORM history, per-function agreement metrics

**Congress/publication linking (R17):**
- Files: [`docs/METARADAR_MASTER_PLAN_v5.0.md`](docs/METARADAR_MASTER_PLAN_v5.0.md) §6, R17
- Why fragile: same drug different trial, press-wire noise, `development_id` match errors
- Safe modification: `link_decision` audit field, subtype classification, human-review flag on ambiguous links
- Test coverage: prescribed EV-9/AC-15 control scenarios (not yet written)

**Missing-signal WATCH false expectations (R8/R18):**
- Why fragile: silence is ambiguous (delayed disclosure, coverage gaps, changed strategy)
- Safe modification: guarded wording only ("Watch for…" / "Not observed yet"), confidence-by-silence cap, human review on expiry

## Scaling Limits

**NewsAPI quota (Developer/free tier):**
- Current capacity: **100 requests/day** (Developer plan; development/testing use only, NOT production/internal deployment — per https://newsapi.org/pricing)
- Limit: hard ceiling for live news ingestion; Developer articles carry up to a 24-hour delay (never described as real-time)
- Scaling path: quota-aware connector; on exhaustion fall back Redis 2h-TTL cache → bronze DB → 500-signal synthetic dataset; adapter-ready sources (FDA/EMA/congress/Reddit) are scaffolded but not fully live

**Local model capability envelope:**
- Current capacity: 4B-parameter reasoning on CPU
- Limit: reasoning depth vs commercial LLMs
- Scaling path: model-agnostic `LOCAL_LLM_MODEL` swap (Mistral 7B, Phi-3 Mini, etc. documented in [`docs/1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md`](docs/1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md)); optional hosted Grok (`LLM_PROVIDER=xai|auto`) for higher-quality reasoning when an external provider is acceptable (privacy-gated, Master Plan §13)

## Dependencies at Risk

**HuggingFace model downloads at demo time:**
- Risk: Gemma 3 4B / BART / MNLI / spaCy models must download before offline demo; failure blocks pipeline
- Impact: demo failure if network is unavailable and models uncached
- Migration plan: pre-download models into Docker image/volume; BART as fallback is smaller and CPU-fast

**Optional hosted Grok dependency (xAI API, R29):**
- Risk: Grok outage/key expiry/quota/latency/invalid responses affect reasoning when hosted mode is enabled
- Impact: reasoning quality degrades, not the data pipeline — Grok is never a data source
- Migration plan: `LLM_PROVIDER=local` default keeps the demo fully offline-capable; provider chain Gemma → Grok → BART degraded (EV-19); privacy gate (EV-20)

**LangGraph version drift:**
- Risk: "LangGraph 0.1+" pinned loosely; graph API changes
- Impact: node implementations break on upgrade
- Migration plan: pin versions in `requirements.txt` at implementation time

## Missing Critical Features

**No CI/CD pipeline:**
- Problem: Gap Analysis prescribes unit tests + 0-bug gate in CI; nothing exists (`docs/1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md` G10 area)
- Blocks: regression safety during 4-week build

**No automated test suite (yet):**
- Problem: all test strategy is prescriptive (see `TESTING.md`); EV-1..EV-14 acceptance checks unwritten
- Blocks: five hackathon success metrics cannot be demonstrated

**No deployment target beyond local Docker:**
- Problem: demo-day deployment plan is "docker compose up on clean machine" only
- Blocks: judge-machine reproducibility if Docker unavailable

## Test Coverage Gaps

**Classification metric harness (EV-2/EV-13):**
- What's not tested: ≥85% classification accuracy claim (disease · patient type · signal type · priority · impacted function) with confusion matrix
- Files: `docs/2_SRS_Software_Requirements_Specification.md`, `docs/8_CORRECTED_UNIFIED_PLAN.md` §10
- Risk: the core judged metric is unverifiable until the B.Pharm-labelled dataset + harness exist
- Priority: High

**Resilience/fallback tests (planned, not yet run):**
- What's not tested (to be verified by failure-injection tests): API 429/500 → cache/bronze/synthetic cascade; network-off demo mode; Gemma-unavailable → BART factual-summarization degraded mode; dedicated PII/PHI detection + redaction layer unit tests
- Files: `docs/8_CORRECTED_UNIFIED_PLAN.md` §11
- Risk: demo-day failure from unexercised fallbacks
- Priority: High

**Calibration drift monitoring:**
- What's not tested: weight-drift, per-persona feedback counts, before/after routing agreement (EV-6)
- Risk: calibration overfit claims undemonstrated
- Priority: Medium

---

*Concerns audit: 2026-08-13*
