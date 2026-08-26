# MetaRadar: Master Plan & Canonical Specification (v5.0)

**Project:** MetaRadar — Near-Real-Time Competitive Intelligence Radar  
**Version:** 5.1 (Canonical Master Specification · B.Pharm Domain Research Integrated · Provider-Agnostic Reasoning Layer · Pre-Implementation Architecture Hardening)  
**Date:** August 13, 2026  
**Target Event:** Novo Nordisk GBS Hackathon 2026 (Problem Statement #3: "From Inbox Noise to Strategic Signal | Pilot Area: Haemophilia within Rare Disease")  
**Team:** Aura Pharmers — MS Ramaiah Institute of Technology (MSRIT), Cross-Disciplinary (2 CSE + 3 B.Pharm)  
**Team Lead:** Sanjana Rathore B.  
**Specification Status:** **SOLE AUTHORITATIVE MASTER PLAN** (All other documentation files are secondary historical references).

> **v4.0 Change Note (Aug 13, 2026):** This version integrates the B.Pharm domain research reports — Sanjana (Medical Affairs & prioritisation), Ishaaq (disease/inhibitor/modality classification & trial lifecycle), Usha (evidence quality, safety, access, Red-Team) — as **domain rules**, NOT as an architecture change. The 10-node LangGraph pipeline, five intelligence mechanisms, Four-Question UI, six primary functions, and stakeholder calibration loop are **unchanged**. What is added: canonical haemophilia classification fields (disease/factor/inhibitor/population/modality), nullable clinical-evidence fields, an evidence-maturity hierarchy, access as a separate intelligence event, 19 Red-Team evidence checks, research-informed routing rules mapped into the **six primary functions**, congress/publication lifecycle logic, Watch-for-Next, a triage (not clinical) priority model, and 7 deterministic evaluation cases. See §12.

> **v5.0 Change Note (Aug 13, 2026):** Final consistency + technical-accuracy pass. The reasoning layer becomes **provider-agnostic** — an internal detail of `node_synthesize` (NO new nodes, NO new agents, NO pipeline change): default **local Gemma 3 4B** (`LLM_PROVIDER=local`), **optional hosted xAI Grok** (`LLM_PROVIDER=xai` or `auto`) behind a mandatory external-LLM privacy gate, and **BART as degraded factual summary only** — never a reasoning-equivalent replacement. Adds the `LLMProvider` interface, two output schemas (FULL INTELLIGENCE vs DEGRADED FACTUAL SUMMARY), Grok JSON-Schema structured-output validation, per-output model metadata, and provider fallback acceptance tests. The 10-node pipeline, five mechanisms, six primary functions, and all §12 domain rules are unchanged. See §13.

> **v5.1 Change Note (Aug 13, 2026 — pre-implementation architecture hardening):** A final hardening pass over the ENTIRE project plan and documentation set, performed BEFORE implementation starts. **No redesign — scope, ten nodes, five mechanisms, six functions, calibration loop, Ask Athena, and the provider abstraction are all retained.** This version: (1) declares the concrete development/demo deployment target — **Gemma 3 4B Instruct Q4/int4 on the local GPU (NVIDIA RTX 3050, 4 GB VRAM)** with `LLM_DEVICE`/`LLM_DTYPE`/`MAX_CONTEXT_TOKENS`/`MAX_OUTPUT_TOKENS` configuration and a never-crash fallback chain (Gemma → Grok → BART degraded → source-grounded factual signal + human-review flag); (2) consolidates scheduling to **ONE scheduler (in-process APScheduler + Redis)** — Celery is removed for the hackathon architecture (§14.9); (3) hardens the **database entity model** (stable `source_id · company_id · asset_id · trial_id · development_id · event_id · publication_id · congress_event_id · regulatory_event_id · access_event_id`, immutable source provenance, canonical Signal schema, evidence relationships, Alembic migrations); (4) defines the **deterministic deduplication layer and source-independence model** BEFORE Confluence; (5) formally specifies the **LangGraph state contract** (state fields, reducers, explicit initial state, `node_calibrate → END`, recursion/failure limits); (6) adds the **domain configuration layer** (`config/haemophilia.yaml`) and ontology quality gate (verified mappings: fitusiran → Qfitlia · concizumab → Alhemo · marstacimab → Hympavzi); and (7) locks the operational surface — versioned `/api/v1/` endpoints, `health/ready|models|connectors`, configurable CORS, versioned scoring/calibration, safe Redis serialization + cache invalidation, observability (`run_id`/`signal_id`/`model_request_id`), idempotency, prompt versioning, evaluation/calibration datasets, Docker `/models` volume, and an honest implementation-status vocabulary. All decisions are specified in **§14** (they do not alter the §4 pipeline).

---

> **CANONICAL PRINCIPLE**  
> *"A conventional AI system summarizes documents. MetaRadar builds an evidence story around a development."*  
> MetaRadar converts fragmented public signals into evidence-backed developments and role-specific actions for Novo Nordisk teams.

---

## **1. PROBLEM**

Haemophilia care is experiencing its most dramatic market transition in decades — moving from lifelong intravenous factor replacement therapy to subcutaneous non-factor bispecific antibodies (emicizumab, concizumab, mim8) and single-administration AAV gene therapies (Hemgenix, Roctavian).

Critical competitive signals regarding this shift are scattered across disparate public sources: PubMed scientific publications, NewsAPI press releases, ClinicalTrials.gov registries, FDA/EMA regulatory announcements, congress abstracts (ASH, ISTH, WFH, EHA), and patient community forums (Reddit).

Pharma teams spend hours manually scouring inbox feeds and unlinked news dashboards. They receive fragmented document summaries rather than connected development timelines. No single role can manually synthesize cross-source signal convergence, track asset lifecycle progressions, detect contradicting trial evidence, flag missing expected filings, or adapt routing to expert feedback.

---

## **2. TARGET USER**

* **MVP Functions (Kickoff 2026 — all clearly supported in the prototype):** **Medical Affairs · Regulatory · Safety / Pharmacovigilance · Market Access · Medical Communications · Leadership** — routed from ONE intelligence engine (not six separate systems).
* **Extended Roles (retained, optional/future routing):** Commercial Strategy · Clinical R&D (kept in the routing matrix; toggled as extended roles, not demo-primary).
* **RELEVANCE-BASED ROUTING PRINCIPLE — *"Not every signal needs to go to everyone."*** MetaRadar first understands a signal, then determines which internal functions need to pay attention to it. The system does NOT broadcast every external update to every user. Flow: **External Signal → Understand → Classify → Determine relevance → Route to relevant function(s) → Generate role-specific explanation/action.**

### Initial Routing Matrix (seed only — never hard-coded as universal rules)

| Signal type (example) | Primary route | Secondary routes |
|---|---|---|
| Clinical trial update | Medical Affairs | Medical Communications · Regulatory |
| Safety signal | Safety / Pharmacovigilance | Medical Affairs · Regulatory (where relevant) |
| Access issue | Market Access | Medical Affairs (where relevant) |
| Regulatory decision | Regulatory | Medical Affairs · Leadership (where material) |
| Congress data | Medical Affairs | Medical Communications · Regulatory / Leadership (depending on relevance) |
| Publication | Medical Affairs | Medical Communications · other functions depending on content |

> These are the **initial routing matrix only**; all routes are adjustable through stakeholder calibration (mechanism 5). Adding a route never requires a new engine — it adjusts `scoring_weights` rows.
* **Primary Focus:** Monitoring clinical trials, publication readouts, congress abstracts, safety signals, and competitor drug positioning affecting Novo Nordisk's haemophilia portfolio (concizumab, mim8) against key market competitors (Roche's emicizumab, CSL Behring's Hemgenix, BioMarin's Roctavian, Sanofi's fitusiran, Pfizer's marstacimab).

---

## **3. MVP SCOPE**

To guarantee execution discipline within a 4-week hackathon window, the MVP scope is strictly locked to:

* **Six Functions, One Engine:** Medical Affairs · Regulatory · Safety / Pharmacovigilance · Market Access · Medical Communications · Leadership (Commercial & R&D retained as extended/future roles)
* **One Disease Area:** Haemophilia within Rare Disease (Haemophilia A & Haemophilia B)
* **Three Primary Live Sources:** NCBI PubMed (E-utilities) + NewsAPI + ClinicalTrials.gov (LIVE) · PMC full-text OPTIONAL/EXTENSION · FDA/EMA/Congress/Reddit ADAPTER-READY · 500-signal synthetic demo fallback (SYNTHETIC-DEMO)
* **Five Intelligence Mechanisms:**
  1. Confluence Detection
  2. Signal Lifecycle Tracking
  3. Red-Team Contradiction Analysis
  4. Missing-Signal Detection
  5. Stakeholder Calibration Prototype (HITL)
* **One UI Interface:** Four-Question Decision Interface (Q1: What changed? → Q2: Why matters? → Q3: Which function? → Q4: What action?)
* **One End-to-End Demo Story:** A haemophilia competitive development involving mim8 / emicizumab / Hemgenix durability data.
* **First-Class Signal Types:** **CONGRESS** (abstract · oral presentation · poster · new congress data · updated congress analysis · presentation of previously known data · congress-related safety/efficacy/PRO/mechanism-dosing data) and **PUBLICATION** (peer-reviewed · preprint · real-world evidence · post-hoc analysis · long-term follow-up · safety publication · PRO · mechanistic) are canonical `signal_type` values with subtypes — NOT generic news. Congress/publication signals connect to the development lifecycle: a congress presentation may be a **NEW DEVELOPMENT** or **NEW EVIDENCE ABOUT AN EXISTING DEVELOPMENT** (never automatically a new unrelated card).
* **Watch-for-Next:** Missing-Signal supports **stakeholder-defined WATCH RULES** (e.g., "monitor this competitor trial for subsequent congress disclosures") with statuses: Watching → New evidence detected / No new evidence / Watch expired / Human review required. Absence is reported as *"No subsequent congress evidence observed during the configured monitoring window"* — never as proof that no activity occurred.

