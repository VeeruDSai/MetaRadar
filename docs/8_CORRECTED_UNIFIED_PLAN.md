# MetaRadar — Corrected Unified Plan (Audit-Closed Specification)

**Project:** MetaRadar — Near-Real-Time Haemophilia Competitive Intelligence Radar
**Document:** v1.5 — Corrected Unified Plan (secondary working reference aligned to the canonical Master Plan — METARADAR_MASTER_PLAN_v5.1.md — which remains the sole authority)
**Date:** August 12, 2026 (post-kickoff)
**Target Event:** Novo Nordisk GBS Hackathon 2026 — Problem Statement #3 "From Inbox Noise to Strategic Signal" | Pilot: Haemophilia within Rare Disease
**Team:** MSRIT — Aura Pharmers (2 CSE + 3 B.Pharm) · **Team Lead: Sanjana Rathore B.**
**Method:** Audit of the MetaRadar master plan (then v3.0 — now METARADAR_MASTER_PLAN_v5.0.md), SRS v2.0, SDD v2.1, UI Design v2.1, Refined Architecture v2.1, Novo Nordisk/Hackathon Intelligence v2.1, Pitch Narrative v3.0, Gap Analysis, and README against the 20-point correction brief. Web research used only to validate industry practice, never to expand scope.

> **v1.1 (newest kickoff, Aug 12, 2026):** Aligned to the latest Novo Nordisk kickoff — six primary functions (Medical Affairs, Regulatory, Safety/Pharmacovigilance, Market Access, Medical Communications, Leadership; Commercial & R&D retained as extended roles), the expanded canonical signal schema, mandatory Fact/Interpretation/Speculation labeling, the evidence-sufficiency gate, the controlled action vocabulary, and named B.Pharm owners. Supersedes v1.0 function lists.

---

> **CANONICAL PRINCIPLE (unchanged):** *"A conventional AI system summarizes documents. MetaRadar builds an evidence story around a development."*
>
> **CORRECTED PRINCIPLE (this plan):** ONE intelligence engine → ONE normalized signal → ONE evidence graph → ONE explainable prioritization layer → SIX primary function interpretations (+ extended Commercial/R&D). Five intelligence mechanisms feed one decision interface. No feature added in this plan exists to impress judges; every addition exists to close a measured gap against the hackathon rubric.
>
> **v1.2 (latest stakeholder brief, Aug 12, 2026):** Adds relevance-based routing ("not every signal goes to everyone" — primary/secondary functions + routing_reason), Congress and Publication as first-class signal types with subtypes linked to development lifecycles (NEW EVIDENCE vs NEW DEVELOPMENT), stakeholder-defined Watch-for-Next rules extending Missing-Signal, role-aware actions, the 6 kickoff demo cases, and the updated architecture flow. Supersedes v1.1 function lists and adds MR-ROUTE-1 / MR-CGR-1/2 / MR-PUB-1 / MR-WATCH-2 / MR-ACT-2.

> **v1.3 (Aug 13, 2026 — B.Pharm research integration):** Integrates the three B.Pharm research reports (Sanjana · Ishaaq · Usha) as domain rules per Master Plan v4.0 §12 — canonical domain classification (disease/factor/inhibitor/population/modality, never-guess-unknown), nullable clinical-evidence fields, evidence-maturity ladder, access as a separate intelligence event (8 access subtypes), the 19 Red-Team evidence checks (A–S), research-informed routing rules re-mapped into the six primary functions (student tables are domain reference only), Watch-for-Next, triage priority model, and 7 deterministic evaluation cases (EV-15..18). Architecture unchanged; the six primary functions remain Medical Affairs · Regulatory · Safety/PV · Market Access · Medical Communications · Leadership (Commercial/R&D/CI/Strategy = extended stakeholders only).
> **v1.4 (Aug 13, 2026 — provider-agnostic reasoning layer):** Per Master Plan v5.0 §13 — the reasoning layer becomes provider-agnostic: default local Gemma 3 4B (`LLM_PROVIDER=local`), optional hosted xAI Grok (`LLM_PROVIDER=xai|auto`) behind a mandatory external-LLM privacy gate, BART degraded factual mode only (never reasoning-equivalent). Adds EV-19/EV-20 (provider fallback chain, external-LLM privacy gate), SRS FR-2.2.3C–G tasking in Phase 2, and provider failure-injection scenarios in Phase 9. Architecture, ten nodes, five mechanisms, six primary functions unchanged.
> **v1.5 (Aug 13, 2026 — pre-implementation hardening, Master Plan v5.1 §14):** Gemma deployment corrected to **local GPU (NVIDIA RTX 3050, 4 GB VRAM, Q4/int4)** with `LLM_DEVICE`/`LLM_DTYPE`/`MAX_CONTEXT_TOKENS`/`MAX_OUTPUT_TOKENS` (VRAM never assumed to guarantee inference; never-crash fallback chain incl. source-grounded + human-review flag). **Scheduling consolidated to ONE in-process APScheduler — Celery removed** (Phase 1 compose becomes 4 services). Canonical entity layer (sources/companies/assets/trials/developments/events/evidence) + deterministic dedup + source independence before Confluence; LangGraph state contract (reducers, initial state, `node_calibrate → END`); versioned scoring/calibration (baseline preserved); health endpoints `/api/v1/health/ready|models|connectors`; configurable CORS; Alembic migrations; versioned Redis caching; `/models` volume; status vocabulary PLANNED/SPECIFIED/IMPLEMENTED/TESTED/VERIFIED. Ten nodes, five mechanisms, six functions unchanged.

**Labeling convention used throughout:**

| Label | Meaning |
|---|---|
| **[SOURCE-DERIVED]** | Requirement taken verbatim from the hackathon problem statement, kickoff scope, or existing project docs (SRS/SDD). |
| **[WEB-VERIFIED]** | Industry practice validated by current (2024–2026) research: pharma CI platforms now connect pipeline/clinical/regulatory/market signals to named decisions (Clarivate, Pienomial, 2026); evidence traceability and inline citations are non-negotiable for audit-ready intelligence; FDA draft AI-in-drug-development guidance and EMA AI principles mandate human-in-the-loop review and model credibility; RAG strictly bounded to verified documents is the standard hallucination mitigation (IntuitionLabs 2026, Nature/FDA summaries). Used as validation, not scope inflation. |
| **[ARCHITECTURAL]** | Engineering recommendation made by this plan to close a gap within the existing architecture. |

---

# 1. EXECUTIVE GAP ANALYSIS

Every material gap found in the current documentation, classified by severity. "Fixed in" refers to sections of this document.

| # | Gap | Documents affected | Severity | Required change | Fixed in |
|---|---|---|---|---|---|
| G1 | Product is described as a **Medical-Affairs-only MVP** ("One Role", "everything else Phase 2") while SRS/UI/Pitch already define five roles. Role scope must be **one engine → five role interpretations**, not five engines and not one role. | Master Plan §2/§3, README (MVP Scope, Roadmap), Doc 1 Week 1 | **CRITICAL** | Update scope language; keep single engine; make role routing (Q3) first-class for all 5 roles from day 1; demo leads with Medical Affairs but shows all five. | §3 (MR-ROLE-1), §4, §7, §10 |
| G2 | Data sources locked to **2 live** (PubMed + NewsAPI) while SRS already requires ≥3 live (AC-1) and lists 7 sources. Must demonstrate **≥3 genuinely live public sources** and explicitly label LIVE / ADAPTER-READY / SYNTHETIC-DEMO. No pretending all sources are production-integrated. | Master Plan §3/§5, README, SDD §1.1/§3.1 (6 fetchers incl. Twitter), SRS FR-2.1.1/AC-1 | **CRITICAL** | Add ClinicalTrials.gov as 3rd core live source; demote FDA/EMA/congress/Reddit to adapter-ready; remove Twitter; keep 500-signal synthetic demo. | §3 (MR-SRC-1/2/3), §5 |
| G3 | **No business/user-level success metrics.** All validation targets are technical latency numbers (Master Plan §10). Missing: source-linked summaries (100%), classification ≥85% with precision/recall/confusion matrix, top-signal discovery time ≤5 min, zero confidential/patient data, calibration agreement pre-vs-post. | Master Plan §10, SRS §6 (partial: AC-3 exists), README Validation | **CRITICAL** | Add metric A–E with reproducible test protocols and acceptance thresholds. | §3 (MR-EVAL-1..6), §9 |
| G4 | **No Four-Question completeness test.** Nothing asserts that 100% of high-priority cards contain Q1–Q4 + evidence + confidence + source + timestamp. | SRS AC-4 (render-only), UI doc | **CRITICAL** | Define completeness acceptance test (100%) with an automated checker. | §3 (MR-Q-1), §8, §9 |
| G5 | **No curated, deterministic evaluation dataset.** The 500-signal synthetic fallback is a demo feed, not a labelled test set. Missing: 20–30 classification examples + 5 confluence + 5 lifecycle + 5 contradiction + 5 missing-signal + 5 calibration scenarios with ground truth. | Master Plan §5, SRS §6, Doc 1 | **CRITICAL** | Create `data/evaluation/` curated dataset with expected outputs; every mechanism demo must point to "this scenario deliberately tests this mechanism." | §3 (MR-EVAL-2), §9 |
| G6 | **Weekly Intelligence Digest absent.** System is dashboard-only; a role-filtered weekly digest (Medical Affairs / Regulatory / Market Access / Commercial / R&D) must reuse the same engine, not a second pipeline. | All docs (only per-entity "briefs" exist) | **HIGH** | Add digest generation service + endpoint + UI, built on existing synthesis/brief agents. | §3 (MR-DIGEST-1), §6, §8, §11 P7 |
| G7 | **Priority scores are unexplained** ("Priority: 91/100 — WHY?"). No factor-level breakdown of what drove priority. | UI doc (relevance bars only), Master Plan §7 | **HIGH** | Add explainable priority decomposition (✓/✗ factor checklist + contribution weights + confidence rationale). | §3 (MR-EXP-1), §6, §8 |
| G8 | **Ask Athena behaves like a generic chatbot.** No required answer schema (Answer / Evidence / Sources / Confidence / Entities / Lifecycle / Contradicting evidence / Insufficient-evidence guard). | SDD §2.6 query_engine, UI §3.3 | **HIGH** | Define and enforce grounded structured answer schema + hallucination guardrail. | §3 (MR-ATHENA-1), §6, §8 |
| G9 | **Temporal / change intelligence under-specified.** Velocity/trend columns exist in schema (`velocity_score`, `trending_scores`) but no simple explainable temporal model (before/after deltas, velocity, acceleration, trajectory). | SDD §2.5, Doc 1 Opt-14, Doc 5 Upgrade 4 | **HIGH** | Add deterministic, explainable temporal layer: current state vs what changed, 7d velocity, acceleration flag, stage matching (B.Pharm rules). No predictive ML. | §3 (MR-TEMP-1), §6 |
| G10 | **No watchlist / entity-focus feature.** Users cannot focus on one drug/company/trial and see everything (signals, lifecycle, confluence, contradictions, missing signals, trend, role relevance, actions, evidence). | UI doc (entity filter exists), SRS §2.4.3 | **HIGH** | Add watchlist (persisted) + entity watch view that reuses entity + lifecycle + mechanism infrastructure. | §3 (MR-WATCH-1), §8, §11 P7 |
| G11 | **Mechanisms are not specified as testable components.** No explicit input / algorithm / output / acceptance test / failure mode contract per mechanism (SDD has failure modes, not acceptance tests). | SDD §5.1, SRS §6 | **HIGH** | Define per-mechanism test contracts; each mechanism gets deterministic scenario tests from the curated dataset. | §3 (MR-MECH-1), §9 |
| G12 | **Calibration is only "shown to exist."** No metric for whether role-routing agreement improves before vs after calibration. | SRS FR-2.8, Doc 6 §3.2 | **HIGH** | Add pre/post routing-agreement metric on the 5-scenario calibration set + confidence uplift. | §3 (MR-EVAL-6), §9 |
| G13 | **No hackathon deliverable checklist** mapping the 20 required deliverables (concept note, prototype, sample schema, source list, 4Q dashboard, signal cards, 5 role views, alerts, digest, Athena, calibration example, classification validation, source-linking validation, discovery-time test, architecture diagram, risk summary, deck, demo dataset, demo script, offline fallback) to actual artifacts. | All docs | **HIGH** | Produce explicit checklist with artifact locations. | §10, §13 |
| G14 | **No rubric traceability matrix** (Requirement → Status → Gap → Change → Location → Demo Evidence → Metric). Nothing is "complete" just because a doc mentions it. | All docs | **HIGH** | Produce matrix; mark everything honestly (specified ≠ implemented). | §10 |
| G15 | **Document contradictions unresolved** (768 vs 384-dim embeddings; Twitter remnants; confluence ≥2 vs ≥3; 100 vs 500 synthetic; ontology factual errors like fitusiran→"Alhemo"). | SDD, Doc 1, SRS ontology | **MEDIUM** | Resolve per §2; edit the weaker docs. | §2, §11 P0 |
| G16 | **Ontology factual QA gap.** `fitusiran` listed with brand "Alhemo" (Alhemo = concizumab) and approval status "FDA approved 2023"; `marstacimab` listed "Phase 3" (approved Dec 2024, verify). These errors would be caught by the planned B.Pharm validation layer — the layer must actually run before demo. | SRS §2.2.4 ontology | **MEDIUM** | Ontology v2 QA pass by B.Pharm; versioned ontology with `updated_by` audit. | §3 (MR-ONT-1), §11 P2 |
| G17 | **Model/version metadata missing from AI outputs.** Auditability requires reconstructing "what produced this" (model, version, prompt template, config hash, temperature) on every AI output. | SDD §2.9 (audit exists), traceability.py | **MEDIUM** | Add `model_metadata` to every insight; log in audit trail. | §3 (MR-SEC-1), §6, §9 |
| G18 | **NewsAPI quota assumption.** Docs historically assumed 500 req/day; the verified Developer/free tier is **100 req/day** (dev/testing only, 24h article delay — not real-time, not production). Connector must be quota-aware and degrade to cache/synthetic on exhaustion. | All docs (now corrected to 100/day) | **MEDIUM** | Quota-aware connector design + documented degradation (Redis → bronze → synthetic). | §5, §11 P1 |
| G19 | **2-page concept note deadline (within 48h of Aug 12 kickoff) is untracked** as a deliverable with owner and source material. | Doc 1 timeline | **MEDIUM** | Add to deliverable checklist with owner + content outline sourced from this plan. | §11 P0, §13 |
| G20 | Minor naming inconsistency: summarizer "DistilBART (sshleifer)" in stack vs "facebook/bart-large-cnn" in master plan/SRS. | CLAUDE.md stack vs Master Plan | **LOW** | Unify on `facebook/bart-large-cnn`. | §2 |
| G21 | README Roadmap "Phase 2 — Future Expansion" lists 5 roles + ClinicalTrials.gov as future, contradicting the corrected scope. | README | **LOW** | Update README roadmap to match corrected plan. | §2, §11 P0 |