*Everything else (additional roles, extra scrapers, custom LLM fine-tuning) is classified as Phase 2 future extensions.*

---

## **4. ARCHITECTURE**

MetaRadar implements a **10-Node LangGraph Workflow** orchestrating data flow from public ingestion to decision panels:

```text
                       PUBLIC EXTERNAL SIGNALS
        LIVE: PubMed/PMC · NewsAPI · ClinicalTrials.gov
        ADAPTER-READY: FDA · EMA · Congress (ASH/ISTH/WFH/EHA) · Reddit/advocacy
        SYNTHETIC-DEMO: 500 curated labelled haemophilia signals
                                ↓
                             INGESTION
                                ↓
                    VALIDATION (PII scrub · dedup · quality)
                                ↓
                  ENTITY + SIGNAL EXTRACTION (ontology)
                                ↓
                  NORMALIZED HAEMOPHILIA SIGNAL
        (disease · patient/inhibitor type · company · asset ·
         asset type · signal type · priority · impacted function)
                                ↓
                           ┌──────────────────┐
                           │   INTELLIGENCE   │
                           │     WORKFLOW     │
                           │                  │
                           │ 1. Confluence    │
                           │ 2. Lifecycle     │
                           │ 3. Red-Team      │
                           │ 4. Missing-Sig.  │
                           └────────┬─────────┘
                                    ↓
                  EVIDENCE + PRIORITY (sufficiency gate)
                                    ↓
           SYNTHESIS PROVIDER (Gemma GPU · Grok hosted · BART degraded)
                                    ↓
                  FACT / INTERPRETATION / SPECULATION
                                    ↓
                    FUNCTION ROUTING (6 functions + extended)
                                    ↓
                        FOUR QUESTIONS (Q1–Q4)
                                    ↓
         FUNCTION-SPECIFIC UI · ALERTS · WEEKLY DIGEST · ATHENA
                                    ↓
                   STAKEHOLDER CALIBRATION (HITL)
                                    ↓
            IMPROVED FUTURE ROUTING / PRIORITIZATION
```

### 10-Node LangGraph Execution Breakdown:
1. **`node_ingest`**: Runs all enabled `SourceConnector` adapters (PubMed, NewsAPI, ClinicalTrials.gov LIVE; FDA/EMA/Congress/Reddit adapter-ready; 500-signal synthetic fallback) through the **one shared connector interface (§14.3)** via `httpx` async clients. Every raw payload is persisted **verbatim** to `raw_signals_bronze` (immutable provenance: `source_id · external_id · url · publisher · published_at · retrieved_at · raw_content_hash · content_version`, §14.2) before any transformation.
2. **`node_validate`**: Filters short text (<50 chars), non-English data, and non-haemophilia scope. Runs the **deterministic deduplication layer** (stable fingerprints from PMID / NCT ID / FDA identifiers / congress abstract IDs, else normalized title+publisher+date+company+asset+URL — §14.4) and the **source-independence classification** (`source_class · publisher · syndication_group · parent_source_id`) BEFORE Confluence, so syndicated copies are never counted as independent signals. PII/PHI scrub runs before persistence.
3. **`node_nlp_extract`**: Extracts drug names, companies, indications, and clinical trial IDs using spaCy (`en_core_sci_md`).
4. **`node_ontology_enrich`**: Maps extracted entities against B.Pharm Haemophilia Ontology (Hemlibra $\rightarrow$ emicizumab $\rightarrow$ Roche $\rightarrow$ bispecific antibody).
5. **`node_confluence`**: Scans rolling 48-hour window for entity convergence across $\ge 3$ distinct signal types. **For congress/publication signals, first asks *"is this part of an existing development?"*** — if a matching `development_id` exists, the signal is linked into the existing development/evidence chain instead of becoming a new intelligence card (NEW EVIDENCE ABOUT EXISTING DEVELOPMENT vs NEW DEVELOPMENT).
6. **`node_lifecycle`**: Advances asset state machine (`announced → in_trial → interim_result → final_result → congress_publication → regulatory_development → approved → post_market | discontinued`). Every event records **`event_type` · `event_date` · `development_id` · `source_id`** so a trial → congress abstract → oral presentation → poster → publication chain stays ONE development timeline.
7. **`node_redteam`**: Runs pairwise NLI entailment/contradiction checks using local `facebook/bart-large-mnli`.
8. **`node_missing_signal`**: Evaluates FSM state against max lag rules to flag absent expected milestones. Supports **stakeholder-defined WATCH RULES** (source_event → expected/interesting next event → monitoring window → responsible function → status). Statuses: `watching` → `new_evidence_detected` / `no_new_evidence` / `watch_expired` / `human_review_required`. Wording is always *"Watch for…" / "Expected/possible next evidence" / "Not observed yet"* — never a claim that the event will happen.
9. **`node_synthesize`**: Runs the **evidence-sufficiency check** (retrieve evidence → sufficient? → YES: generate grounded interpretation; NO: restrict output to verified facts / "Insufficient evidence to support an interpretation" + request human review). Generates 1-sentence summaries (BART batch), **Fact / Interpretation / Speculation labels**, and Four-Question briefs via the **provider-agnostic reasoning layer (§13)** — default local Gemma 3 4B, optional hosted Grok, degraded BART factual mode — anchored strictly in source excerpts.
10. **`node_calibrate`**: Updates function-scoring weights based on stakeholder feedback ratings (`StakeholderCalibrationService`) → improved future routing/prioritization. **Calibration scope is not limited to priority** — stakeholders can influence priority, routing, actions, watch rules, and relevance criteria (BEFORE/AFTER shown in demo). **Explicit termination: `node_calibrate → END`** — the graph never relies on implicit termination.

**LangGraph State Contract (formal, §14.6):** The graph uses one explicit `MetaRadarState` (TypedDict) with declared fields, explicit **initial state**, and **typed reducers** — accumulating fields (`raw_signals`, `validated_signals`, `extracted_entities`, `ontology_entities`, `developments`, `scored_signals`, `confluent_stories`, `lifecycle_events`, `redteam_flags`, `missing_signals`, `role_briefs`, `calibration_feedback`, `model_metadata`, `errors`) use append/merge reducers so parallel connector nodes never overwrite each other; scalar fields use replacement semantics. Each node declares which fields it reads/writes; no node mutates arbitrary state. Recursion/failure limits are configured (e.g., `recursion_limit` and per-node error boundaries) so one source failure never kills the pipeline (see also §14.6).

### Technology Stack:
* **Frontend:** Next.js 15 (React 19, TypeScript, TailwindCSS 4, shadcn/ui)
* **Backend API:** FastAPI (Python 3.11 ASGI)
* **Workflow Orchestration:** LangGraph 0.1+ (10-node state graph)
* **Database & Vector Storage:** PostgreSQL 16 + `pgvector` extension
* **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (**384-dimensional vector embeddings**)
* **Reasoning Layer (provider-agnostic, §13):** **Default local provider `google/gemma-3-4b-it`** — Gemma 3 4B Instruct, a local instruction-tuned LLM (**Q4/int4-quantized, deployed on the local GPU — NVIDIA RTX 3050, 4 GB VRAM**; §14.1) driving narrative synthesis, Four-Question reasoning, AI-suggested actions, and Ask Athena; **optional hosted provider: xAI Grok API** (`LLM_PROVIDER=local|xai|auto`, mandatory external-LLM privacy gate, §13.5); and a safe **degraded mode: BART performs factual summarization only** when no reasoning provider is available — it is NOT a reasoning-equivalent replacement; no unsupported interpretation and no reasoning-based action recommendation are generated; degraded mode is clearly marked in the UI (*"AI reasoning unavailable — showing source-grounded factual summary"*) and human review applies where necessary. Model execution is configured via `LLM_DEVICE` (GPU/CPU/auto), `LLM_DTYPE` (e.g., int4), `MAX_CONTEXT_TOKENS`, and `MAX_OUTPUT_TOKENS` — **the system MUST NOT assume 4 GB VRAM guarantees successful inference** (model weights, KV cache, runtime overhead, and context length are treated as separate budgets; if Gemma cannot initialize/execute, the provider chain falls back per §13.6 and §14.1 — the application never crashes because Gemma does not fit).
* **Batch Summarizer:** `facebook/bart-large-cnn` — fast CPU seq2seq model for 1-sentence factual signal summaries (< 60s per 100 signals target); also the safe degraded fallback (factual summarization only).
* **Cache & Rate Limiting:** Redis 7 (2h TTL hot cache, quota-aware API rate limiting — NewsAPI Developer tier is 100 req/day; safe JSON serialization + versioned cache keys + invalidation rules, §14.8)
* **Scheduler (single):** **APScheduler (3.x stable), in-process with FastAPI** — the ONLY scheduling system (2-hour periodic fetch, nightly digest, on-demand recalibration). **Celery is deliberately NOT used in the hackathon architecture** (rationale + reintroduction path in §14.9). Heavy CPU/GPU-bound LangGraph runs are offloaded from the event loop via `asyncio`/thread/process execution, not via a second scheduling system.

---

## **5. DATA SOURCES**

### Live Ingestion Sources (MVP):
1. **NCBI PubMed / E-utilities:** PubMed literature retrieval for clinical literature, Phase 2/3 trial readouts, academic reviews (keyless REST via NCBI E-utilities). **PubMed Central (PMC) APIs/services for eligible full-text content are an OPTIONAL/EXTENSION** — not the same endpoint as PubMed literature retrieval and not claimed as implemented unless they are.
2. **NewsAPI:** Industry news, press releases, competitor corporate announcements (**Developer/free tier: 100 requests/day**, development/testing use only, articles delayed up to 24 hours — NOT real-time, NOT for production/internal deployment; official pricing https://newsapi.org/pricing). Quota-aware connector; on exhaustion fall back to Redis cache → bronze DB → synthetic dataset.

### System Data Polling & Availability:
* **Source Polling Frequency:** Every 2 hours (via the single in-process **APScheduler**; §14.9).
* **Dashboard Availability:** Continuously available near-real-time radar.
* **Source Freshness Classes (honest labeling, §14.3):** each connector is labelled `real_time` · `near_real_time` · `delayed` · `batch` · `adapter_ready` · `synthetic`. The dashboard shows freshness honestly (e.g., NewsAPI = `delayed` — Developer tier articles are up to 24h old; PubMed = `delayed`/`batch`; ClinicalTrials.gov = `near_real_time`). No connector is blanket-labelled "real-time".

### Synthetic Demo Fallback:
* **500-Signal Pre-Curated Synthetic Dataset:** Local JSON fallback designed to keep the offline demo executable when public APIs experience rate limits or network failures (an engineering target exercised in rehearsal — not an absolute guarantee).

---

## **6. INTELLIGENCE MECHANISMS (COMPUTATIONS & ALGORITHMS)**

MetaRadar executes five distinct mathematical and logical computations on every incoming signal cluster:

| Mechanism | Input Data | Computation & Algorithm | Output Product |
|---|---|---|---|
| **1. Confluence** | Incoming raw signals | Group by normalized Entity ID over rolling 48h window. Check if distinct `signal_type` count $\ge 3$. Aggregate severity $S = \sum (w_{type} \times \text{credibility})$. **For congress/publication signals: match `development_id` first — if the signal belongs to an existing development, it becomes a new evidence event in that chain, NOT a new card.** | **Convergence Alert** (e.g. ASH + Press Release + Patient Forum in 48h) + **development-link decision** (new development vs new evidence about existing development) |
| **2. Lifecycle** | Historical signal logs | FSM State Machine: `announced → in_trial → interim_result → final_result → congress_publication → regulatory_development → approved → post_market \| discontinued`. Chronological event ordering + expected event calculation. Each event stores `event_type · event_date · development_id · source_id`. | **Development Timeline** (Current state + expected next milestone + elapsed days; trial → congress abstract → oral → poster → publication stays one chain) |
| **3. Red-Team** | Claim pairs | Zero-shot NLI entailment check using local `facebook/bart-large-mnli`. Evaluate claim pairs linked to entity in 90d window. Flag `contradiction` if score $> 0.60$. | **Challenge Evidence** (Side-by-side evidence chains + devil's advocate review note) |
| **4. Missing-Signal** | Lifecycle FSM state + stakeholder watch rules | Rule evaluation: if current state is $S_i$ and $\Delta t_{\text{last\_signal}} > t_{\text{max\_lag}}$, create a **WATCH item** (monitoring signal, NOT a claim that the event will happen) with confidence $C = \min(0.40 + 0.002 \times \Delta t_{\text{silence}}, 0.95)$. Supports **stakeholder-defined WATCH RULES** (e.g., competitor trial → congress disclosure; statuses: watching / new_evidence_detected / no_new_evidence / watch_expired / human_review_required). Absence wording: *"No subsequent congress evidence observed during the configured monitoring window."* | **Missing-Event WATCH Alert + Watch-for-Next item** (labeled monitoring signal; human review required) |
| **5. Stakeholder Calibration** | Persona feedback ratings (1–5) | Online gradient update on function scoring weights $\mathbf{W}_{role}$ processed by `StakeholderCalibrationService`, logged in WORM `calibration_history`. **Scope: priority, routing, actions, watch rules, and relevance criteria — feedback must visibly change output (BEFORE/AFTER).** | **Revised Relevance Score + revised routing/action/watch** (Dynamic role-routing weight adjustment) |

---

## **7. USER INTERFACE (DECISION-FIRST LAYOUT)**

The UI is strictly subordinate to the intelligence. Rather than presenting raw news lists, the interface centers on the **High-Priority Development Card**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ HIGH-PRIORITY DEVELOPMENT                                              │
│ mim8 Competitive Landscape Shift                                       │
│ Overall Confidence: 87% | Confluence Level: CRITICAL | Evidence: FACT  │
├────────────────────────────────────────────────────────────────────────┤
│ Q1 — WHAT CHANGED?                                                     │
│ Hemgenix 3-year durability data published at ASH 2026 alongside        │
│ CSL Behring press release and patient forum discussion.                │
├────────────────────────────────────────────────────────────────────────┤
│ Q2 — WHY DOES IT MATTER?                                               │
│ Challenges mim8 subcutaneous factor replacement positioning.           │
│ Contrasting real-world cohort data flags declining factor IX levels.   │
├────────────────────────────────────────────────────────────────────────┤
│ Q3 — WHICH FUNCTION SHOULD REVIEW IT?                                  │
│ Medical Affairs 94% · Regulatory 71% · Safety/PV 52% (calibrated)      │
│ ROUTING REASON: "Clinical efficacy/safety data with implications for    │
│ scientific understanding and future regulatory review."               │
├────────────────────────────────────────────────────────────────────────┤
│ Q4 — WHAT INTERNAL ACTION MAY BE REQUIRED?                             │
│ Suggested — Medical Affairs to draft response on gene therapy          │
│ durability vs subcutaneous prophylaxis. (Human review required).      │
├────────────────────────────────────────────────────────────────────────┤
│ EVIDENCE CHAIN (Traceable)                                             │
│ ├─ PubMed: "3-Year Hemgenix Durability Analysis" [View Source]         │
│ ├─ NewsAPI: CSL Behring Press Announcement [View Source]               │
│ └─ Reddit: Patient Community Forum Narrative [View Source]             │
├────────────────────────────────────────────────────────────────────────┤
│ CONGRESS/PUBLICATION CONNECTION (if congress or publication signal)    │
│ Development: FRONTIER4 · Event: ISTH 2026 abstract                     │
│ Relationship: "New evidence for existing development"                 │
│ Related evidence: ClinicalTrials.gov · previous publication ·          │
│ congress presentation                                                  │
├────────────────────────────────────────────────────────────────────────┤
│ CHALLENGE EVIDENCE (Red-Team)                                          │
│ ⚠️ Contradiction: ASH trial durability vs Real-world cohort waning     │
├────────────────────────────────────────────────────────────────────────┤
│ LIFECYCLE TIMELINE                                                     │
│ ● Phase 3 Readout ──● Results Published ──○ Regulatory Submission      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## **8. IMPLEMENTATION TIMELINE (REVISED 4-WEEK PLAN)**

### Week 1 — Foundation (Make Live Signals Appear)
* **Engineering Tasks:** Docker Compose environment setup (FastAPI, Next.js 15, PostgreSQL 16 + pgvector, Redis 7 — 4 services; model weights in a mounted `/models` volume, §14.14). Implement NCBI PubMed (E-utilities) & NewsAPI connectors via the shared `SourceConnector` interface (`httpx` async + `tenacity`). **Alembic-managed schema migrations** creating the canonical entity layer (§14.2): `sources · companies · assets · trials · developments · events · evidence · signals · calibration · audit` (no `drop_all()`/`create_all()` for normal development).
* **Milestone:** Live signals appear on basic dashboard screen.

### Week 2 — Intelligence Core (Connect Signals into Stories)
* **Engineering Tasks:** spaCy NER entity extraction (`en_core_sci_md`) + B.Pharm Haemophilia Ontology integration. Deduplication via fuzzy title matching. Implement Confluence Detection (48h rolling window) and Lifecycle FSM state tracking. Four-Question UI panel component rendering.
* **Milestone:** Multiple raw documents become one unified development story.

### Week 3 — Differentiation (Add Challenge & Calibration)
* **Engineering Tasks:** Integrate Red-Team Contradiction engine using `facebook/bart-large-mnli` zero-shot NLI. Implement Missing-Signal Detection state engine with silence confidence scoring. Build `StakeholderCalibrationService` for HITL feedback and weight recalibration.
* **Milestone:** System challenges, tracks silence, and prioritizes intelligence based on user feedback.

### Week 4 — Hardening & Rehearsal (Harden, Don't Expand)
* **Engineering Tasks:** Comprehensive fallback testing (Redis cache $\rightarrow$ Bronze DB $\rightarrow$ 500-signal synthetic dataset). Error handling, log verification, performance tuning (<500ms cached dashboard response). UI polish, citation link checks, **role-filtered weekly digest generation**, **labelled evaluation dataset run (≥85% classification, 100% source-linked summaries)**, end-to-end demo rehearsal.
* **Milestone:** Bulletproof submission package (Docker Compose, presentation deck, 2-page report, recorded demo video).

---

## **9. DEMO SCENARIO (THE HEMGENIX 3-YEAR DURABILITY SHIFT)**

The presentation demo tells **one continuous haemophilia story**:

1. **Signals Arrive:** Three signals enter the system (PubMed paper on Hemgenix 3-year data + CSL Behring press release + Reddit patient forum post).
2. **Confluence Connects:** Confluence Engine merges all three into one High-Confluence Strategic Alert.
3. **Lifecycle Tracks:** Lifecycle Tracker places the update at *Post-Market Durability Tracking* on the timeline.
4. **Red-Team Challenges:** Red-Team Agent flags contradicting evidence between trial durability claims and real-world cohort waning.
5. **Missing-Signal Warns:** Missing-Signal Detector flags an expected competitor regulatory submission that remains silent past 120 days.
6. **Watch-for-Next (stakeholder-defined):** A stakeholder watches the competitor Phase III programme for upcoming congress disclosures; when the next congress abstract arrives it links into the SAME development chain (confluence), and the watch status flips to "New evidence detected" and notifies Medical Affairs + Medical Communications.
7. **Four Questions Frame:** Q1–Q4 panels summarize the situation, show the routing reason ("Clinical efficacy/safety data with implications for scientific understanding and future regulatory review"), tag Medical Affairs at 94% confidence, and present a suggested briefing action.
8. **Stakeholder Prototype Calibrates:** A Medical Affairs persona submits feedback, `StakeholderCalibrationService` updates scoring weights, and future routing confidence visibly recalibrates live — with a visible BEFORE/AFTER comparison (priority/function/action/watch).

---

## **10. VALIDATION CRITERIA (MEASURABLE TARGETS)**

To maintain absolute technical honesty, system performance is evaluated strictly against verifiable engineering targets AND business-level success metrics:

**Engineering targets (retained):**
* **Dashboard Response Time:** $< 500\text{ ms}$ for cached signal views.
* **Ingestion Resilience (target):** graceful degradation during **tested** connector/model failures when external APIs fail or return 429/500 errors — verified by failure-injection tests, not claimed as an untested guarantee.
* **Data Replayability:** $100\%$ verbatim raw payload persistence in `raw_signals_bronze` before processing.
* **Traceability:** $100\%$ of generated AI insights contain valid source links, timestamps, and quotes.
* **Testing:** Automated unit & integration tests covering critical pipeline nodes (ingestion, entity extraction, confluence clustering, calibration service).
* **LLM Provider Fallback (target):** the provider chain is exercised with failure-injection tests — Gemma unavailable → Grok (in `xai`/`auto` modes); Grok unavailable → BART degraded factual mode; external call blocked by the privacy gate → local Gemma / BART / source-only display; schema-invalid or semantically invalid Grok output → retry/fallback. These are acceptance targets, not guarantees (§13.6).

**The Five Hackathon Success Metrics (explicit, non-negotiable):**
1. **Source-linked summaries = 100%** — every high-priority AI insight carries source name, URL, publication date, source type, excerpt, evidence level, confidence, timestamp, AI-generated label.
2. **Classification accuracy ≥ 85%** — on a B.Pharm-labelled validation dataset (disease · patient type · signal type · priority · impacted function), reporting accuracy, precision, recall, confusion matrix.
3. **Top-signal discovery time ≤ 5 minutes** — reproducible test on a 100-signal weekly batch vs a manual browsing baseline.
4. **Confidential / patient data = 0 (evaluation target)** — public and synthetic data only; dedicated PII/PHI detection + redaction layer before persistence (spaCy NER contributes to entity detection but is not a guaranteed scrubber; low-confidence content is rejected/quarantined); audit scan. This is an evaluation target, not a mathematical guarantee.
5. **Stakeholder-calibrated improvement** — measurable routing/priority improvement before vs after feedback (e.g., agreement uplift ≥ 10 points).

**F-I-S compliance:** 100% of high-priority outputs carry a Fact / Interpretation / Speculation label; speculation is never presented as fact; insufficient evidence yields "Insufficient evidence to support an interpretation."

**Routing explainability:** every high-priority signal carries `primary_function` + `secondary_functions[]` + per-function relevance scores + a **routing reason** ("why this function, why now"); routing is never a bare badge. Initial routing matrix is seed-only; calibration adjusts it (mechanism 5).

**Congress/Publication linking:** congress and publication signals participate in Confluence, Lifecycle, Red-Team, priority scoring, function routing, the evidence chain, and stakeholder calibration — they are first-class signal types, not generic news. A congress abstract for an existing trial must attach to that trial's development chain (NEW EVIDENCE ABOUT EXISTING DEVELOPMENT) rather than spawn an unrelated card.

**Watch-for-Next coverage:** the demo dataset includes the watch-rule scenario ("watch this competitor trial for future congress disclosures") with the full flow: trial detected → watch created → congress signal detected → linked to existing development → functions notified; plus the no-evidence variant returning *"No subsequent congress evidence observed during the configured monitoring window."*

---

## **11. KNOWN LIMITATIONS**

1. **Public API Quotas:** NewsAPI Developer/free tier is capped at **100 requests/day** (development/testing use only; articles delayed up to 24h; not for production/internal deployment). Mitigated by quota-aware connectors, Redis caching, and 2-hour fetch polling; on exhaustion fall back to bronze DB / synthetic dataset. (Official pricing: https://newsapi.org/pricing.)
2. **Model Capabilities:** The local reasoning model (`google/gemma-3-4b-it`, Q4/int4) runs on the **local GPU (NVIDIA RTX 3050, 4 GB VRAM)**; BART (batch summarizer + degraded fallback), BART-MNLI (NLI), spaCy (NER), and MiniLM (embeddings) run on CPU. **4 GB VRAM is NOT assumed to guarantee successful inference** — model weights (~2.6 GB Q4), KV cache, runtime overhead, and context length are budgeted separately (max context/output tokens are configurable). If Gemma cannot initialize or execute, the chain falls back: **Gemma → Grok (if configured & privacy-gated) → BART degraded factual → source-grounded factual signal + human-review flag** — the application never crashes because a model does not fit (§13.6, §14.1). Reasoning depth remains bounded on constrained hardware compared to commercial LLMs; an **optional hosted Grok provider** (`LLM_PROVIDER=xai|auto`) can supplement reasoning where available, gated by the external-LLM privacy gate (§13.5). When no reasoning provider is available the system enters **degraded mode — BART factual summarization only** (no reasoning-equivalent output).
3. **Stakeholder Feedback Scope:** True organizational feedback across global pharma teams is unavailable in a hackathon setting; the calibration loop is demonstrated using persona-driven simulated feedback.
4. **Absence Alerting Precision:** Missing-signal detection relies on rule-based time lag thresholds ($t_{\text{max\_lag}}$); abnormal market delays may trigger false-positive alerts, which are strictly gated behind mandatory human review.

---

## **12. B.PHARM DOMAIN RESEARCH INTEGRATION (v4.0 — CANONICAL DOMAIN RULES)**

This section converts the B.Pharm research reports (Sanjana · Ishaaq · Usha) into concrete MetaRadar rules. It does **not** change the architecture (§4): everything below runs inside the existing 10-node pipeline as extraction fields, evidence assessment, Confluence/Lifecycle/Red-Team/Missing-Signal rules, priority inputs, and routing adjustments. **No new engines are created.**

### 12.1 Haemophilia Domain Classification (mandatory fields)

Every normalized signal SHALL carry the following canonical domain fields. **Do not infer a field when evidence is insufficient — set it to `unknown`.** Entity resolution SHALL attempt source, product, trial ID, and context before assigning A/B.

| Field | Allowed values | Extraction rule |
|---|---|---|
| `disease` | `haemophilia_a` · `haemophilia_b` · `both` · `unknown` | FVIII/F8 terms → A; FIX/F9 terms → B; explicit "A and B" → both; bare "haemophilia" → **unknown** until entity resolution (product/trial/context) succeeds |
| `factor` | `fviii` · `fix` · `unknown` | Factor VIII / F8 → fviii; Factor IX / F9 → fix; else unknown |
| `inhibitor_status` | `with_inhibitor` · `without_inhibitor` · `mixed` · `unknown` | "FVIII inhibitor" / "FIX inhibitor" / "neutralising antibody" / "inhibitor-positive" → with; explicit "no/without inhibitors" → without; both → mixed; absent → **unknown** (never assume) |
| `population` | `adult` · `adolescent` · `child` · `other_or_unknown` | Where available (age words, trial eligibility) |
| `therapy_modality` | `factor_replacement` · `extended_half_life_factor` · `non_factor` · `bispecific_antibody` · `sirna` · `gene_therapy` · `aav_gene_therapy` · `lentiviral` · `gene_editing` · `other` | Modality classifier per Ishaaq rules (FVIII/FIX protein → factor; antibody/TFPI/siRNA/pathway modifier → non-factor; AAV/lentiviral/transgene/editing → gene therapy) |

**Why inhibitor status is a core segmentation variable:** Inhibitor status materially changes treatment context and competitive relevance (separate WFH guidance for inhibitors, outcome assessment, and AAV gene therapy — https://guidelines.wfh.org/guidelines/). A therapy indicated for inhibitor patients occupies a distinct niche; indication expansion **across** the inhibitor boundary (e.g., Hemlibra, Alhemo, Hympavzi) is a high-value `INDICATION_EXPANSION` signal. Do not generalise evidence between inhibitor-positive and inhibitor-negative populations (Red-Team check D, §12.7).

### 12.2 Clinical Evidence Fields (nullable)

For clinical/trial signals the system SHALL populate the following **nullable** fields only when supported by the source — never forced, never fabricated:

`trial_id` · `trial_phase` · `study_design` · `population` · `comparator` · `primary_endpoint` · `secondary_endpoints` · `abr` · `bleeding_outcome` · `joint_or_target_joint_outcome` · `patient_reported_outcome` · `quality_of_life_outcome` · `treatment_burden` · `follow_up_duration` · `sample_size` · `safety_findings` · `effect_size` · `confidence_interval` · `p_value` · `interim_or_final` · `evidence_maturity`.

Extraction implications (Sanjana): capture endpoint **definitions** (e.g., treated vs all-bleed ABR — Red-Team check E), comparator, effect size, CI/p-value, population, regimen, and safety findings rather than just "positive trial". Capture PROs, QoL, pain, physical function, joint outcomes, and treatment burden as separate fields (never buried in a summary).

### 12.3 Evidence Maturity Hierarchy

Every important signal SHALL carry `source_type` · `source_authority` · `evidence_maturity` · `source_date`. Evidence maturity is an **evidence-context indicator, NOT a truth ranking** — a congress abstract can be extremely important but preliminary; a company announcement can be an important early signal but is not independently verified evidence.

| Maturity tier | Source types |
|---|---|
| **VERY HIGH** | Regulatory decision / official regulatory assessment |
| **HIGH** | Peer-reviewed publication · ClinicalTrials.gov structured update/result |
| **MEDIUM/HIGH** | Congress abstract/presentation |
| **MEDIUM** | Official company announcement |
| **LOWER** | Secondary media / commentary |

Confidence starts lower for preliminary evidence and is upgraded only when peer-reviewed publication, registry results, or regulatory documentation confirm/qualify the finding. Congress evidence is ingested as provisional, never discarded (low-volume field — it may precede formal literature).

### 12.4 Access Is a Separate Intelligence Event

**Approval ≠ Reimbursement ≠ Commercial availability ≠ Actual patient access.** These distinctions SHALL appear in the Red-Team documentation (§12.7 checks M/N/O) and drive a dedicated access signal class. The system SHALL NOT merge regulatory approval and access.

**Access signal types (new canonical values for `signal_type = access`):**
- `ACCESS_REIMBURSEMENT_EVENT` — positive/negative/conditional/restricted payer or HTA decision
- `RESTRICTED_REIMBURSEMENT` — eligibility narrowed by severity/age/treatment history
- `SUPPLY_ACCESS_RISK` — shortage, manufacturing, distribution, treatment-interruption risk
- `GEOGRAPHIC_ACCESS_GAP` — material variation between countries/regions
- `BUDGET_IMPACT_SIGNAL` — major economic consequences for payers
- `OUTCOME_BASED_ACCESS_MODEL` — payment linked to performance/durability
- `REAL_WORLD_ACCESS_GAP` — approved treatment not reaching intended patients (affordability/infrastructure/system barriers)
- `ACCESS_SUPPORT` — manufacturer patient-support programme (kept distinct from reimbursement)

**Access fields:** `country` · `jurisdiction` · `effective_date` · `expiry_or_review_date` · `product` · `indication` · `eligible_population` · `inhibitor_status` (where relevant) · `coverage_status` · `restrictions` · `prior_authorisation` · `specialist_centre_requirements` · `source_authority` · `intended_vs_actual_access`.

### 12.5 Function Routing (research-informed, mapped into the six PRIMARY functions)

Routing rules below replace/supplement the §2 seed matrix. **The six primary functions remain: Medical Affairs · Regulatory · Safety/Pharmacovigilance · Market Access/Patient Access · Medical Communications · Leadership.** Commercial, R&D, Clinical Development, Competitive Intelligence, Strategy, etc. exist only as **extended/secondary stakeholders** where appropriate — never as replacements. The student research routing tables (R&D/CI/Strategy-led) are **domain reference only** and are re-mapped into the six primary functions as follows:

| Signal type | Primary function | Secondary functions (from six) |
|---|---|---|
| Major clinical efficacy result | Medical Affairs | Medical Communications · Leadership (where material) |
| Serious safety signal | Safety/PV | Medical Affairs · Regulatory (where relevant) |
| Regulatory approval/rejection/label change | Regulatory | Medical Affairs · Market Access · Leadership (where material) |
| New patient outcome / QoL evidence | Medical Affairs | Market Access · Medical Communications (where relevant) |
| New congress data | Medical Affairs | Medical Communications · Regulatory / Leadership (depending on content) |
| Pricing / reimbursement / access event | Market Access | Leadership · Medical Affairs (where relevant) |
| Major competitor therapy/development | Medical Affairs | Leadership (+ extended: Competitive Intelligence / R&D stakeholder where appropriate) |
| Trial lifecycle change | Medical Affairs | Regulatory · Leadership (depending on significance) |
| Guideline change | Medical Affairs | Regulatory · Market Access |
| Serious thromboembolic/TMA signal | Safety/PV | Medical Affairs · Regulatory |
| Gene-therapy durability/safety data | Medical Affairs | Medical Communications · Safety/PV (durability/late-safety aspects) |

Output per signal: `primary_function` · `secondary_functions[]` · `function_relevance_scores` · `routing_reason`. Never broadcast every signal to every function.

### 12.6 Congress / Publication Lifecycle Logic (major requirement)

Congress and publication signals SHALL NOT automatically become independent intelligence items. Lifecycle chain:

```text
Clinical trial → Congress abstract/presentation → Company announcement → Peer-reviewed publication → Regulatory event → Long-term follow-up
```

Connect via `development_id` · `trial_id` · `product_id` · `source_id` · `event_id`. Decision logic uses a **tri-state link decision** — do not force a link when evidence is insufficient:
- Same trial ID/product/programme as an existing development → **`linked`** (NEW EVIDENCE, not a new card; append to the existing chain)
- Genuinely new information → **create a new lifecycle event** within the chain (`linked`)
- Only repeats known information → **mark as repeated / low novelty** (deduplication, not a new event)
- **Ambiguous match** (partial overlap, same drug different trial, press-wire noise) → **`possibly_linked`** + **`requires_human_review` flag** — never auto-linked, never auto-created as a new development
- No plausible match → **`unlinked`** (candidate NEW DEVELOPMENT, still human-reviewable)

`link_decision` values: `linked` · `possibly_linked` · `unlinked` (with `requires_human_review` on ambiguous cases). Stored with `development_id` · `event_id` · `source_id`.

This feeds Confluence + Lifecycle + Priority. Publication/registry results later confirmed by peer-reviewed publication upgrade evidence maturity (never counted as two independent findings). Trial registries are live timelines: status changes (recruiting → terminated), protocol/endpoint/population changes, and recruitment variance are lifecycle signals with reason classification (safety-driven termination ≫ recruitment issue).

### 12.7 Red-Team Evidence Checks (extended checklist)

The existing Red-Team layer (NLI contradiction) SHALL additionally run the following evidence checks (from Usha's consolidated framework). High-impact signals must actively search for contradictory/qualifying evidence before producing a strong narrative.

| ID | Check | Rule |
|---|---|---|
| A | **Causality error** | Never convert "adverse event occurred" into "drug caused adverse event"; require causality assessment, preserve uncertainty |
| B | **Duplicate counting** | Trial + congress abstract + company announcement + publication for the SAME underlying evidence ≠ four developments; link records and deduplicate |
| C | **Denominator blindness** | Do not interpret percentages/safety clusters without exposure/sample size where available; block confirmation when denominator absent |
| D | **Population mismatch** | Do not generalise HA→HB, adult→child, inhibitor+→inhibitor− without evidence; check applicability fields |
| E | **Endpoint mismatch** | Do not compare ABR values blindly when endpoint definitions differ (treated vs all bleeds; assay differences) |
| F | **Surrogate overclaim** | Factor activity is not automatically proof of patient-important benefit |
| G | **Small-sample overconfidence** | Very small cohorts must not get high certainty; apply uncertainty penalty |
| H | **Short-follow-up / durability overclaim** | Early gene-therapy data ≠ lifelong durability; require explicit follow-up-duration check |
| I | **Preliminary-evidence error** | Congress abstract/preprint/press release ≠ final evidence; label evidence maturity |
| J | **Sponsor / source-independence error** | Company statement ≠ independent confirmation; capture sponsor/funding relationship |
| K | **Stale information** | Old label/reimbursement rule/trial status used after a newer authoritative update; mark stale, refresh lifecycle |
| L | **Negative-evidence omission** | Terminated/withdrawn/unpublished trials must not be ignored; actively search for disconfirming evidence |
| M | **Approval ≠ reimbursement** | Marketing authorisation must not be presented as reimbursement/coverage |
| N | **Approval ≠ actual patient access** | Approval ≠ commercial availability ≠ actual patient access |
| O | **Jurisdiction mismatch** | A payer decision in one country must not be generalised elsewhere |
| P | **Lifecycle disconnection** | Publication/congress/registry update must link to the existing product/trial record |
| Q | **Statistical significance ≠ clinical significance** | Statistically significant ≠ automatically clinically meaningful (and vice versa for small studies) |
| R | **Contradiction blindness** | Never report a strong positive/safety claim without actively searching for conflicting evidence |
| S | **Governance bypass** | No autonomous diagnosis, causality determination, treatment change, or high-impact decision without qualified human review |

### 12.8 Watch-for-Next (extends Missing-Signal)

Stakeholder feedback can create a **watch rule**: `source_event → development → expected_event_type (e.g., Congress) → monitoring window → responsible function → status`. Statuses: `watching` · `new_evidence_detected` · `no_new_evidence` · `watch_expired` · `human_review_required`. The system NEVER claims a future event will definitely happen — wording is limited to *"Watch for…"*, *"Expected/possible next evidence…"*, *"No subsequent evidence observed during the configured period."* (See §3 Watch-for-Next; mechanism unchanged.)

### 12.9 Priority Scoring (triage mechanism, not a clinical score)

**This is a MetaRadar prioritisation mechanism, not a validated clinical score.** The score is an internal triage aid. It considers: novelty · clinical relevance · safety impact · regulatory impact · strategic/competitive impact · patient impact · evidence maturity · source authority · access impact · freshness · uncertainty · duplication. The research-informed starting formula:

```text
Priority = 0.25 novelty + 0.20 seriousness/actionability + 0.15 source authority
          + 0.15 evidence strength/maturity + 0.10 population relevance
          + 0.10 geographic/access impact + 0.05 freshness  (± uncertainty/duplication penalties)
```

**Automatic CRITICAL/HIGH triggers (regardless of score):** serious safety warning · regulatory rejection/approval/major label change · trial termination for safety · major unexpected benefit-risk change · major treatment-landscape change (new modality/paradigm) · major access restriction. Safety and regulatory events may trigger automatic high-priority escalation. Safety findings can override an otherwise positive efficacy classification. Stakeholder calibration can modify the effective relevance/priority logic (mechanism 5).

### 12.9A Source Authority Model

Authority is contextual — **never a simplistic "source X is always true" rule**. The evidence model combines: `source type` + `source authority` + `publication/event date` + `evidence maturity` + `corroboration` + `contradictory evidence`.

| Source | Authority framing |
|---|---|
| Authoritative regulatory source (FDA/EMA) | High authority for **regulatory facts** (e.g., an approval can be FACT on the FDA source alone) |
| Clinical trial registry (ClinicalTrials.gov) | High authority for **registry/status facts** |
| Peer-reviewed publication | High authority for **published study findings** |
| Congress | Important but **potentially preliminary** (evidence maturity MEDIUM/HIGH) |
| Company announcement | Important primary source but **sponsor-originated** (not independent confirmation) |
| Secondary media | Useful **discovery** source, lower authority |
| Social/community discussion | **Signal/discovery** source, not strong evidence by itself |

**The AI must preserve the distinction between "source says X" and "MetaRadar interprets X as Y"** — outputs always carry the source claim and the system's own interpretation separately (F-I-S labeling plus `source_authority` and `evidence_maturity` fields).

### 12.10 Four-Question Output + Evidence Context

Q1–Q4 remain the core stakeholder questions. Every significant signal additionally carries evidence context (supporting explainability): **Q5 How strong is the evidence?** (evidence maturity + confidence) · **Q6 What is uncertain or contradictory?** (Red-Team flags, uncertainty penalties) · **Q7 What should we watch next?** (watch-for-next / expected milestones).

### 12.11 Deterministic Evaluation Cases (B.Pharm-labelled ground truth)

| Case | Scenario | MetaRadar must… |
|---|---|---|
| CASE 1 | Company says "positive Phase 3 results" | Ask: endpoint? comparator? population? effect size? follow-up? safety? preliminary? (check A/E/H/I/J) |
| CASE 2 | Congress abstract reports new gene-therapy data | Mark preliminary evidence, identify trial, connect to lifecycle, search/flag later publication/regulatory evidence, do NOT treat as regulatory confirmation (I/H/P) |
| CASE 3 | Safety event in positive efficacy programme | Allow safety signal to override simple positive classification; route Safety/PV first; do NOT establish causality automatically (A) |
| CASE 4 | Drug receives regulatory approval | Route Regulatory; do NOT infer reimbursement or actual patient access (M/N) |
| CASE 5 | Reimbursement restriction in one country | Route Market Access; record jurisdiction; do not generalise globally (O) |
| CASE 6 | Evidence from inhibitor-positive haemophilia A patients | Must NOT generalise to inhibitor-negative or haemophilia B populations (D) |
| CASE 7 | Congress presentation + later publication refer to same trial | Link them; identify publication as lifecycle continuation; avoid duplicate development counting (B/P) |

### 12.12 Authoritative Example Sources (examples only — never hard-coded into architecture)

- FDA confirms QFITLIA (fitusiran) approved for routine prophylaxis in patients aged 12+ with haemophilia A or B, with or without FVIII/FIX inhibitors: https://www.fda.gov/news-events/press-announcements/fda-approves-novel-treatment-hemophilia-or-without-factor-inhibitors
- FDA confirms Roctavian for eligible adults with severe haemophilia A: https://www.fda.gov/vaccines-blood-biologics/roctavian
- FDA confirms Hemgenix for specified adults with haemophilia B: https://www.fda.gov/vaccines-blood-biologics/vaccines/hemgenix
- WFH guidelines cover inhibitors, outcome assessment, musculoskeletal complications, and AAV gene therapy: https://guidelines.wfh.org/guidelines/

---

## **13. PROVIDER-AGNOSTIC REASONING LAYER (v5.0 — CANONICAL LLM PROVIDER RULES)**

One shared evidence-grounded intelligence pipeline with a provider-agnostic reasoning layer: **Gemma runs locally by default, Grok can provide hosted reasoning when required, and BART provides a safe factual degraded mode if reasoning is unavailable.** The provider layer is an internal detail of `node_synthesize` (and Ask Athena's grounded answers) — **no new LangGraph nodes, no new agents, no pipeline change.**

```text
                    node_synthesize
                           ↓
                     LLMProvider
                    /     |      \
                   /      |       \
             Gemma     Grok API    BART
             local     hosted      degraded
             reasoning reasoning   factual summary
```

### 13.1 Provider Modes (`LLM_PROVIDER`)

| Mode | Behavior |
|---|---|
| `LLM_PROVIDER=local` (default) | Gemma → BART degraded mode if Gemma is unavailable |
| `LLM_PROVIDER=xai` | Grok → BART degraded mode if Grok is unavailable |
| `LLM_PROVIDER=auto` | Gemma → (failure/unavailable) → Grok → (failure/unavailable) → BART factual degraded mode |

Gemma MUST remain fully usable without any external API key; **no deployment is forced to use Grok.**

**Local Gemma deployment is GPU-first but failure-tolerant (§14.1):** `LLM_DEVICE` selects the device (`cuda:0` default when a GPU is available, else `cpu`/`auto`); `LLM_DTYPE`/quantization selects `int4`/Q4; `MAX_CONTEXT_TOKENS` and `MAX_OUTPUT_TOKENS` bound the model budgets. **Model initialization/inference failure (including "does not fit in 4 GB VRAM") is handled like any other provider failure** — fall through the configured chain. No GPU-specific logic is hard-coded into LangGraph nodes; the provider abstraction owns all model execution.

### 13.2 Provider Interface

LangGraph nodes call the provider interface — never Gemma or Grok directly. Provider-specific logic stays inside the provider implementations:

```python
generate_intelligence(evidence, task, output_schema, metadata) -> IntelligenceResult
```

Providers: `LocalGemmaProvider` · `XAIProvider` · `BartDegradedProvider`. No provider-specific logic is introduced into other nodes.

### 13.3 Two Output Schemas

**Do not force BART to produce the same reasoning schema as Gemma/Grok.**

| Schema | Providers | Fields |
|---|---|---|
| **A. FULL INTELLIGENCE OUTPUT** | Gemma, Grok | `what_changed` · `why_it_matters` · `primary_function` · `secondary_functions` · `routing_reason` · `suggested_action` · `evidence_level` · `confidence` · `supporting_sources` · `uncertainties` · `contradictions` · `watch_for_next` (+ relevant signal metadata) |
| **B. DEGRADED FACTUAL SUMMARY** | BART only | `factual_summary` · `source_ids` · `source_urls` · `published_at` · `evidence_level` · `degraded_mode=true` · `reason_for_degradation` |

BART MUST NOT generate: strategic interpretation · unsupported competitor conclusions · treatment recommendations · safety causality · role-specific strategic recommendations. When BART is used, the UI shows: **"AI reasoning unavailable — showing source-grounded factual summary."**

**Canonical BART statement:** *"BART-large-CNN is used for batch summarization and degraded source-grounded factual summaries only. It does not perform reasoning-equivalent intelligence synthesis."* Keep **BART-MNLI** separate — it is the NLI model for signal classification and Red-Team contradiction analysis, not a summarization or reasoning model.

### 13.4 Grok Structured Output & Validation

- Grok calls SHALL use **JSON-Schema structured outputs** (`response_format` with `json_schema`) — relying on "please return JSON" alone is insufficient (official: https://docs.x.ai/developers/model-capabilities/text/structured-outputs).
- The response SHALL additionally be validated at application level: required fields · enum values · evidence IDs exist · source URLs correspond to retrieved sources · confidence within valid range · evidence level valid · suggested action from the controlled vocabulary · primary/secondary functions valid · no unsupported source IDs · no fabricated entities.
- **Even when the provider guarantees schema conformity, semantic/evidence validation is still required** (a schema-valid response can still cite non-retrieved sources or invent entities).
- **Three distinct validation layers:** (1) **structural/schema validation** — the response conforms to the JSON Schema; (2) **semantic evidence validation** — claims map to retrieved sources (source IDs/URLs exist, no fabricated entities); (3) **evidence-sufficiency gate** (node 9 / SRS FR-2.2.7) — sufficient retrieved evidence before any interpretation is generated. Schema conformity alone does not prove factual correctness.

### 13.5 External LLM Privacy Gate (mandatory for hosted providers)

Before any Grok API call:

```text
PUBLIC/SYNTHETIC CHECK → PII/PHI CHECK → CONFIDENTIALITY CHECK → ALLOWED? YES → GROK / NO → BLOCK
```

NEVER send: confidential Novo Nordisk strategy · internal forecasts · launch plans · patient-level information · PII/PHI · non-public information · confidential documents. If the external call is blocked: use **local Gemma if available → otherwise BART degraded mode → otherwise source-only display.**

xAI API data handling does **not** override the hackathon's stricter public/synthetic-only rule: xAI does not use API inputs/outputs for training without explicit permission, but requests/responses are normally retained ~30 days for abuse auditing (encrypted at rest, auto-deleted) unless applicable stricter retention arrangements (e.g., Zero Data Retention) are used (official: https://docs.x.ai/developers/faq/security).

### 13.6 Failure / Fallback Handling

Handle: missing API key · timeout · rate limit · quota exhaustion · network failure · provider unavailable · invalid provider response · schema validation failure · semantic evidence validation failure.

```text
Gemma unavailable (incl. VRAM/init failure) → Grok (in xai/auto modes)
Grok unavailable  → BART factual summary
No reasoning provider → source-linked factual signal + human-review flag
```

**The dashboard is designed to remain available during tested provider failures** through retry, the configured provider-chain fallback, and degraded factual output. Graceful degradation across the defined failure-injection scenarios is an acceptance target, not an absolute production guarantee (§10).

### 13.7 Model Metadata (every generated output)

Every generated output SHALL record: `provider` · `model` · `model version/ID` · `task` · `temperature` · `prompt-template ID` · `config hash` · `timestamp` · `fallback status` · `fallback reason`.

```json
{ "provider": "xai", "model": "<configured model>", "mode": "reasoning",
  "fallback_from": "local_gemma", "fallback_reason": "model_load_failure" }
{ "provider": "local", "model": "facebook/bart-large-cnn", "mode": "degraded_factual",
  "fallback_from": "xai", "fallback_reason": "api_timeout" }
```

### 13.8 Canonical Model Table (every document MUST use this)

| Role | Default | Alternative |
|---|---|---|
| Reasoning / Four Questions / Athena | Gemma 3 4B local (**GPU**, Q4/int4 — RTX 3050 4 GB VRAM) | Grok API |
| Degraded factual summary | BART-large-CNN | — |
| Batch summarization | BART-large-CNN | — |
| NLI | BART-MNLI | — |
| NER | spaCy | — |
| Embeddings | MiniLM | — |

BART is NEVER listed as a reasoning model.

---

## **14. ARCHITECTURE HARDENING (v5.1 — PRE-IMPLEMENTATION DECISIONS)**

This section records the decisions from the final pre-implementation hardening pass. It is **not a redesign** — the §4 pipeline, ten nodes, five mechanisms, six functions, calibration loop, Ask Athena, and the provider abstraction are all unchanged. Every item below is a decision that would become expensive, dangerous, or difficult to change AFTER implementation begins, so it is locked here first.

### 14.1 Local Model Execution — GPU Deployment Target & Root `models/` GGUF Discovery

**Deployment target (actual development/demo machine):** NVIDIA RTX 3050, **4 GB VRAM** (or CPU fallback).

* **Gemma 3 4B Instruct, Q4/int4 — Local GPU / Direct GGUF.** Stored directly in the root `models/` directory (e.g. `models/gemma-3-4b-it-Q4_K_M.gguf`) or served via local Ollama sidecar (`http://localhost:11434`).
* **Root `models/` Folder Architecture:** MetaRadar automatically scans the repository root `models/` directory for any reasoning `.gguf` file. Any user-placed quantized reasoning model (`*.gguf`) is auto-discovered and loaded for local reasoning, Four-Question synthesis, and Ask Athena.
* **Interactive Setup (`setup.py`):** The automated setup wizard provides an interactive choice:
  1. Download default local reasoning model (`gemma-3-4b-it-Q4_K_M.gguf` ~2.4 GB into `models/`) for 100% private, offline inference.
  2. Enter Hosted LLM API Key (`xAI Grok`).
  3. Skip (operate in source-grounded BART degraded factual fallback mode).
* **4 GB VRAM does NOT guarantee successful inference.** Model weights, KV cache, runtime overhead, and context length are budgeted **separately** (weights ≈ 2.4 GB Q4; KV cache and context grow with `MAX_CONTEXT_TOKENS`; runtime/overhead depends on the runner).
* **The system must never crash because Gemma cannot fit or execute.** Execution flow:

```text
Local GGUF in models/ or Ollama → Gemma 3 4B Q4 → reasoning output
        ↓ init/inference failure / credits limit
Grok API (if configured and permitted) → reasoning output
        ↓ failure
BART factual degraded mode (source-grounded summary)
        ↓ if no reasoning provider at all
source-grounded factual signal + human-review flag (dashboard stays alive)
```

* **Configurable settings (env vars, SRS §4.2):** `MODELS_DIR` (`./models`) · `LOCAL_GGUF_MODEL` · `LOCAL_LLM_MODEL` · `LLM_DEVICE` (`cuda:0` / `cpu` / `auto`) · `LLM_DTYPE`/quantization (`int4`/Q4 default) · `MAX_CONTEXT_TOKENS` · `MAX_OUTPUT_TOKENS`. BART/spaCy/MiniLM/BART-MNLI remain CPU-friendly and are unaffected.
* **No GPU-specific logic in LangGraph nodes.** The `LLMProvider` abstraction (`GemmaProvider`/`GrokProvider`/`DegradedProvider`) owns ALL model execution, device selection, quantization, and failure handling (§13).

### 14.2 Canonical Entity Model & Database Architecture

The database is designed around **stable entities** — never one giant `signals` table. Stable identifiers (UUIDs):

```text
signal_id · source_id · company_id · asset_id · trial_id · development_id · event_id ·
publication_id · congress_event_id · regulatory_event_id · access_event_id
```

**Central relationships (must hold in the schema):**

```text
Signal → Development → Asset → Company

Development → Trial → Congress → Publication → Regulatory event → Access event → Post-market evidence
```

* The **same development accumulates multiple signals without duplicate developments** (essential for Confluence and Lifecycle). A trial → congress abstract → oral → poster → publication stays ONE development.
* **Entity tables (first migration must anticipate all of them):** `sources` · `companies` · `assets` · `trials` · `developments` · `events` · `evidence` · `signals` · `raw_signals_bronze` · `confluences` · `lifecycle_chains`/`lifecycle_events` · `contradictions` · `watch_items` · `calibration` (`stakeholder_feedback` + `calibration_history` + `scoring_weights`) · `audit_log`.
* **Canonical Signal object** (consumed identically by database, LangGraph, API, frontend, LLM provider, scoring engine, calibration engine, audit system):

```text
signal_id · source_id · external_id · development_id · company_id · asset_id · trial_id ·
signal_type · disease · factor · inhibitor_status · population · title · content ·
published_at · retrieved_at · source_type · source_authority · evidence_maturity ·
facts · interpretation · speculation · priority · priority_breakdown · routing ·
actions · watch_for_next · supporting_evidence_ids · contradictory_evidence_ids ·
model_metadata · calibration_metadata
```

  All fields are **nullable** where evidence may be unavailable — the AI is never forced to invent missing fields.
* **Immutable source provenance:** every ingested source item preserves `source_id · external_id · source_url · publisher · source_type · published_at · retrieved_at · raw_content_hash · content_version`. AI claims reference evidence IDs; the database can always answer *"What exact source caused this statement?"*
* **Explicit evidence relationships** (explainability): `claim → evidence` · `interpretation → evidence` · `priority → evidence` · `routing → evidence + scoring logic` · `action → evidence + reasoning`.
* **Migrations:** schema evolution via **Alembic** only — never `drop_all()`/`create_all()` for normal development (§14.14).

### 14.3 Source Connector Interface

All external sources implement **one common interface** returning the same normalized `RawSignal`:

```text
RawSignal: source_id · source_type · external_id · title · content · url ·
           published_at · retrieved_at · publisher · raw_hash
```

Adapters: `PubMedConnector` · `NewsAPIConnector` · `ClinicalTrialsConnector` · `FDAConnector` · `EMAConnector` · `CongressConnector` · `RedditConnector` (+ `SyntheticConnector`). **Adding a future source requires a new adapter only — never a rewrite of `node_ingest`.** Each connector reports its **freshness class**: `real_time` · `near_real_time` · `delayed` · `batch` · `adapter_ready` · `synthetic` (the dashboard is honest about freshness; no blanket "real-time" labels).

### 14.4 Deduplication & Source Independence (BEFORE Confluence)

* **Deterministic deduplication layer runs before Confluence.** Every raw source item receives a stable fingerprint, preferring available identifiers: PubMed PMID · ClinicalTrials.gov NCT ID · FDA identifiers · official publication identifiers · congress abstract identifiers; for sources without stable IDs, use the normalized **title + publisher + date + company + asset + URL**.
* **Source-independence model:** store `source_class · publisher · syndication_group · parent_source_id`. Example — PubMed + ClinicalTrials.gov + a company announcement may count as independent; **three websites reproducing the same company release are ONE source**, not three signals.
* Confluence operates on **independent evidence, not raw article count.** Duplicate/syndicated copies are never counted as independent signals (supports Red-Team check B).

### 14.5 Domain Configuration Layer & Ontology Quality Gate

* **Haemophilia is configuration, not hard-code.** No `if haemophilia` / `if Hemlibra` / `if FVIII` scattered through application code. A domain configuration layer (`config/haemophilia.yaml`) contains: diseases · factors · inhibitor categories · companies · assets · therapies · signal types · keywords · synonyms · functions · ontology mappings · scoring defaults. **The core intelligence engine is therapy-area agnostic** — the primary scalability mechanism for expanding beyond Haemophilia (Haemophilia → other Rare Diseases → multiple therapy areas) without touching the database, API contracts, LangGraph nodes, provider layer, or frontend foundation.
* **Ontology quality gate (before any ontology data enters production/demo databases):** `generic_name · brand_name · company · mechanism · disease · factor · inhibitor_population · approval_status · approval_date · jurisdiction · source · last_verified`. Stale or manually-guessed product information is rejected. Approval status is tracked as an **updatable fact** (with source + last_verified), never treated as permanent/static.
* **Verified FDA product mappings (do not swap):**
  - **fitusiran → Qfitlia** (Sanofi; FDA-approved March 2025 for routine prophylaxis, haemophilia A/B ± inhibitors)
  - **concizumab → Alhemo** (Novo Nordisk; FDA-approved December 2024 for prophylaxis in haemophilia A/B with inhibitors)
  - **marstacimab → Hympavzi** (Pfizer; approved 2024, expanded June 2026 to ages 6+ haemophilia A/B ± inhibitors)

### 14.6 LangGraph State Contract (formal)

* **Explicit state fields:** `raw_signals · validated_signals · extracted_entities · ontology_entities · developments · scored_signals · confluent_stories · lifecycle_events · redteam_flags · missing_signals · role_briefs · calibration_feedback · model_metadata · errors`.
* **Explicit initial state** is defined; no node may assume a field is pre-initialized (`state["signals"].append(...)` on an uninitialized field is forbidden).
* **Typed reducers:** list/accumulating fields use append/merge reducers (critical for parallel source connectors and parallel analysis nodes); scalar fields use replacement semantics.
* **Ownership:** each node declares read/write fields (documented in the graph module); no node mutates arbitrary state.
* **Explicit termination:** `node_calibrate → END` (never implicit). Configure `recursion_limit` and per-node error boundaries/failure limits. One node's failure does not kill the pipeline (per-node error handling, §39 → SRS error FRs).
* **Concurrency:** parallel connectors share `raw_signals`/`validated_signals`/`evidence`/`errors` through reducers — concurrent nodes cannot overwrite the same field incorrectly.

### 14.7 API Versioning, Health & CORS

* **Versioned API only:** `/api/v1/` (`/signals · /developments · /companies · /trials · /briefs · /feedback · /athena · /health`). No unversioned production-style endpoints are added.
* **Health endpoints:** `GET /api/v1/health` · `GET /api/v1/health/ready` · `GET /api/v1/health/models` · `GET /api/v1/health/connectors`. Health separately reports: **API · PostgreSQL · Redis · Gemma (loaded/available) · Grok (configured/not) · PubMed · NewsAPI · ClinicalTrials.gov**. **A failed optional source must not make the entire application appear dead** (source health degrades independently).
* **CORS:** `CORSMiddleware` with an environment-configurable allowlist (`CORS_ORIGINS=http://localhost:3000`, multiple origins supported). `"*"` is never hard-coded for credentialed application traffic.

### 14.8 Caching — Redis Serialization & Invalidation

* **One canonical JSON serialization layer** for datetime · UUID · Decimal · Enum · Pydantic models before Redis — no scattered custom `json.dumps` over raw ORM/Pydantic objects.
* **Versioned cache keys:** `signal:{signal_id}:v1`, `brief:{brief_id}:v{api_version}` etc.
* **Every cache entry carries:** TTL · schema version · source timestamp · optional model/config version. When scoring/calibration/model logic changes, stale generated intelligence must NOT silently appear as current — keys or TTLs are invalidated on version bump (pattern: `signal:{id}:v1` → `:v2`).

### 14.9 Scheduler — ONE Scheduler (decision record)

* **Decision:** **FastAPI + APScheduler (in-process, single scheduler) + Redis for caching.** **Celery is NOT used** in the hackathon architecture.
* **Why:** the required jobs (2-hour fetch, nightly digest, on-demand recalibration) are lightweight and fully served by one in-process APScheduler with async jobs; heavy LangGraph runs are offloaded from the event loop via `asyncio`/thread-pool execution. Two scheduling systems would introduce duplicate scheduling paths and unnecessary infrastructure for a 4-week demo on a 4 GB VRAM laptop.
* **Reintroduction path (documented, NOT built):** if sustained throughput exceeds ~1,000 signals/cycle, multi-node workers are needed, or jobs must survive backend restarts, migrate the job bodies to Celery workers with APScheduler (or Celery beat) as the single scheduler — the job logic lives in services, so the move is additive, not a rewrite.
* All docs, Docker Compose, and the stack references are updated to remove Celery (README · CLAUDE.md · SDD · SRS · plan docs).

### 14.10 Scoring & Calibration Versioning

* **Priority score versioning:** never store only `priority_score = 82`. Store `priority_score` **+ `scoring_model_version` (e.g., "v1") + `scoring_config_version` (e.g., "haemophilia_v1") + `score_breakdown`** (factor-level). Future scoring changes do not rewrite historical results.
* **Calibration versioning:** never overwrite the AI baseline. Per signal store `baseline_score · baseline_routing · baseline_action` THEN `calibrated_score · calibrated_routing · calibrated_action`, plus `calibration_version · feedback_id · feedback_timestamp · stakeholder_function`. The demo must reproduce **BEFORE → stakeholder feedback → AFTER** for exactly the same signal.

### 14.11 Red-Team Modularity, Watch Rules, Action Vocabulary

* **Red-Team rules are modular:** `RedTeamRule` registry (causality · denominator · population mismatch · endpoint mismatch · surrogate overclaim · small sample · short follow-up · preliminary evidence · source independence · stale information · negative evidence · approval/access · jurisdiction · lifecycle · statistical vs clinical significance · contradiction · duplicate inflation — a superset already covers A–S in §12.7). **New checks are addable without rewriting `node_redteam`.**
* **Watch rules are data/configuration-driven** (no competitor watches hard-coded in Python): `watch_id · development_id · trigger_event · expected_event · monitoring_window · responsible_function · status`. Canonical statuses: **`active` · `observed` · `expired` · `dismissed`**, with an explicit mapping to the persisted/UI-facing §12.8 statuses (stored in `watch_items.status`): **`active` ↔ `watching`** · **`observed` ↔ `new_evidence_detected`** (also covers `no_new_evidence` while still watching) · **`expired` ↔ `watch_expired`** · **`dismissed` ↔ `human_review_required`** (human-resolved). The schema stores the UI-facing value; the canonical vocabulary is the application-level contract.
* **Action vocabulary (controlled, FR-2.6.1):** `monitor` · `review` · `prepare_internal_briefing` · `prepare_scientific_faq` · `escalate` · `request_stakeholder_review` · `no_immediate_action`. Every action is **"Suggested — requires human review." No autonomous action.**

### 14.12 Prompt Versioning, Observability, Idempotency

* **Prompt versioning:** every production prompt carries `prompt_id` + `prompt_version` (e.g., `four_question_reasoning_v1` · `routing_v1` · `redteam_v1` · `athena_v1`). The prompt version is stored with every model output (`prompt_template_id` in model metadata). Prompts live in versioned config/template files — never buried in random source files.
* **Model metadata (every output, FR-2.2.3F):** `provider · model · model_version · task · prompt_template_id · config_hash · timestamp · fallback_status · fallback_reason · latency`.
* **Observability:** structured logging with `run_id` per pipeline run, `signal_id` per signal, `model_request_id` per model request; log `node · duration · provider · fallback · error · source · signal_id · run_id`. **No confidential data or patient information is ever logged.**
* **Idempotency:** pipeline jobs are safe to run repeatedly. Stable external IDs + idempotency keys mean: the same source item retrieved twice does not create duplicate signals; the same calibration feedback submitted twice is not applied twice; the same development event processed twice does not duplicate lifecycle events.

### 14.13 Evaluation & Calibration Datasets

* **Synthetic 500-signal dataset carries ground truth:** `signal_id · ground_truth_signal_type · ground_truth_company · ground_truth_asset · ground_truth_disease · ground_truth_priority · ground_truth_function · ground_truth_action · expected_evidence_level` — making the **≥85% classification target measurable**. The classifier is never evaluated only on data it generated itself.
* **Calibration uses separate feedback data:** calibration is never trained AND tested on the same feedback records. Feedback records carry `feedback_id · signal_id · function · relevance · urgency · action_appropriate · comment · timestamp`; the system tracks `baseline → feedback → calibrated result` (see §14.10).

### 14.14 Migrations, Indexing, Docker & Configuration

* **Migrations:** Alembic for ALL schema evolution; `drop_all()`/`create_all()` are never the normal development path. The FIRST migration already anticipates `signals · sources · companies · assets · trials · developments · events · evidence · calibration · audit`.
* **Indexing (frequent queries):** `signal_id · development_id · company_id · asset_id · trial_id · published_at · retrieved_at · signal_type · primary_function · priority · evidence_maturity`; **vector indexes only where semantic search actually requires them** — no unnecessary indexes everywhere.
* **Docker:** application image is separate from **model weights** — a mounted `/models` directory (model volume/cache) so the app starts without re-downloading multiple GB every time. Compose uses healthchecks (`pg_isready` for PostgreSQL, `redis-cli ping` for Redis, `/api/v1/health/ready` for the backend) — `depends_on` alone never implies readiness.
* **Configuration:** database URL · Redis URL · CORS origins · LLM provider · Gemma model/device/dtype/context · Grok model/API key · NewsAPI key · source polling intervals · cache TTL · scoring configuration · calibration configuration are ALL environment-configurable. **No hard-coded credentials. No secrets in Next.js/browser code.**

### 14.15 Frontend / Backend Contract & Reusable Components

* **API response schemas (Pydantic) define the contract** — the frontend NEVER depends on database models directly. Flow: `Database → service/domain layer → API schema → frontend` (not `Database model → directly serialized into frontend`).
* **Reusable component contract (canonical names, one implementation each):** `SignalCard` · `EvidenceBadge` · `PriorityBadge` · `FunctionBadge` · `LifecycleTimeline` · `ConfluenceAlert` · `RedTeamPanel` · `CalibrationWidget` · `WatchAlert` · `AthenaPanel`. No separate one-off implementations per signal type (the UI Design doc maps existing components to these canonical names, §4_UI).

### 14.16 Implementation Status Vocabulary

Repository claims are **honest** using exactly: **`PLANNED`** (designed, not started) · **`SPECIFIED`** (fully specified in docs) · **`IMPLEMENTED`** (code exists) · **`TESTED`** (verified by tests) · **`VERIFIED`** (demonstrated). Nothing is claimed implemented/working/tested/verified unless the repository actually contains and passes it. Today the repository is documentation-only: every feature is **SPECIFIED**.

### 14.17 Final Architecture (unchanged canonical flow)

```text
PUBLIC SOURCES → SOURCE CONNECTORS → NORMALIZATION → DEDUPLICATION → VALIDATION →
NLP EXTRACTION → ONTOLOGY ENRICHMENT → CONFLUENCE → LIFECYCLE → RED-TEAM →
MISSING-SIGNAL / WATCH → SYNTHESIS → STAKEHOLDER CALIBRATION → FOUR QUESTIONS →
FUNCTION ROUTING → DASHBOARD / DIGEST / ATHENA

SYNTHESIS PROVIDER: Gemma GPU → (failure) Grok API → (failure) BART factual degraded mode
```

No additional pipeline exists. The hardening decisions in §14 do not change the §4 pipeline — they lock its contracts so implementation can begin without expensive late changes.

---

*Master Specification Approved & Frozen: August 2026*  
*Novo Nordisk GBS Hackathon 2026 — Problem Statement #3*  
*Team: Aura Pharmers — MSRIT (2 CSE + 3 B.Pharm) · Team Lead: Sanjana Rathore B.*