**Severity counts:** 5 CRITICAL · 9 HIGH · 5 MEDIUM · 2 LOW. All CRITICAL and HIGH gaps are closed in this document and in the revised roadmap (§11).

---

# 2. CONTRADICTIONS BETWEEN DOCUMENTS

| # | Document A | Document B | Conflict | Correct interpretation | Required change |
|---|---|---|---|---|---|
| C1 | **Master Plan §2/§3 + README:** "Primary MVP Role: Medical Affairs", "One Role: Medical Affairs", "Everything else Phase 2". | **SRS §1.2 + UI doc §3.1 + Pitch §2:** Five roles in MVP (Medical Affairs, Regulatory, Market Access, Commercial, R&D); role badges + role filter throughout. | Is the MVP one role or five? The two canonical-ish docs contradict on the product's core scope. | The kickoff problem statement ("for every function") and SRS intent are the product; the Master Plan's "one role" was scope discipline, not product intent. **One engine, role interpretations** — the correction directive is explicit and preserves the architecture (role_relevance JSONB already scores all roles). **Superseded by v1.1+: SIX primary functions (Medical Affairs, Regulatory, Safety/Pharmacovigilance, Market Access, Medical Communications, Leadership) with Commercial/R&D/CI/Strategy as extended stakeholders only — see MR-ROLE-1 and Master Plan v4.0 §12.5.** | Rewrite Master Plan §2/§3 and README MVP Scope: "One intelligence engine; six primary function perspectives; demo leads with Medical Affairs." Do NOT create six engines. |
| C2 | **Master Plan §3/§5 + README:** Two primary live sources (PubMed Central + NewsAPI); "no additional scrapers". | **SRS FR-2.1.1/AC-1:** Fetch from 7 sources; AC-1 = "≥3 live public sources + synthetic fallback". **SDD §1.1/§3.1:** 6 fetchers incl. Twitter. | How many sources are live at MVP? 2 vs 3 vs 7 (with Twitter). | SRS AC-1 is the binding acceptance test: ≥3 genuinely live. Choose: **LIVE = PubMed/PMC, NewsAPI, ClinicalTrials.gov** (free, keyless or simple keys, reliable). **ADAPTER-READY = FDA openFDA, EMA RSS, congress archives (ASH/ISTH/WFH/EHA), Reddit/advocacy** (thin connectors, seeded with synthetic where unavailable). **Twitter removed** (free tier discontinued; not in problem scope). | Master Plan §3/§5, README Data Sources, SDD §1.1/§3.1 (delete fetch_twitter), SRS keeps 7 in "target architecture" but re-labeled LIVE/ADAPTER/SYNTHETIC. |
| C3 | **Master Plan §4 + CLAUDE.md:** 384-dimensional embeddings (all-MiniLM-L6-v2). | **SDD §2.5/§2.6 + Doc 5 Part 4:** `embedding vector(768)`, "768-dim". | Embedding dimension mismatch. | `sentence-transformers/all-MiniLM-L6-v2` outputs **384-dim** vectors. 768 would corrupt the schema and search. | SDD: `vector(768)` → `vector(384)` everywhere; ivfflat index stays. |
| C4 | **Master Plan §6 + SRS FR-2.3.1:** Confluence needs ≥3 distinct signal types in 48h. | **Doc 1 Opt-11 + SDD §2.4:** `CONFLUENCE_MATRIX` fires at ≥2 signal types (e.g., regulatory+clinical). SRS patterns: mostly 3, but inhibitor_safety_wave = 2/24h. | Confluence threshold: 2 or 3? | Default = **≥3 distinct signal types within 48h** (the correction directive: "multiple independent sources describing the same event → one consolidated event"). Keep a configurable per-pattern override (inhibitor/safety wave = 2 types / 24h). Engine is config-driven; both docs become one rule set. | Unify `HAEMOPHILIA_CONFLUENCE_PATTERNS` as the single source of truth; document default 3/48h + exceptions. |
| C5 | **Master Plan §4 + Doc 1 + SRS FR-2.2.3A:** Gemma 3 4B Instruct is default reasoning LLM; BART-large-cnn is summarizer + fallback. | **Doc 5 Part 4:** "Default: facebook/bart-large-cnn" for LLM/summarization; Gemma listed only as a swap-in. | Which model does narrative synthesis / Four-Question reasoning / Ask Athena? | SRS FR-2.2.3A/B is the most recent, most specific: **`google/gemma-3-4b-it` for reasoning (default), `facebook/bart-large-cnn` for batch summarization + automatic fallback.** Model-agnostic via env vars. | Doc 5 Part 4 wording: move Gemma to default reasoning slot. |
| C6 | **CLAUDE.md stack:** "DistilBART (sshleifer/distilbart-cnn-12-6)" for summarization. | **Master Plan §4 + SRS §4.2:** `facebook/bart-large-cnn`. | Summarizer identity. | Use `facebook/bart-large-cnn` (canonical env var `SUMMARIZER_MODEL`). | CLAUDE.md stack line updated. |
| C7 | **Master Plan §5:** "500-Signal Pre-Curated Synthetic Dataset". | **Doc 1 Week 4:** "Curate demo dataset (100 high-quality signals)". | Dataset size: 500 or 100? | 500-signal curated fallback feed (deterministic, annotated, clearly labeled synthetic). The evaluation dataset (~45 items) is a separate, smaller, ground-truthed subset used for tests — not a second demo feed. | Unify on 500 curated + separate evaluation set; Doc 1 wording updated. |
| C8 | **SRS ontology:** `fitusiran.brand_names = ["Alhemo"]`, `status: "FDA approved 2023"`. | **SRS ontology (same file):** `concizumab.brand_names = ["Alhemo"]`; real-world: fitusiran is Sanofi RNAi, brand ≠ Alhemo. | Ontology factual error (copy-paste). | fitusiran = Sanofi RNAi (antithrombin knockdown); Alhemo = concizumab (Novo Nordisk). Approval dates for fitusiran/marstacimab must be verified and corrected (marstacimab approved Dec 2024; verify fitusiran). | B.Pharm ontology v2 QA; add ontology version + `updated_by`; include an "ontology QA" row in the evaluation dataset. |
| C9 | **Doc 1 Gap-1 + SDD §3.1:** Twitter/X as a data source ("1000 tweets"). | **Master Plan + CLAUDE.md + problem scope:** no Twitter; social = Reddit. | Is Twitter in scope? | No. Twitter's free API tier no longer supports this use case. Reddit PRAW (or advocacy/forum sources) covers patient/access signals. | Remove Twitter from SDD data flow and external APIs. |
| C10 | **SRS §2.2.1:** "Extraction accuracy target: >90%". | **SRS AC-3:** "Classifies signals into 7 types with ≥85% accuracy". | Different metrics, sometimes quoted interchangeably. | Both are valid but distinct: entity-extraction accuracy (≥90%) and signal-classification accuracy (≥85% overall, with precision/recall/confusion matrix per class). Evaluate both separately with separate labelled sets. | §9 defines both tests; docs keep both targets. |
| C11 | **Doc 6 §2.2:** "Intelligence needed across 25 functions". | **Corrected scope:** 5 role perspectives in MVP. | 5 vs 25 functions. | Not a contradiction: 5 roles are the MVP interpretation layer; the 25-function framing is the company-wide pain (problem statement). Corrected plan: 5 roles now, documented extension path to more (Q3 weights are data-driven, adding a role = adding a row). | No doc change; §7 documents the extension path. |

**Resolution rule applied:** where docs disagree, this plan adopts the version that best satisfies (a) the correction directive, (b) SRS acceptance criteria, (c) hackathon judging weights — while preserving the existing architecture. The weaker documents are listed in the "Required change" column; §11 Phase 0 makes those edits.

---

# 3. FINAL METARADAR REQUIREMENTS (Corrected Specification)

Supersedes conflicting SRS statements. Existing SRS FR IDs remain valid where unchanged; new requirements use `MR-*` IDs. Every acceptance test is runnable; nothing below is "aspirational."

## 3.1 Product definition & role model

- **MR-ROLE-1 [SOURCE-DERIVED]:** MetaRadar is ONE intelligence engine producing ONE normalized signal, ONE evidence graph, and ONE explainable prioritization layer, interpreted by SIX primary functions (kickoff): **Medical Affairs, Regulatory, Safety / Pharmacovigilance, Market Access, Medical Communications, Leadership** — with **Commercial and R&D retained as extended/future roles** (not removed). Each function view includes: relevance score, function-specific explanation, function-specific impact, function-specific suggested action, and the SAME underlying evidence chain. **No function receives its own engine.**
- **MR-ROLE-2 [SOURCE-DERIVED]:** The Five Intelligence Mechanisms are preserved and are non-negotiable: 1) Signal Confluence Detection, 2) Signal Lifecycle Tracking, 3) Red-Team Contradiction Analysis, 4) Missing-Signal Detection, 5) Stakeholder Learning / HITL Calibration.
- **MR-ROLE-3 [SOURCE-DERIVED]:** The Four-Question Framework is the decision interface: Q1 What changed? · Q2 Why does it matter? · Q3 Which function should review it? · Q4 What action may be required?
- **MR-ROLE-4 [ARCHITECTURAL]:** Adding a future function = adding a row in `scoring_weights` + a function label + an explanation template. No re-architecture. (Addresses Doc 6's 25-function framing.)
- **MR-ROUTE-1 [SOURCE-DERIVED] (newest kickoff — relevance-based routing):** *"Not every signal needs to go to everyone."* Flow: External Signal → Understand → Classify → Determine relevance → Route to relevant function(s) → Role-specific explanation/action. Every signal stores `primary_function` · `secondary_functions[]` · `function_relevance_score` · `routing_reason` (explainable) · `suggested_action`. The initial routing matrix is a SEED (clinical trial → Medical Affairs + Medical Communications + Regulatory; safety → Safety/PV (+ MA/Regulatory where relevant); access → Market Access (+ MA where relevant); regulatory decision → Regulatory + Medical Affairs (+ Leadership where material); congress data → Medical Affairs + Medical Communications (+ Regulatory/Leadership by relevance); publication → Medical Affairs + Medical Communications (+ others by content) — and is adjustable through stakeholder calibration. NO per-function engines: one pipeline, role-specific views.
- **MR-CGR-1 [SOURCE-DERIVED] (newest kickoff — congress as first-class signal):** `signal_type=CONGRESS` with subtypes `congress_abstract · oral_presentation · poster · new_congress_data · updated_congress_analysis · presentation_of_previously_known_data · congress_related_safety_signal · congress_related_efficacy_signal · congress_related_pro · congress_related_mechanism_dosing`. Congress signals participate in Confluence, Lifecycle, Red-Team, priority scoring, function routing, evidence chain, and stakeholder calibration.
- **MR-PUB-1 [SOURCE-DERIVED] (newest kickoff — publication as first-class signal):** `signal_type=PUBLICATION` with subtypes `peer_reviewed_publication · preprint · real_world_evidence · post_hoc_analysis · long_term_follow_up · safety_publication · patient_reported_outcomes · mechanistic_publication`. Publications connect to `company · asset · trial · development · disease · patient population`.
- **MR-CGR-2 [SOURCE-DERIVED] (congress↔lifecycle connection):** A congress presentation may be a NEW DEVELOPMENT or NEW EVIDENCE ABOUT AN EXISTING DEVELOPMENT. Confluence attempts to connect trial → congress abstract → oral → poster → publication into ONE development/evidence chain (never four unrelated cards). Lifecycle records `event_type · event_date · development_id · source_id`. (Web-verified justification: Novo Nordisk's own public ISTH 2026 material shows multiple presentations/analyses per development, incl. FRONTIER4/denecimig and Explorer10/concizumab.)
- **MR-WATCH-2 [SOURCE-DERIVED] (Watch-for-Next, newest kickoff):** Stakeholder-defined WATCH RULES extend Missing-Signal: `source_event → expected/interesting next event → monitoring window → responsible function → status` with statuses `watching · new_evidence_detected · no_new_evidence · watch_expired · human_review_required`. Wording limited to *"Watch for / Expected/possible next evidence / Not observed yet"*; absence → *"No subsequent congress evidence observed during the configured monitoring window."* (never proof that nothing happened). No separate watch engine — this is Missing-Signal + Calibration.
- **MR-SIG-1 [SOURCE-DERIVED]:** Every normalized signal SHALL carry the canonical dimensions: `disease` (HA/HB/both/unknown) · `patient_type` (with/without/unknown inhibitors) · `company` · `asset` · `asset_type` · `signal_type` (11 categories incl. congress + publication with subtypes) · `signal_subtype` · `development_id` · `event_date` · `source_id` · `priority` (high/medium/low) · `impacted_functions` (primary + secondary) · `evidence_level`. These are in the schema, not only the docs.
- **MR-FIS-1 [SOURCE-DERIVED]:** Every intelligence output SHALL be labeled **FACT** (directly supported by reliable source evidence) / **INTERPRETATION** (reasoned interpretation, labeled as such) / **SPECULATION** (early/uncertain, never presented as fact) — in schema, AI prompts, UI cards, API responses, audit trail, and evaluation.
- **MR-EVS-1 [SOURCE-DERIVED+WEB-VERIFIED]:** Evidence-sufficiency gate before narrative generation: retrieve evidence → sufficient? → YES: grounded interpretation → NO: "Insufficient evidence to support an interpretation." + human review. Consistent with FDA thinking on AI credibility and independent review of AI-supported outputs.
- **MR-ACT-1 [SOURCE-DERIVED]:** Controlled action vocabulary: `monitor` · `review` · `prepare_internal_briefing` · `prepare_scientific_faq` · `escalate` · `request_stakeholder_review` · `no_immediate_action`. AI suggests, never executes. Every action carries: Action · Reason · Relevant function · Evidence · Confidence · Human-review requirement.
- **MR-ACT-2 [SOURCE-DERIVED] (role-aware actions, newest kickoff):** Suggested actions are role-specific — Medical Affairs (review scientific evidence / prepare internal scientific briefing / monitor new clinical evidence), Medical Communications (review congress-publication development / prepare scientific FAQ / monitor emerging scientific narrative), Regulatory (review regulatory implication / monitor regulatory milestone), Safety/PV (safety review / request pharmacovigilance assessment / monitor safety evidence), Market Access (review access-reimbursement implications / monitor HTA-payer developments), Leadership (escalate material cross-functional development / request strategic review).

## 3.2 Data sources

- **MR-SRC-1 [SOURCE-DERIVED]:** The MVP MUST demonstrate **≥3 genuinely live public sources** (SRS AC-1). Core live set:
  1. **NCBI PubMed / E-utilities** (E-utilities REST, free) — PubMed literature retrieval, trial readouts. (PMC full-text services = optional extension.)
  2. **NewsAPI** (free tier, quota-aware) — industry news, press releases.
  3. **ClinicalTrials.gov** (public v2 API, free, keyless) — trial registrations, status changes, protocol amendments.
- **MR-SRC-2 [SOURCE-DERIVED]:** Additional sources are **ADAPTER-READY** (connector scaffold + rate limits + graceful degradation; may be seeded from synthetic for demo): FDA openFDA, EMA RSS, congress abstract archives (ASH, ISTH, WFH, EHA), patient/access sources (Reddit PRAW via public subreddits, advocacy feeds). No adapter is described as "live production-integrated" unless it actually fetches live data on demo day.
- **MR-SRC-3 [SOURCE-DERIVED]:** **SYNTHETIC-DEMO**: 500 curated, deterministic, clearly-labeled haemophilia signals for offline demo, failure fallback, and reproducibility. Synthetic rows carry `is_synthetic: true` and are never presented as real.
- **MR-SRC-4 [SOURCE-DERIVED]:** Source status MUST be visible in the UI footer (LIVE ✓ / ADAPTER ⚠ / SYNTHETIC ◐ per source). (UI doc §3.1 already specifies this; enforce the three-way label.)
- **MR-SRC-5 [ARCHITECTURAL]:** No Twitter/X. Reddit covers social. (C2, C9.)

## 3.3 Business-level success metrics (new)

- **MR-EVAL-1 — Source-linked summaries [SOURCE-DERIVED+WEB-VERIFIED]:** Target **100%**. Every high-priority AI-generated insight MUST contain: source, URL, publication date, supporting excerpt, evidence chain, confidence, and an explicit "AI-generated" label. If evidence is insufficient, the system MUST NOT fabricate a conclusion (output the insufficiency guardrail). *Web-verified: traceability to named primary sources is the industry non-negotiable for audit-ready CI.*
- **MR-EVAL-2 — Signal classification [SOURCE-DERIVED]:** Target **≥85% overall accuracy** on a labelled validation dataset (25 curated examples, B.Pharm-reviewed ground truth). Report: accuracy, per-class precision/recall, and confusion matrix. Entity-extraction accuracy separately ≥90% (SRS FR-2.2.1) on a 20-example extraction set.
- **MR-EVAL-3 — Top-signal discovery time [ARCHITECTURAL]:** Target **≤5 minutes**. Reproducible protocol: 100 weekly signals (deterministic synthetic week) → task: "identify the top 5 priority developments" → measure time to decision. Baseline: same task with a manual search/browse tool. Acceptance: MetaRadar median ≤5 min AND ≥50% faster than baseline.
- **MR-EVAL-4 — Confidential / patient data [SOURCE-DERIVED]:** Evaluation target **0** (not a mathematical guarantee). Only public or synthetic data. A dedicated PII/PHI detection + redaction layer runs before persistence (spaCy NER contributes to entity detection; it is not claimed as a guaranteed scrubber; low-confidence content is rejected/quarantined); audit check asserts zero private data rows.
- **MR-EVAL-5 — Source-failure resilience [SOURCE-DERIVED]:** **Target**: graceful degradation during tested connector/model failures — any/all live sources down → cached/bronze/synthetic fallback, verified with failure-injection tests (not an untested guarantee; Master Plan §10 retained).
- **MR-EVAL-6 — Stakeholder calibration improvement [SOURCE-DERIVED+ARCHITECTURAL]:** Measure whether role-routing agreement improves pre vs post calibration on the 5-scenario calibration set: **top-1 role agreement ≥10 points uplift** (e.g., 60% → ≥70%) AND confidence uplift >0 on corrected routes. Also report per-role avg rating trend and weight drift (SDD §9.1 already tracks these — now with an acceptance threshold).
- **MR-EVAL-7 — Four-Question completeness [SOURCE-DERIVED]:** Target **100%** of high-priority signal cards contain Q1–Q4 + evidence + confidence + source + timestamp (see MR-Q-1).

## 3.4 Four-Question completeness

- **MR-Q-1 [SOURCE-DERIVED+ARCHITECTURAL]:** Automated acceptance test `test_four_question_completeness`: for every card with priority ≥ HIGH, assert non-empty: `q1.what_changed`, `q2.why_it_matters`, `q3.role_routing[]` (≥1 role badge with confidence), `q4.suggested_actions[]` (prefixed "Suggested — requires human review"), plus `evidence_chain[]`, `confidence`, `source`, `timestamp`, `ai_generated_label`. Result: 100% pass on the demo dataset and on live/fallback data. UI renders a per-card completeness strip (Q1✓ Q2✓ Q3✓ Q4✓ ⛓✓) so judges see the acceptance check pass.

## 3.5 Weekly Intelligence Digest (new)

- **MR-DIGEST-1 [SOURCE-DERIVED+ARCHITECTURAL]:** Weekly Intelligence Digest generated by the SAME engine (batch run of synthesis + brief agents over the trailing 7-day window; no second pipeline). Structure per development: What changed · Why it matters · Function affected · Suggested action · Evidence. Top developments first, ranked by explainable priority. **Role-filtered variants:** Medical Affairs Digest / Regulatory Digest / Market Access Digest / Commercial Digest / R&D Digest (same underlying events; role-specific relevance, impact, and actions). Exportable (Markdown/PDF/JSON) and viewable at `/digest`. Backend: `GET /api/v1/digest?role=&window=7d` + APScheduler nightly generation job.

## 3.6 Explainability (priority decomposition)

- **MR-EXP-1 [SOURCE-DERIVED+WEB-VERIFIED]:** Every high-priority signal renders an explicit "Priority: N/100 — WHY?" block listing contributing factors with ✓/✗ status and contribution: multiple independent sources ✓, relevant competitor ✓, recent activity increase (velocity) ✓, Phase III milestone ✓, regulatory implication ✓, confluence detected ✓, contradiction/missing-signal flags (✓ adds scrutiny, may raise priority). Below it: evidence chain (Sources A/B/C), overall confidence (with rationale: source count × platform diversity × credibility), and per-role relevance with the factors that drove each score. *Web-verified: audit-ready CI must survive "why should I trust this number?" from senior leadership.*

## 3.7 Ask Athena (grounded, structured answers)

- **MR-ATHENA-1 [SOURCE-DERIVED+WEB-VERIFIED]:** Every Athena answer follows the required schema: **Answer · Evidence · Sources · Confidence · Relevant entities · Lifecycle context · Contradicting evidence (if present)**. When retrieval yields insufficient evidence, Athena MUST return: *"Insufficient evidence to support an interpretation."* — never a hallucinated answer. Answers are function-scoped. *Web-verified: RAG bounded to verified document sets with strict grounding is the standard hallucination mitigation in healthcare AI.*

## 3.8 Temporal / change intelligence (simple, explainable)

- **MR-TEMP-1 [SOURCE-DERIVED+ARCHITECTURAL]:** Distinguish **CURRENT STATE** from **WHAT CHANGED**. Deterministic model only: per-entity daily mention counts (`trending_scores`), 7-day velocity (slope), acceleration (Δvelocity), and delta vs previous window ("3 signals in last 48h vs 0 in prior week"). Outputs: velocity badge (rising/steady/declining), acceleration flag ("activity accelerating"), trajectory label from B.Pharm timeline patterns (pre-approval surge, access decline — existing `temporal_patterns.py`). NO predictive ML, no opaque models.

## 3.9 Watchlist / entity focus

- **MR-WATCH-1 [SOURCE-DERIVED+ARCHITECTURAL]:** Watchlist API + UI: `GET/POST/DELETE /api/v1/watchlist`. A watched entity (drug, company, trial, indication, mechanism, competitor) opens a watch view showing: latest signals, lifecycle, confluence, contradictions, missing signals, trend/velocity, role relevance, suggested actions, and evidence — all via existing endpoints filtered by entity. Reuses entity + lifecycle infrastructure; zero new intelligence engines.

## 3.10 Mechanisms as testable components

- **MR-MECH-1 [SOURCE-DERIVED]:** Each mechanism is defined by input / algorithm / output / acceptance test / failure mode (full contracts in §9.3). Acceptance tests run against the curated evaluation scenarios with ground truth. Per-mechanism demo evidence must be provable: "this scenario was deliberately constructed to test this mechanism."

## 3.11 Role routing & calibration (unchanged behavior, new measurement)

- Keep SRS FR-2.5 (function scoring matrix — 6 primary + 2 extended rows), FR-2.8 (feedback/calibrate endpoints, simulated personas). Add MR-EVAL-6 measurement. Initial weights from SRS §2.5 remain; weights are data, not code.

## 3.12 Guardrails (explicit, enforced)

- **MR-GRD-1 [SOURCE-DERIVED]:** public/synthetic data only · no confidential data · no patient-identifiable data (dedicated PII/PHI detection + redaction layer before persistence; spaCy NER contributes but is not a guaranteed scrubber; low-confidence content rejected/quarantined) · no automated clinical/regulatory/commercial decisions · AI-generated content clearly labeled (non-suppressible `DisclaimerBadge`) · human review required for recommended actions · evidence required for claims · target: graceful degradation during tested source failures (fallback cascade: Redis → bronze → synthetic) · synthetic fallback available offline (local 500-signal dataset) · secrets never enter source control (`.env` gitignored; env vars only).
- **MR-ONT-1 [SOURCE-DERIVED+ARCHITECTURAL]:** Ontology v2 QA by B.Pharm corrects factual errors (C8), adds version + `updated_by` metadata, and is validated by an ontology-QA evaluation row. (C8 fixes: fitusiran ≠ Alhemo; verify fitusiran/marstacimab approval status.)

## 3.13 Security / auditability (retained and strengthened)

- **MR-SEC-1 [SOURCE-DERIVED+WEB-VERIFIED]:** Retain: append-only WORM `audit_log`, `stakeholder_feedback` (append-only), `calibration_history`, source provenance (`raw_signals_bronze` + sha256), timestamps, evidence references. Strengthen: every AI-generated output persists `model_metadata` (model name/version, task, temperature, prompt-template id, config hash) so the system can reconstruct *"What information did the system use to produce this, and with what model?"*. *Web-verified: model credibility/versioning is required under emerging FDA/EMA AI guidance.*

## 3.14 Anti-over-engineering

- **MR-SIMPLE-1 [SOURCE-DERIVED]:** Prefer simple, explainable, deterministic, local, testable, reliable over complex, opaque, GPU-heavy, research-grade. No feature is added in this plan that does not close a measured gap in §1. No new AI models. No new vendors. All mechanisms run locally.

---

# 4. FINAL ARCHITECTURE (Corrected ASCII)

One engine, one evidence graph, one prioritization layer, six function interpretations (+ extended Commercial/R&D). The 10-node LangGraph workflow is preserved; only the function-output layer and new features (digest, watchlist, temporal, explainability, Athena schema) attach to existing nodes.

```text
                         PUBLIC SIGNALS
                 LIVE          |        ADAPTER-READY        SYNTHETIC-DEMO
        PubMed/PMC · NewsAPI · |  FDA openFDA · EMA RSS ·    (500 curated,
        ClinicalTrials.gov     |  Congress (ASH/ISTH/WFH/EHA)  labeled)
                               |  Reddit/advocacy
                               v
                  ┌───────────────────────────┐
                  │   INGESTION (node_ingest) │──► raw_signals_bronze (verbatim replay)
                  └─────────────┬─────────────┘
                                v
                  ┌───────────────────────────┐
                  │  VALIDATION (node_validate)│  quality · dedup · PII scrub
                  └─────────────┬─────────────┘
                                v
                  ┌───────────────────────────┐
                  │  ENTITY + ONTOLOGY        │  spaCy NER + B.Pharm haemophilia
                  │  (node_nlp + node_onto)   │  ontology → ONE normalized signal,
                  └─────────────┬─────────────┘  ONE entity/evidence graph
                                v
        ┌───────────────────────┴───────────────────────┐
        │           ONE INTELLIGENCE ENGINE             │
        │  1. Confluence   (node_confluence)  ≥3 types/48h│
        │  2. Lifecycle    (node_lifecycle)   FSM+expected│
        │  3. Red-Team     (node_redteam)     NLI pairs   │
        │  4. Missing-Sig. (node_missing_signal) silence  │
        │  5. Temporal     (velocity/accel, explainable)  │
        └───────────────────────┬───────────────────────┘
                                v
                  ┌───────────────────────────┐
                  │  SYNTHESIS + PRIORITIZATION│  ONE explainable priority score
                  │  (node_synthesize)        │  (factor decomposition MR-EXP-1)
                  └─────────────┬─────────────┘
                                v
                  ┌───────────────────────────┐
                  │  FUNCTION INTERPRETATION  │  ONE event × SIX primary functions
                  │  (node_brief + routing)   │  (+ extended Commercial/R&D)
                  │                           │  primary + secondary functions +
                  │                           │  routing_reason (relevance-based)
                  └─────────────┬─────────────┘
                                v
        ┌───────────────────────────────────────────────────────┐
        │  FOUR-QUESTION INTERFACE · DIGEST · WATCHLIST · ATHENA│
        │  Q1 What changed │ Q2 Why it matters │ Q3 Who reviews │
        │  Q4 What action  │ evidence · confidence · source     │
        └─────────────┬─────────────────────────────────────────┘
                      v
        ┌───────────────────────────────┐
        │  STAKEHOLDER CALIBRATION (HITL)│──► recalibrates prioritization/role
        │  (node_calibrate)             │    weights (audited, measured pre/post)
        └───────────────────────────────┘

  Storage: PostgreSQL 16 + pgvector (384-dim) · Redis 7 cache/queue
  Scheduler: APScheduler (single, in-process) — 2h fetch · digest nightly · recalibration on demand (Celery removed)
  AI (local default): spaCy en_core_sci_md · Gemma 3 4B (reasoning) · BART-large-cnn
              (summarize+degraded factual fallback) · BART-large-MNLI (classify+red-team)
              · MiniLM (384-dim) · optional hosted Grok (LLM_PROVIDER=xai|auto, privacy-gated)
```

**Key corrections vs old diagrams:** role layer expanded from "MEDICAL AFFAIRS UI" to six function interpretations (+ extended); sources split into three tiers; Temporal mechanism added; Calibration explicitly feeds back into prioritization weights (not just Q3); 384-dim noted; Twitter removed.

---

# 5. DATA-SOURCE ARCHITECTURE

| Source | Tier | Status | API | Quota/dependency | Demo behavior | Fallback if down |
|---|---|---|---|---|---|---|
| PubMed / PMC | **LIVE** | Core MVP | E-utilities REST (esearch/efetch/esummary) | Free; ~3 req/s unkeyed (10 req/s with key) | Real literature + readout signals with PMID links | Redis cache → bronze → synthetic |
| NewsAPI | **LIVE** | Core MVP | REST `everything`/`top-headlines` | Developer/free tier **100 req/day** (dev/testing only, 24h article delay; quota-aware — never assume 500) | Real industry news + press releases | Cache (24h) → bronze → synthetic; quota-aware batching (one fetch per 2h cadence, incremental since last run) |
| ClinicalTrials.gov | **LIVE** | Core MVP | Public v2 API (JSON, keyless) | Free, no key | Real trial status changes, new registrations, protocol amendments | Cache → bronze → synthetic |
| FDA (openFDA) | **ADAPTER-READY** | Week 2 connector | REST (drugs/label, drugs/events) | Free, keyless | Approvals, label changes, safety comms | Synthetic seeding for demo determinism |
| EMA | **ADAPTER-READY** | Week 2 connector | EMA RSS / public register | Free | CHMP opinions, approvals | Synthetic seeding |
| Congress archives (ASH/ISTH/WFH/EHA) | **ADAPTER-READY** | Week 3 connector | Public abstract portals / official archives | Free, structure varies | Congress abstract signals (flagship demo uses ASH 2026 Hemgenix abstract) | Synthetic seeding (demo story uses seeded ASH data, labeled) |
| Reddit / advocacy | **ADAPTER-READY** | Week 3 connector | PRAW (public subreddits r/hemophilia, r/raredisease) + WFH/NHF feeds | Free with OAuth | Patient/access narrative signals | Synthetic seeding |
| Synthetic demo set | **SYNTHETIC-DEMO** | Always available | Local JSON (`data/synthetic/`) | None | Deterministic 500-signal fallback; `is_synthetic=true`; also deterministic evaluation scenarios (§9.2) | N/A (it IS the last fallback) |

**Rules:** (1) ≥3 LIVE must actually fetch on demo day (SRS AC-1). (2) ADAPTER sources are labeled in UI as adapters, not full integrations. (3) Synthetic rows never masquerade as real. (4) Every fetched payload persists to `raw_signals_bronze` with source + sha256 before any transformation. (5) Twitter is out of scope.

---

# 6. INTELLIGENCE PIPELINE (Signal → Decision)

1. **FETCH** (every 2h, async parallel) — 3 LIVE + adapters; tenacity retries (3×, 2s/4s/8s); persist raw to bronze.
2. **VALIDATE** — required fields, length >50, English, quality score; reject/deduplicate (>80% similarity).
3. **SCRUB** — PII/PHI redaction before storage (audit-logged).
4. **EXTRACT + NORMALIZE** — spaCy NER → ontology resolution → ONE normalized entity graph (Hemlibra = emicizumab = Roche competitor).
5. **CLASSIFY** — zero-shot BART-MNLI → canonical signal types with congress/publication subtypes (grounded; evaluated per MR-EVAL-2).
6. **CONFLUENCE** — ≥3 distinct signal types / 48h (per-pattern config) → consolidated event with severity. **Development-link decision:** congress/publication signal matching an existing `development_id` → NEW EVIDENCE ABOUT EXISTING DEVELOPMENT (linked into the chain, not a new card); else NEW DEVELOPMENT (MR-CGR-2).
7. **LIFECYCLE** — FSM `announced → in_trial → interim_result → final_result → congress_publication → regulatory_development → approved → post_market | discontinued`; expected-next computed; every event records `event_type · event_date · development_id · source_id`.
8. **RED-TEAM** — pairwise NLI (same BART-MNLI) within 90d window; contradiction >0.6 → dual evidence chains + devil's-advocate note + human-review flag.
9. **MISSING-SIGNAL + WATCH-FOR-NEXT** — expected-event rules (B.Pharm) + `max_lag_days`; confidence-by-silence `min(0.4 + days×0.02, 0.95)`; human review required. Stakeholder watch rules → `watch_items` (statuses watching/new_evidence_detected/no_new_evidence/watch_expired/human_review_required); absence → "No subsequent congress evidence observed during the configured monitoring window."
10. **TEMPORAL** — daily counts → 7d velocity → acceleration → delta ("what changed") → trajectory stage (B.Pharm patterns). Explainable; no ML.
11. **SYNTHESIZE + PRIORITIZE** — narrative anchored in source excerpts; ONE explainable priority score (factor decomposition MR-EXP-1); model_metadata attached.
12. **FUNCTION INTERPRET (relevance-based routing)** — one event × six primary functions (+ extended): relevance score (calibrated weights) + function explanation + function impact + function action (controlled vocabulary, role-aware per MR-ACT-2); `primary_function` + `secondary_functions[]` + `routing_reason` stored in `signal_routing` (MR-ROUTE-1); same evidence chain.
13. **BRIEF (Q1–Q4)** — completeness-checked cards (MR-Q-1); congress/publication cards render the Development Connection block (Development · Event · Relationship · Related evidence, MR-CGR-2); digest generation (MR-DIGEST-1); watchlist hydration (MR-WATCH-1/MR-WATCH-2); Athena retrieval index updated.
14. **CALIBRATE (HITL)** — stakeholder ratings → weight update (audited) → next cycle uses new weights → pre/post agreement measured (MR-EVAL-6). **Calibration scope: priority · routing · action · watch rules · relevance criteria** — a comment like "monitor this competitor trial for upcoming congress disclosures" creates a watch rule (BEFORE/AFTER shown).
15. **DELIVER** — Four-Question UI · role-filtered views · digest · alerts · watchlists · Ask Athena · audit export.

---

# 7. FUNCTION MODEL (One Signal → Six Interpretations)

The same intelligence event carries six primary function-specific interpretations (plus two extended), all from the same evidence graph.

| Function | Relevance driver (matrix) | Function-specific explanation/impact | Function-specific suggested action (example: Hemgenix 3-yr durability at ASH) |
|---|---|---|---|
| **Medical Affairs** | Clinical + safety + congress weights (0.9/0.4/0.8…) | Sustained FIX durability strengthens the "curative vs lifelong prophylaxis" evidence story for HCPs; contradiction (sustained vs waning) must be reconciled before HTA engagement. | *Suggested — Prepare internal briefing: gene-therapy durability vs concizumab/mim8 prophylaxis positioning (requires human review).* |
| **Regulatory** | Regulatory filings weight (0.95) | Label/indication trajectory; any durability claims in labeling have regulatory implications; missing filings are tracked by missing-signal WATCH. | *Suggested — Review: Hemgenix/Roctavian label and safety communication updates (requires human review).* |
| **Safety / Pharmacovigilance** | Safety signal weight (0.95) | Waning-expression subset and safety communications are PV WATCH items; causality is never determined by the system. | *Suggested — Escalate: waning-expression subset watch with human review (requires human review).* |
| **Market Access** | HTA/reimbursement weight (0.9) | Durable efficacy shifts cost-effectiveness math for HTA bodies (NICE/G-BA); prophylaxis budget models may need re-run. | *Suggested — Prepare scientific FAQ: 3-yr durability evidence for HTA engagement (requires human review).* |
| **Medical Communications** | Congress/publication/company-news weights (0.7/0.5/0.5) | New durability narrative affects HCP communication and publication planning; FAQ readiness. | *Suggested — Prepare scientific FAQ: durability vs prophylaxis for HCPs (requires human review).* |
| **Leadership** | Strategic/pipeline weights (0.6/0.5) | Portfolio-level implications of gene-therapy durability for the prophylaxis franchise; escalation triggers. | *Suggested — Escalate: portfolio-level gene-therapy disruption briefing (requires human review).* |
| **Commercial (extended)** | Pipeline/competitive weights (0.8/0.4) | Gene-therapy durability pressures prophylaxis market share; mim8/concizumab positioning vs Roche/CSL needs refresh. | *Suggested — Review: competitor positioning documents and briefing decks (requires human review).* |
| **R&D (extended)** | Pipeline/clinical weights (0.85/0.7) | Durability benchmark for mim8 trial endpoints; long-term follow-up design implications. | *Suggested — Review: Hemgenix durability data vs mim8 trial design and endpoints (requires human review).* |

**Mechanics:** one engine → function scores via `scoring_weights` matrix (calibrated) → per-function explanation generated from the SAME evidence chain, function template, and signal-type weights. Q3 shows the six primary badges with confidence + "why this score" (MR-EXP-1) + inline ⭐ feedback. Extended roles (Commercial, R&D) are toggleable. Extension to more functions = new matrix row (MR-ROLE-4).

---

# 8. FOUR-QUESTION UI (Panel Specifications)

Every high-priority card renders Q1–Q4 + evidence + **F-I-S badge** (FACT / INTERPRETATION / SPECULATION / INSUFFICIENT), with the completeness strip (Q1✓ Q2✓ Q3✓ Q4✓ ⛓✓ F-I-S✓). Panel tints per UI doc §15.1 (`#F0F4FF / #FFF4E6 / #F0FFF4 / #FFF0F0`). **v4.0 evidence context:** every significant card additionally renders Q5 **HOW STRONG IS THE EVIDENCE?** (evidence-maturity label + confidence + source authority), Q6 **WHAT IS UNCERTAIN OR CONTRADICTORY?** (Red-Team flags + uncertainty penalties), Q7 **WHAT SHOULD WE WATCH NEXT?** (watch-for-next / expected milestones — monitoring wording, never a claim). Q1–Q4 remain the core stakeholder questions.

- **Q1 · WHAT CHANGED?** (blue) — Signal feed: signal-type badges, entity tags (ontology-resolved), freshness, **delta + velocity badge** ("3 signals in 48h · activity ↑" per MR-TEMP-1), analysis flags (⏱ lifecycle · ⚔ contradiction · 🕳 missing). This is the "current state vs what changed" answer.
- **Q2 · WHY DOES IT MATTER?** (orange) — Relevance breakdown (per-role bars), **"Priority: N/100 — WHY?" factor checklist** (MR-EXP-1), confluence alert + severity, lifecycle stage + expected next, contradiction flags with both chains, competitive context (ontology), trajectory stage.
- **Q3 · WHICH FUNCTION SHOULD REVIEW IT?** (green) — Six primary function badges with confidence (calibrated; extended Commercial/R&D toggleable), per-badge factor rationale, **routing reason line** ("why this function, why now" — MR-ROUTE-1), inline ⭐ stakeholder feedback widget (`POST /api/v1/feedback`), calibration status ("Regulatory 92% — up from 88% after calibration").
- **Q4 · WHAT ACTION MAY BE REQUIRED?** (red) — AI-suggested bullets from the **controlled action vocabulary** (monitor · review · prepare internal briefing · prepare scientific FAQ · escalate · request stakeholder review · no immediate action), **role-aware per function (MR-ACT-2)**, prefixed **"Suggested — requires human review"**, each carrying Action · Reason · Relevant function · Evidence · Confidence; includes red-team reconciliation and missing-signal WATCH follow-up actions.
- **Congress/publication card block** — for `congress`/`publication` signals: **Development** (e.g., FRONTIER4) · **Event** (e.g., ISTH 2026 abstract) · **Relationship** ("New evidence for existing development") · **Related evidence** (ClinicalTrials.gov · previous publication · congress presentation) — makes the Confluence/Lifecycle value visible to judges (MR-CGR-2).
- **Watch block** — stakeholder-defined watch rules render on the signal and on `/missing-signals`: source event · expected next event · monitoring window · responsible function · status (watching / new_evidence_detected / no_new_evidence / watch_expired / human_review_required) (MR-WATCH-2).
- **⛓ Evidence chain + meta block** — Sources (name, URL, date, excerpt, credibility), overall confidence + rationale, timestamp, **AI-generated label**, model_metadata (MR-SEC-1).
- **Watch view (`/watch/{entity}`)** — watchlist page: latest signals, lifecycle timeline, confluence, contradictions, missing signals, trend chart, role relevance, suggested actions, evidence (MR-WATCH-1).
- **Digest view (`/digest`)** — weekly digest with function filter tabs (six primary functions; MR-DIGEST-1); each item = Q1–Q4 mini-card + evidence + F-I-S label; export.
- **Athena view (`/athena`)** — structured grounded answers (Answer · Evidence · Sources · Confidence · Entities · Lifecycle · Contradicting evidence; insufficiency guardrail) (MR-ATHENA-1).

---

# 9. EVALUATION FRAMEWORK

## 9.1 Metrics, tests, and acceptance thresholds

| ID | Metric | Target | Test protocol | Dataset | Acceptance |
|---|---|---|---|---|---|
| EV-1 | Source-linked summaries | **100%** | Automated checker over all high-priority insights: source, URL, date, excerpt, evidence chain, confidence, AI-generated label present; no claim without evidence | Demo dataset + live/fallback run | 100% pass |
| EV-2 | Signal classification | **≥85% accuracy** | Classifier vs ground truth; report accuracy, per-class precision/recall, confusion matrix | 25 labelled examples (B.Pharm-reviewed) | Acc ≥85%; worst-class recall ≥0.6 |
| EV-2b | Entity extraction | **≥90%** | NER vs ground truth (drug/company/indication/phase) | 20 labelled texts | ≥90% exact-match accuracy |
| EV-3 | Top-signal discovery time | **≤5 min** | 100-signal deterministic week; task: identify top-5 priorities; measure TTD; same task vs manual browsing baseline | Synthetic week (100) | Median ≤5 min AND ≥50% faster than baseline |
| EV-4 | Confidential/patient data | **0 (evaluation target)** | Audit scan: no non-public data rows; dedicated PII/PHI detection + redaction layer unit tests (incl. reject/quarantine on low confidence); `.env` not in repo | Repo + DB scan | 0 violations (target) |
| EV-5 | Source-failure resilience | **Target: 100% graceful degradation across the defined failure-injection scenarios** | Kill each live source (simulate 429/500/timeout) → dashboard still renders from fallback (retry → cache → bronze → synthetic) | Synthetic + cache | 0 unhandled 5xx on tested scenarios; data freshness banner |
| EV-6 | Calibration improvement | **Agreement +≥10 pts** | Pre-calibration top-1 function agreement vs post-calibration on the 5-scenario set; confidence uplift on corrected routes | 5 calibration scenarios | Agreement 60% → ≥70%; uplift >0 |
| EV-7 | Four-Question completeness | **100%** | `test_four_question_completeness` over all HIGH+ cards | Demo + live/fallback | 100% pass |
| EV-8 | Confluence correctness | **≥4/5 scenarios** | Seeded confluence scenarios must produce one consolidated event (no duplicates, correct alert level) | 5 confluence scenarios | ≥4/5 match ground truth |
| EV-9 | Lifecycle correctness | **≥4/5 scenarios** | State transitions + expected-next match ground truth | 5 lifecycle scenarios | ≥4/5 |
| EV-10 | Red-team correctness | **≥4/5 scenarios** | Seeded contradiction pairs flagged with BOTH chains + human-review flag; no false positives on control pairs | 5 contradiction scenarios + 3 control pairs | ≥4/5; 0/3 controls flagged |
| EV-11 | Missing-signal correctness | **≥4/5 scenarios** | Expected-but-absent milestones fire with growing confidence; control (expected event arrived) does NOT fire | 5 missing scenarios + 3 controls | ≥4/5; 0/3 controls |
| EV-12 | Athena grounding | **100% grounded** | For each of ≥5 demo queries: answer cites retrieved signals; insufficiency query returns the guardrail text verbatim | 5 queries + 1 out-of-knowledge query | 100% grounded; guardrail shown |
| EV-13 | F-I-S label accuracy | **≥90%** | Predicted F-I-S label vs B.Pharm ground truth on the labelled set | 25 labelled examples | ≥90% agreement; speculation never marked fact |
| EV-14 | Action vocabulary conformance | **100%** | All Q4/digest actions belong to the controlled vocabulary and carry action/reason/function/evidence/confidence/human-review | All high-priority cards | 100% conformant |
| EV-15 | Domain classification | **≥85%** | disease/factor/inhibitor_status/population/modality vs B.Pharm ground truth on the labelled set; "haemophilia" alone → unknown (never guessed); indicator-expansion detection | 25 labelled examples + 7 domain cases | Acc ≥85%; no guessed unknown; expansion cases detected |
| EV-16 | Evidence maturity | **100%** | Every high-priority card carries source_type/source_authority/evidence_maturity/source_date; company announcement never labeled independently-verified | All high-priority cards | 100% present; hierarchy respected |
| EV-17 | Access separation | **100%** | Approval signal does not imply reimbursement/access; access subtypes recognised; jurisdiction recorded; approval≠access Red-Team checks (M/N/O) fire on seeded cases | 5 access scenarios + controls | 0 conflation; checks fire |
| EV-18 | Red-Team evidence checks A–S | **≥4/5 scenarios** | Seeded causality/denominator/population/surrogate/approval-access cases flagged with governing rule; controls not flagged | 7 domain cases + 3 controls | ≥4/5; 0/3 controls |
| EV-19 | Provider fallback chain | **All modes** | Failure-injection: Gemma unavailable → Grok used (xai/auto); Gemma+Grok unavailable → BART degraded factual output correctly labeled in UI (SRS FR-2.2.3B/C, AC-23) | 10 provider scenarios (TESTING.md Provider Fallback Tests) | Chain follows `LLM_PROVIDER`; degraded output labeled |
| EV-20 | External-LLM privacy gate | **100%** | PII/PHI or confidential content → external call blocked → local Gemma/BART/source-only (SRS FR-2.2.3D, AC-24); Grok schema- or semantically-invalid response rejected/retried/fallback (FR-2.2.3E, AC-25) | 5 privacy scenarios + controls | 0 external sends of blocked content; 0 unvalidated Grok outputs |

## 9.2 Curated evaluation dataset (`data/evaluation/`)

Deterministic, ground-truthed, realistic haemophilia scenarios. Each item: id, inputs (signals with source/url/date/text), expected outputs, and "tests mechanism: X" tag.

- **25 classification examples** — 7 signal types × realistic texts (incl. tricky ones: "gene therapy" in cardiac context → not haemophilia signal; "mim8" in engineering context → false positive test; congress + publication subtype examples per MR-CGR-1/MR-PUB-1).
- **7 deterministic domain-evaluation cases (v4.0, Master Plan §12.11)** — CASE 1 ("positive Phase 3" → endpoint/comparator/population/effect-size/follow-up/safety probes), CASE 2 (congress gene-therapy abstract → preliminary, linked to lifecycle, not regulatory confirmation), CASE 3 (safety event in positive programme → safety overrides, Safety/PV first, no causality), CASE 4 (approval → Regulatory, no inferred reimbursement/access), CASE 5 (one-country reimbursement restriction → Market Access, jurisdiction recorded, no global generalisation), CASE 6 (inhibitor-positive HA evidence → no generalisation to inhibitor-negative or HB), CASE 7 (congress + later publication same trial → linked, lifecycle continuation, no duplicate counting). Each carries the Red-Team checks (A–S) it must trigger.
- **5 confluence scenarios** — e.g., Hemgenix: ASH abstract + CSL press release + r/hemophilia post in 48h → ONE CRITICAL alert; plus a control (3 duplicate press wires ≠ confluence).
- **5 lifecycle scenarios** — e.g., mim8: announced(2024-05) → results_in(2026-01) → under_review(2026-03) → expected next: submission announced.
- **5 contradiction scenarios** — e.g., "sustained 3-yr FIX efficacy" (ASH) vs "declining FIX in subset" (real-world cohort); 3 control pairs (no contradiction).
- **5 missing-signal scenarios** — e.g., Roctavian follow-up silent 150d > max_lag → alert with confidence ≥0.7; 3 controls (event arrived → no alert).
- **5 calibration scenarios** — initial routing vs persona-correct routing; pre/post agreement recorded.
- **6 kickoff demo cases (newest kickoff, MR-ROUTE-1/MR-CGR-2/MR-WATCH-2):**
  1. Clinical trial update → Medical Affairs + Regulatory (routing seed check)
  2. Safety update → Safety/PV primary
  3. Access/reimbursement issue → Market Access primary
  4. New congress abstract for an existing trial → confluence links to existing development, lifecycle updated, Medical Affairs/Medical Communications routing
  5. New publication from an existing trial → confluence + evidence-chain update (never an isolated card)
  6. Stakeholder says "watch this competitor trial for future congress disclosures" → AI baseline → feedback → watch rule created → future congress signal linked to development → calibrated routing/action (BEFORE/AFTER)
- **5 ontology-QA items** — brand→molecule→company resolution incl. the C8 error class (fitusiran/Alhemo) as a "must not regress" test.
- **1 synthetic 100-signal week** — for the EV-3 discovery-time test and digest demos.

Every mechanism demo points at its scenario: *"This scenario was deliberately constructed to test mechanism X."*

## 9.3 Mechanism contracts (input / algorithm / output / acceptance / failure mode)

| Mechanism | Input | Algorithm | Output | Acceptance test | Failure mode |
|---|---|---|---|---|---|
| Confluence | Normalized signals w/ entity+type+timestamp | Group by entity in 48h; distinct signal_type ≥3 (config); severity = Σ(w_type × credibility) | One confluence event (level, signals, story) | EV-8 (≥4/5) | Degrade: no alert, signals still served (never blocks delivery) |
| Lifecycle | Historical signal log | FSM state machine + temporal linking + expected-next rules | Timeline (state, expected next, elapsed) | EV-9 (≥4/5) | Degrade: no timeline, card still renders |
| Red-Team | Claim pairs (same entity, 90d) | NLI entailment (BART-MNLI); contradiction >0.6 | Contradiction flag + dual evidence chains + human-review flag | EV-10 (≥4/5, 0/3 controls) | Degrade: no flag; flags never block delivery |
| Missing-Signal | Lifecycle state + rules | Lag check vs `max_lag_days`; confidence-by-silence | Missing alert + confidence + human review | EV-11 (≥4/5, 0/3 controls) | Degrade: no alert (advisory only) |
| Calibration | Ratings (1–5) per role | Weighted update on `scoring_weights`; audited | New weights + history row + confidence change | EV-6 (agreement uplift) | Skip if <MIN_FEEDBACK; degradation-safe (no pipeline crash on tested failures) |
| Temporal | Daily mention counts | 7d slope, Δslope, delta vs prev window | Velocity/acceleration/delta labels | Manual spot-check + EV-3 support | Degrade: badge hidden |
| Priority (explainability) | All mechanism outputs | Weighted factor composition | Priority 0–100 + factor checklist | EV-7 + manual inspection | Degrade: show factors, hide score |

---

# 10. HACKATHON RUBRIC TRACEABILITY MATRIX

"Complete" means **implemented + testable + demonstrable**. Status legend: **S** = specified in docs only (not yet implemented); **B** = will be built this cycle; **T** = test defined; **D** = demo beat defined. Today: everything is S (repository contains docs only); the roadmap (§11) moves rows to B+T+D. **Owner column per kickoff** — B.Pharm owners: Sanjana (Medical Affairs/priority/routing/actions), Ishaaq (treatment map/disease/inhibitor/lifecycle/signal types/expected-event rules), Usha (evidence quality/F-I-S/red-team/safety/access/human-review triggers); CSE owns all implementation.

### 10.1 Kickoff rubric dimensions → implementation → owner

| Dimension | Implementation | Document | Demo evidence | Metric | Owner |
|---|---|---|---|---|---|
| Problem understanding & haemophilia relevance | B.Pharm ontology + treatment map + disease/patient-type classification | SRS §2.2 (FR-2.2.5), ontology JSON | Card fields (disease/patient/company/asset) + ontology-QA row | EV-2b (extraction ≥90%) | Ishaaq |
| Domain classification (v4.0) | `DomainClassifier` (disease/factor/inhibitor/population/modality; never guess → unknown) | SRS FR-2.2.5A, SDD §2.4 | Card DOMAIN row + indicator-expansion detection | EV-15 ≥85% | Ishaaq + Usha |
| Clinical evidence + maturity (v4.0) | Nullable clinical-evidence fields + evidence-maturity ladder | SRS FR-2.2.5B/5C, SDD schema | Expandable evidence fields + maturity label | EV-16 100% | Usha + Sanjana |
| Access separation (v4.0) | Access as separate event; 8 access subtypes; jurisdiction | SRS FR-2.2.2, Master Plan §12.4 | Access cards on Market Access view | EV-17 0 conflation | Usha + Sanjana |
| Red-Team evidence checks A–S (v4.0) | Evidence-check suite on high-impact signals | SRS FR-2.3B.2A, Master Plan §12.7 | Red-team flags on signal card | EV-18 ≥4/5 | Usha |
| AI signal detection/classification | spaCy NER + zero-shot classification (11 types + 7 subtypes + F-I-S) | SRS FR-2.2.2/2.2.6 | Classification metric screen | EV-2 ≥85%, EV-13 ≥90% | Ishaaq + Usha (labels) |
| Source traceability | evidence_chain + bronze + sha256 + model_metadata | SRS FR-2.6.2, SDD §2.5 | Evidence chain on every card + audit export | EV-1 = 100% | Usha + CSE |
| Stakeholder calibration | feedback → weights → BEFORE/AFTER display | SRS FR-2.8, AC-14 | Calibration beat (priority/function/action change) | EV-6 agreement uplift ≥10 pts | Sanjana |
| Cross-functional usefulness | Six-function routing + function views + digest | SRS §2.4.2/2.5, MR-DIGEST-1 | Role switcher + six digest variants | Q3 badges on ≥90% of signals; 6 digest variants | Sanjana + CSE |
| Dashboard UX | Four-Question panels, F-I-S badge, WHY checklist | UI doc §2.2/§15 | Dashboard beat | EV-7 completeness 100%; <500ms | CSE |
| Compliance/safety/governance | WORM audit (traceability-analogy), dedicated PII/PHI layer, INTERNAL DECISION SUPPORT ONLY, F-I-S, evidence gate, risk register | SRS §3, docs/9_RISK_AND_GUARDRAILS.md | Guardrail slide + audit export | EV-4 = 0 (target); EV-1/12 | Usha |
| Scalability | One engine → matrix rows; APScheduler/Redis; roadmap | SDD §10, MR-ROLE-4 | Feasibility slide + load test | 1000 signals w/o degradation | CSE |

| Requirement (rubric/deliverable) | Current status | Gap | Required change | Implementation location | Demo evidence | Validation metric |
|---|---|---|---|---|---|---|
| Six function perspectives (one engine) | S (SRS/UI specify; Master Plan contradicted) | G1 | Scope docs updated; implement function views | `backend/services/scoring_service.py` (function_relevance), `frontend/app/[function]/` | Function switcher shows same event × 6 interpretations (+ extended) | MR-ROLE-1 acceptance; Q3 badges on ≥90% of signals |
| ≥3 live sources | S (AC-1 exists) | G2 | ClinicalTrials.gov connector live; adapter tiering | `backend/services/api_fetcher.py`, source registry | Footer: 3 LIVE ✓ sources | EV-5 + live fetch on demo day |
| Source-linked summaries | S (traceability designed) | G3/G7 | Enforce 100% on high-priority outputs | `services/traceability.py`, brief agent | Expand card → full evidence chain | EV-1 = 100% |
| Signal classification | S (AC-3) | G3 | Labelled dataset + metrics harness | `data/evaluation/classification/`, `tests/` | Metric screen: accuracy/precision/recall/matrix | EV-2 ≥85% |
| Top-signal discovery time | — | G3 | Test protocol + baseline | `tests/eval_discovery_time.py`, synthetic week | Live timed demo vs baseline | EV-3 ≤5 min |
| Zero confidential/patient data | S (guardrails exist) | G3 | Audit scan + scrubber test | `services/pii_scrubber.py`, `tests/` | Guardrail slide + scan output | EV-4 = 0 |
| Calibration improvement metric | S (loop exists) | G12 | Pre/post agreement harness | `tests/test_calibration_improvement.py` | Calibration beat: agreement 60→70%+ | EV-6 |
| Four-Question dashboard | S (UI doc complete) | G4 | Build + completeness checker | `frontend/app/(dashboard)/`, `components/QuestionPanel` | Dashboard beat | EV-7 = 100% |
| Signal cards (traceable) | S (UI doc §2.2) | — | Build | `components/SignalCard.tsx` | Card expansion in demo | EV-1/EV-7 |
| Five mechanisms | S (SDD services) | G11 | Per-mechanism contracts + tests | `services/*_engine.py`, `tests/` | Five mechanism beats | EV-8..11 |
| Weekly digest + function filters | — | G6 | Digest service on brief agent | `services/digest_service.py`, `/digest`, APScheduler job | Digest beat (function tabs) | EV-1 on digest items; function filter works |
| Ask Athena (grounded) | S (query_engine) | G8 | Structured schema + guardrail | `services/query_engine.py`, `/athena` | Athena beat + insufficiency demo | EV-12 |
| Explainability (priority WHY) | — | G7 | Factor decomposition | `services/scoring_service.py`, `PriorityExplanation` component | Card shows 91/100 + ✓ factors | EV-7 + manual |
| Temporal/change intelligence | S (schema exists) | G9 | Velocity/accel/delta layer | `services/temporal_patterns.py`, `trending_scores` | Q1 velocity badge + trend chart | EV-3 support; spot-check |
| Watchlists/entity focus | — | G10 | Watchlist API + watch view | `api/v1/watchlist.py`, `/watch/{entity}` | Watch mim8 view beat | Watch view returns all 9 panels |
| Alerts (confluence/missing/contradiction) | S (UI pages exist) | — | Build + seed demo | `/confluence`, `/red-team`, `/missing-signals` | Alert pages beat | EV-8/10/11 |
| WORM audit + provenance + model metadata | S (SDD §2.9) | G17 | model_metadata on outputs | `services/audit_logger.py`, traceability | Audit export button demo | EV-4 + export contains metadata |
| Curated evaluation dataset | — | G5 | Build ground-truthed set | `data/evaluation/` | "Scenario deliberately tests X" framing | EV-8..11 pass |
| Guardrails & risk summary | S (docs) | — | One-page risk/guardrail summary artifact | `docs/9_RISK_AND_GUARDRAILS.md` | Slide 7 | Checklist item |
| Architecture diagram | S (docs) | — | Corrected diagram (§4) | README/docs | Slide 4 | — |
| Sample data schema | S (SDD §2.5) | C3 | Fix 384-dim; add new tables | SDD + migrations | Slide 5/6 | DB migration applies cleanly |
| Source list | S (scattered) | G2 | Canonical source list w/ tiers | README Data Sources + §5 | Slide 3 | 3 LIVE verified |
| AI baseline vs calibrated example | S (loop exists) | G12 | Pre/post comparison view | `/calibration` page | Calibration beat | EV-6 |
| Classification validation | — | G3 | Metric harness | `tests/test_classification.py` | Metric screen | EV-2 |
| Source-linking validation | — | G3 | EV-1 checker | `tests/test_source_linking.py` | Metric screen | EV-1 |
| Discovery-time test | — | G3 | EV-3 harness | `tests/eval_discovery_time.py` | Timed demo | EV-3 |
| Demo dataset + script | S (scenario exists) | G5 | Curate + write 5-min script | `data/evaluation/`, `docs/10_DEMO_SCRIPT.md` | Full demo | §12 rehearsal passes |
| Offline fallback | S (500 dataset) | C7 | Deterministic + labeled | `data/synthetic/` | Kill-network demo | EV-5 |
| 2-page concept note | — | G19 | Draft from this plan | `docs/11_CONCEPT_NOTE.md` | Submit on time | Due ~Aug 14 (48h) |
| 5–7 slide deck | S (pitch doc) | — | Refresh to corrected scope | `docs/7_PITCH...` + slides | Final presentation | §13 checklist |
| Judging criteria (Innovation 25 / Technical 25 / Business 20 / Feasibility 15 / Presentation 15) | S | — | Evidence per criterion in deck + demo | Deck + demo script | Each demo beat maps to a criterion | §12 beat→criterion map |

---

# 11. REVISED IMPLEMENTATION ROADMAP (Phases 0–10, 4 weeks)

Kickoff = Aug 12, 2026. Team = 2 CSE + 3 B.Pharm. **Phase 0 completes by Aug 14 (concept note deadline).** Acceptance criteria are testable; each phase lists a demo outcome.

## PHASE 0 — Requirements alignment (Days 1–3, Week 1)
- **Objective:** Remove contradictions; freeze the corrected spec; everyone works from ONE plan.
- **Tasks:** Apply the §2 "Required change" edits to Master Plan §2/§3/§5, README, SDD (384-dim, drop Twitter), Doc 1 (500 vs 100, model defaults), CLAUDE.md (summarizer name), SRS ontology (C8). Draft + submit the 2-page concept note from §1–§5 of this plan. Baseline the rubric matrix (§10) with honest statuses.
- **Dependencies:** None (day-1 work; document-only).
- **Acceptance criteria:** No unresolved contradictions remain; concept note submitted; matrix baselined.
- **Demo outcome:** (not a demo phase) — judges see consistent narrative across all docs.

## PHASE 1 — Data / source layer (Week 1)
- **Objective:** 3 LIVE sources + bronze layer + bulletproof fallback; quota-aware design.
- **Tasks:** Docker Compose (backend, frontend, postgres+pgvector, redis — Celery removed; single in-process APScheduler; `/models` volume). Schema migrations via Alembic (incl. 384-dim fix + entity layer + watchlist + digest tables). PubMed + NewsAPI + ClinicalTrials.gov connectors (tenacity, rate limiting, incremental fetch). Bronze persistence + replay. Redis 2h cache. Synthetic fallback loader (500 curated, labeled). Adapter scaffolds for FDA/EMA (stubs returning synthetic, real calls behind flag).
- **Dependencies:** Phase 0 (schema frozen).
- **Acceptance criteria:** All 3 LIVE sources return data in a smoke test; kill each source → dashboard still serves (EV-5); bronze replay works.
- **Demo outcome:** Footer shows 3 LIVE ✓ sources; offline-mode switch works.

## PHASE 2A — Domain classification (Week 1–2, parallel with Phase 2)
- `services/domain_classifier.py` (disease/factor/inhibitor/population/modality; unknown-not-guess) + evidence-maturity ladder (FR-2.2.5A/5B/5C)
- Nullable clinical-evidence extraction (ABR, endpoints, sample size, follow-up, safety findings) — populated only when source-supported
- Acceptance: EV-15 (≥85% classification, no guessed unknown)

## PHASE 2 — Entity + ontology (Week 1–2)
- **Objective:** One normalized signal via spaCy + B.Pharm ontology; classification baseline.
- **Tasks:** spaCy `en_core_sci_md` NER; ontology JSON v2 (fix C8; add version + `updated_by`); ontology enrichment + validation layer; zero-shot classification (BART-MNLI) → 11 canonical types + 7 domain subtypes; F-I-S classification + evidence-sufficiency gate wiring (FR-2.2.6/2.2.7); batch summarization (BART-large-cnn) + **provider-agnostic reasoning layer** — `LLMProvider` interface (`LocalGemmaProvider`/`XAIProvider`/`BartDegradedProvider`), `LLM_PROVIDER=local|xai|auto` chain, external-LLM privacy gate (FR-2.2.3D), Grok JSON-Schema structured-output + semantic validation (FR-2.2.3E), per-output model metadata (FR-2.2.3F); build the 25-example classification + 20-example extraction labelled sets; **B.Pharm manual review of all labels.**
- **B.Pharm owners:** Ishaaq (treatment map, disease/inhibitor classification, lifecycle stages, signal types, expected-event rules) · Sanjana (signal importance, priority rules, function routing, suggested actions) · Usha (evidence quality, F-I-S rules, red-team questions, safety/access context, human-review triggers). Their output = the labelled evaluation dataset + domain rules.
- **Dependencies:** Phase 1 (signals flowing).
- **Acceptance criteria:** EV-2 ≥85% on the labelled set; EV-2b ≥90%; ontology QA row passes; false-positive cases (cardiac "gene therapy", engineering "mim8") classified correctly.
- **Demo outcome:** Entity tags resolve Hemlibra→emicizumab→Roche; metric screen shows the confusion matrix.

## PHASE 3 — Intelligence mechanisms (Week 2–3)
- **Objective:** All five mechanisms as tested components (MR-MECH-1), plus congress/publication linking and Watch-for-Next.
- **Tasks:** Confluence engine (3 types/48h + configurable patterns, EV-8) with **development-link decision** (MR-CGR-2); Lifecycle FSM + expected-next (EV-9) recording `event_type · event_date · development_id · source_id`; Red-Team NLI + dual chains + devil's-advocate note (EV-10); Missing-signal rules + confidence-by-silence (EV-11) + **stakeholder watch rules → `watch_items`** (MR-WATCH-2); congress/publication subtypes in classification (MR-CGR-1/MR-PUB-1); temporal layer — velocity/acceleration/delta (MR-TEMP-1); per-mechanism unit + scenario tests against `data/evaluation/` (incl. the 6 kickoff demo cases); mechanism endpoints (`/confluences`, `/lifecycles`, `/contradictions`, `/missing-signals`, `/watchlist`, `/trends`).
- **Dependencies:** Phase 2 (entities + classification).
- **Acceptance criteria:** EV-8/9/10/11 pass (≥4/5; 0/3 control false positives); congress abstract links into existing development (AC-15); watch rule transitions through statuses (AC-17); each mechanism has input/algorithm/output/acceptance/failure-mode documented in code or SDD.
- **Demo outcome:** The five-mechanism beats (confluence alert, mim8 timeline, Hemgenix contradiction, Roctavian silence) each run from a scenario that "deliberately tests" the mechanism; FRONTIER4 congress card + watch-rule beat.

## PHASE 4 — RAG / Ask Athena (Week 3)
- **Objective:** Grounded, structured, non-hallucinating answers.
- **Tasks:** pgvector 384-dim embeddings + hybrid search (semantic 0.6 / keyword 0.4, RRF); Athena structured schema (Answer/Evidence/Sources/Confidence/Entities/Lifecycle/Contradicting evidence); insufficiency guardrail verbatim ("Insufficient evidence to support an interpretation."); function-scoped answers; EV-12 tests.
- **Dependencies:** Phase 2 (entities/classification for retrieval quality); Phase 3 (lifecycle/contradiction context into answers).
- **Acceptance criteria:** EV-12 100% grounded; insufficiency query returns guardrail; answers cite supporting signals.
- **Demo outcome:** Athena beat + deliberate "out of knowledge" question shows the guardrail.

## PHASE 5 — Function routing + calibration (Week 3)
- **Objective:** Six function interpretations (+ extended) + measurable HITL improvement; relevance-based routing (MR-ROUTE-1).
- **Tasks:** Function scoring matrix ×8 rows — 6 primary + 2 extended (SRS §2.5 weights as seed); **`signal_routing` storage: primary_function + secondary_functions[] + function_relevance_scores + routing_reason + role-aware action (MR-ACT-2)**; per-function explanation/impact/action templates (one engine); calibration service (feedback → weights → history → audit) with **expanded scope: priority · routing · action · watch rules · relevance criteria**; watch-rule creation from stakeholder comments (MR-WATCH-2); simulated personas (six primary + extended); **pre/post agreement harness (EV-6)**; `/calibration` page with BEFORE/AFTER uplift display (incl. watch-rule creation).
- **Dependencies:** Phase 2 (classification feeds matrix); Phase 3 (mechanism flags feed routing).
- **Acceptance criteria:** EV-6 agreement uplift ≥10 pts; routing_reason present on ≥90% of high-priority signals (AC-16); confidence badges show "up from X% after calibration"; WORM rows written.
- **Demo outcome:** Calibration beat — persona rates a misrouted signal; Q3 badge visibly changes; a stakeholder watch comment creates a watch rule; metric screen shows pre/post agreement.

## PHASE 6 — Four-Question UI (Week 2–3, parallel)
- **Objective:** The decision interface with 100% completeness.
- **Tasks:** Four-Question panel grid (tints, Q1–Q4); signal cards with evidence chain + F-I-S badge + priority WHY block + completeness strip; function filter (six + extended); confluence/lifecycle/red-team/missing pages; trend chart; empty/error/loading states; **completeness checker (EV-7)**.
- **Dependencies:** APIs from Phases 1–3.
- **Acceptance criteria:** EV-7 100%; <500ms cached / <3s cold; WCAG AA.
- **Demo outcome:** Dashboard beat — one card answers Q1–Q4 with evidence.

## PHASE 7 — Digest / alerts / watchlists (Week 3–4)
- **Objective:** Beyond-dashboard intelligence delivery, reusing the same engine.
- **Tasks:** Weekly digest service (7d window → ranked developments → role-filtered variants, export Markdown/PDF); digest UI + APScheduler nightly generation job; watchlist API + `/watch/{entity}` view; notification/alerts badge for confluence/missing/contradiction; email-style digest preview.
- **Dependencies:** Phase 3 (mechanisms), Phase 5 (role actions), Phase 6 (UI patterns).
- **Acceptance criteria:** Digest items pass EV-1/EV-7 structure checks; each role filter returns role-specific actions; watch view returns all 9 panels for mim8.
- **Demo outcome:** Digest beat + watchlist beat.

## PHASE 8 — Evaluation (Week 4)
- **Objective:** Prove every metric; fix what fails.
- **Tasks:** Run full suite: EV-1..EV-14 (incl. F-I-S accuracy and action-vocabulary conformance) + EV-3 timed discovery protocol vs manual baseline; B.Pharm QA review of results; fix regressions; metric dashboard (accuracy, precision/recall, matrix, times, agreement uplift, completeness, grounding, F-I-S accuracy).
- **Dependencies:** Phases 1–7 complete.
- **Acceptance criteria:** All EV targets met (or documented, measured deviations with mitigation); metric screenshots for the deck.
- **Demo outcome:** Metric screen = quantified proof for judges.

## PHASE 9 — Demo hardening (Week 4)
- **Objective:** Bulletproof submission (Master Plan §8 preserved).
- **Tasks:** Offline rehearsal (network off → synthetic fallback); docker-compose up on clean machine; load test 1000 signals; **failure-injection tests** (API 429/500 → cache/bronze/synthetic; provider chain: Gemma unavailable → Grok in xai/auto → BART degraded factual mode; Grok timeout/rate-limit/schema-invalid → retry/fallback; privacy gate blocks external call on PII/confidential content → local Gemma/BART/source-only); recorded demo video; demo dataset finalized; risk/guardrail summary doc; demo script doc (§12 rehearsed); PII/secret scan; `pytest` green.
- **Dependencies:** Phase 8.
- **Acceptance criteria:** Rehearsal passes end-to-end twice; fallback works with 0 internet; video backup ready.
- **Demo outcome:** The §12 script runs end-to-end as rehearsed.

## PHASE 10 — Presentation (Week 4)
- **Objective:** 5–7 slide deck + 2-page note + submission package mapped to judging criteria.
- **Tasks:** Refresh pitch doc to corrected scope (six functions, 3 live sources, F-I-S, metrics, digest); slides: Problem → Gap → Approach (one engine, six functions) → Architecture → Demo → Metrics → Risk/Guardrails → Roadmap; assign B.Pharm/CSE speakers (Sanjana/Ishaaq/Usha domain beats); judge Q&A prep (Doc 6 Q&As refreshed); submission checklist (§13) completed.
- **Dependencies:** Phase 9.
- **Acceptance criteria:** Checklist 100% green; rehearsal with mock judges.
- **Demo outcome:** Final presentation.

---

# 12. DEMO SCRIPT (5 minutes, offline-safe)

Every beat maps to a judging criterion (Innovation I · Technical T · Business B · Feasibility F · Presentation P).

| Time | Beat | On screen | What to say (one line) | Criterion | Fallback if live APIs fail |
|---|---|---|---|---|---|
| 0:00–0:30 | Problem & principle | Title slide | "MetaRadar converts inbox noise into strategic signal — one engine, six function perspectives, every claim labeled Fact/Interpretation/Speculation and traceable." | P, I | — |
| 0:30–1:00 | Live sources | Dashboard footer + Q1 feed | "Three live sources — PubMed, NewsAPI, ClinicalTrials.gov — plus adapters and synthetic fallback; every payload audited in the bronze layer." | T, F | Show SYNTHETIC tier; say "network failed → graceful fallback to the synthetic tier (tested scenario)" (that IS the demo) |
| 1:00–1:30 | Confluence + card | CRITICAL confluence alert → expand card | "ASH abstract + CSL press release + patient forum within 48h = ONE development. The card answers Q1–Q4 with evidence, confidence, a FACT label, and a WHY checklist — Priority 91/100, here's why." | I, T | Seeded confluence scenario (labeled) |
| 1:30–2:00 | Five mechanisms | Lifecycle / Red-Team / Missing pages | "Where is mim8? results_in → next: submission. Is the evidence challenged? ASH 'sustained' vs real-world 'waning' — both chains shown, human review flagged. What should have happened? Roctavian follow-up silent 150 days — confidence grows with silence." | I | Seeded scenarios |
| 2:00–2:30 | Function model + routing | Function switcher on same event; routing reason shown | "Same evidence, six interpretations: Medical Affairs briefs, Regulatory watches labeling, Safety/PV flags a watch, Market Access re-runs HTA math, Medical Communications drafts the FAQ, Leadership sees escalation triggers — plus extended Commercial/R&D views. Routing is relevance-based — not every signal goes to everyone — with an explainable reason on every card." | B, I | Works offline |
| 2:30–3:00 | Watchlist + congress link | `/watch/mim8` → FRONTIER4 card | "One watch page for mim8: signals, lifecycle, confluence, contradictions, missing signals, trend, role relevance, actions, evidence. And the ISTH 2026 abstract for FRONTIER4 linked as NEW EVIDENCE into its existing development — one chain, not a new card." | B, I | Works offline; seeded scenarios |
| 3:00–3:30 | Ask Athena | `/athena` | "Grounded answer with evidence, sources, confidence, lifecycle context — and when the knowledge base can't answer: 'Insufficient evidence to support an interpretation.' No hallucination." | T, I | Works offline |
| 3:30–4:00 | Weekly digest | `/digest` with role tabs | "Same engine produces the weekly digest — Medical Affairs Digest, Regulatory Digest — not a second pipeline." | B, I | Works offline |
| 4:00–4:30 | Calibration + watch rule | Feedback → badge change + watch rule + metric | "A stakeholder says 'monitor this competitor trial for upcoming congress disclosures' → priority Medium→High, routing adds Medical Communications, action adds prepare internal review, and a WATCH rule is created — visible BEFORE/AFTER; when the next congress signal arrives it links into the development and the watch flips to 'new evidence detected'; agreement improved from 60% to 72% on our calibration set." | I, T | Persona seeding |
| 4:30–5:00 | Metrics + close | Metric screen + guardrail slide | "100% source-linked summaries, 86% classification accuracy with confusion matrix, top-signal discovery 2m40s vs 11m manual, zero private data, WORM audit with model metadata. MetaRadar is an intelligence layer, not a feed." | T, B, F | — |

**Live-failure rule:** if any LIVE source is down on stage, say so and show the footer tier label — the graceful-degradation demo is itself EV-5 proof (Technical criterion).

---

# 13. FINAL SUBMISSION CHECKLIST

Nothing counts as complete unless **implemented + testable + demonstrable**.

- [ ] **2-page concept note** — `docs/11_CONCEPT_NOTE.md` (due ~Aug 14; content sourced from this plan)
- [ ] **Working clickable prototype** — Docker Compose full stack (backend, frontend, postgres+pgvector, redis; single APScheduler)
- [ ] **Sample data schema** — migrations + `data/synthetic/` samples (384-dim vector, new tables)
- [ ] **Source list** — canonical LIVE/ADAPTER/SYNTHETIC list (README + §5)
- [ ] **Four-question dashboard** — Q1–Q4 panel grid, completeness strip, EV-7 green
- [ ] **Signal cards** — traceable evidence chain + priority WHY + AI-generated label
- [ ] **Six function perspectives** — function switcher shows same event × 6 interpretations (+ extended Commercial/R&D)
- [ ] **Alerts** — confluence / red-team / missing-signal pages + notification badge
- [ ] **Weekly intelligence digest** — role-filtered, exportable, same engine
- [ ] **Ask Athena** — grounded structured answers + insufficiency guardrail
- [ ] **AI baseline vs stakeholder-calibrated example** — pre/post agreement + confidence uplift shown
- [ ] **Classification validation** — 25-example labelled set; accuracy/precision/recall/confusion matrix ≥85%
- [ ] **Source-linking validation** — EV-1 100% checker green
- [ ] **Top-signal discovery-time test** — EV-3 ≤5 min vs manual baseline
- [ ] **Architecture diagram** — corrected (§4) in README/deck
- [ ] **Risk/guardrail summary** — `docs/9_RISK_AND_GUARDRAILS.md` (public/synthetic only; no patient data; no automated decisions; AI labeled; human review; evidence required; no secrets in repo)
- [ ] **Final 5–7 slide presentation** — refreshed pitch, criterion-mapped
- [ ] **Demo dataset** — curated evaluation set + 100-signal synthetic week (labeled)
- [ ] **Demo script** — §12 rehearsed twice + recorded video backup
- [ ] **Offline fallback** — network-off rehearsal passes; synthetic fallback available offline from the local 500-signal dataset

---

# WHAT CHANGED FROM THE CURRENT PLAN

Concrete changes only (no redesign, no feature-count inflation, all five mechanisms preserved):

1. **Function scope corrected:** "Medical-Affairs-only MVP" → **one engine, six primary functions** (Medical Affairs, Regulatory, Safety/PV, Market Access, Medical Communications, Leadership) **+ extended Commercial/R&D**. No six engines.
1a. **Relevance-based routing added (v1.2):** "Not every signal needs to go to everyone" — per-signal `primary_function` · `secondary_functions[]` · `function_relevance_score` · `routing_reason` · role-aware action; initial routing matrix is a seed, adjustable via calibration (MR-ROUTE-1, MR-ACT-2).
1b. **Congress + Publication as first-class signal types (v1.2):** canonical `signal_type` values with full subtype lists; congress/publication signals participate in all five mechanisms and link to existing developments (NEW EVIDENCE vs NEW DEVELOPMENT — one chain: trial → congress abstract → oral → poster → publication) (MR-CGR-1/2, MR-PUB-1).
1c. **Watch-for-Next added (v1.2):** stakeholder-defined WATCH RULES extend Missing-Signal — source_event → expected next event → monitoring window → responsible function → status (watching/new_evidence_detected/no_new_evidence/watch_expired/human_review_required); absence wording "No subsequent congress evidence observed during the configured monitoring window" (MR-WATCH-2).
1d. **Calibration scope expanded (v1.2):** priority · routing · action · watch rules · relevance criteria — demo shows BEFORE/AFTER incl. watch-rule creation.
1e. **6 kickoff demo cases added (v1.2):** clinical trial → MA+Regulatory; safety → Safety/PV; access → Market Access; congress abstract for existing trial → confluence+lifecycle; new publication from existing trial → evidence-chain update; stakeholder watch → watch rule → linked congress signal → calibrated routing.
2. **Data sources corrected:** PubMed + NewsAPI only → **≥3 genuinely live (added ClinicalTrials.gov)**, with FDA/EMA/congress/Reddit as **adapter-ready** and a **500-signal synthetic demo**; sources explicitly labeled LIVE / ADAPTER / SYNTHETIC; **Twitter removed**.
3. **Business metrics added** (were latency-only): 100% source-linked summaries; ≥85% classification with precision/recall/confusion matrix; ≤5-min top-signal discovery vs manual baseline; zero confidential/patient data; calibration agreement uplift ≥10 pts pre/post.
4. **Four-Question completeness test added:** 100% of high-priority cards carry Q1–Q4 + evidence + confidence + source + timestamp (EV-7, automated).
5. **Weekly Intelligence Digest added** (function-filtered — six primary functions), generated by the existing synthesis/brief agents — no second pipeline.
6. **Explainability added:** every priority score renders a "WHY?" factor checklist + confidence rationale + per-function factor breakdown.
7. **Curated deterministic evaluation dataset added:** 25 classification + 5×5 scenario sets (confluence/lifecycle/contradiction/missing/calibration) + ontology-QA rows + a 100-signal synthetic week, all with ground truth.
8. **Mechanisms formalized as testable components:** input / algorithm / output / acceptance test / failure mode per mechanism (EV-8..11).
9. **Ask Athena hardened:** mandatory structured answer schema (Answer/Evidence/Sources/Confidence/Entities/Lifecycle/Contradicting evidence) + verbatim insufficiency guardrail.
10. **Temporal/change intelligence added:** deterministic velocity/acceleration/delta layer (current state vs what changed), no predictive ML.
11. **Watchlist / entity focus added:** watch any drug/company/trial/indication → all nine intelligence panels, reusing existing infrastructure.
12. **Security strengthened:** `model_metadata` (model, version, task, config hash) on every AI output for full provenance reconstruction; WORM audit retained.
13. **Contradictions resolved:** 384-dim embeddings (not 768); Gemma 3 4B reasoning default local, optional hosted Grok, BART degraded factual mode only; confluence ≥3 types/48h (configurable); 500 curated synthetic; ontology factual errors flagged for B.Pharm QA (fitusiran ≠ Alhemo).
16. **Provider-agnostic reasoning layer added (v1.4):** `LLMProvider` interface + two output schemas (FULL INTELLIGENCE vs DEGRADED FACTUAL SUMMARY), `LLM_PROVIDER=local|xai|auto`, external-LLM privacy gate for hosted Grok, Grok structured-output + semantic validation, per-output model metadata (EV-19/EV-20; Master Plan v5.0 §13).
14. **Deliverable alignment added:** 20-item submission checklist + full rubric traceability matrix with honest statuses (nothing "complete" until implemented, tested, demonstrable).
15. **Roadmap restructured** into Phases 0–10 (with Phase 0 closing doc contradictions and hitting the 48h concept-note deadline) mapped onto the 4-week window, each phase with objective / tasks / dependencies / acceptance criteria / demo outcome.

**Unchanged (deliberately):** the five intelligence mechanisms, the four-question framework, the 10-node LangGraph pipeline, the tech stack (Next.js/FastAPI/LangGraph/PostgreSQL+pgvector/Redis/APScheduler/local AI — Celery removed per Master Plan §14.9), the Docker Compose deployment (4 services), the guardrails, the B.Pharm ontology ownership, and the 500-signal synthetic fallback.

---

*Corrected Unified Plan v1.5 · August 13, 2026 · Novo Nordisk GBS Hackathon 2026 — Problem Statement #3 · Team: MSRIT Aura Pharmers (2 CSE + 3 B.Pharm) · Team Lead: Sanjana Rathore B.*
