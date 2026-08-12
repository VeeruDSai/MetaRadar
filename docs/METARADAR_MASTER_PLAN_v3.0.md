# MetaRadar: Master Plan & Canonical Specification (v3.0)

**Project:** MetaRadar — Near-Real-Time Competitive Intelligence Radar  
**Version:** 3.0 (Canonical Master Specification)  
**Date:** August 2026  
**Target Event:** Novo Nordisk GBS Hackathon 2026 (Problem Statement #3: "From Inbox Noise to Strategic Signal | Pilot Area: Haemophilia within Rare Disease")  
**Team:** MS Ramaiah Institute of Technology (MSRIT) — Cross-Disciplinary (2 CSE + 3 B.Pharm)  
**Specification Status:** **SOLE AUTHORITATIVE MASTER PLAN** (All other documentation files are secondary historical references).

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
* **Three Primary Live Sources:** PubMed Central API + NewsAPI + ClinicalTrials.gov (LIVE) · FDA/EMA/Congress/Reddit ADAPTER-READY · 500-signal synthetic demo fallback (SYNTHETIC-DEMO)
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
1. **`node_ingest`**: Fetches raw JSON from PubMed API & NewsAPI via `httpx` async client.
2. **`node_validate`**: Filters short text (<50 chars), non-English data, and non-haemophilia scope.
3. **`node_nlp_extract`**: Extracts drug names, companies, indications, and clinical trial IDs using spaCy (`en_core_sci_md`).
4. **`node_ontology_enrich`**: Maps extracted entities against B.Pharm Haemophilia Ontology (Hemlibra $\rightarrow$ emicizumab $\rightarrow$ Roche $\rightarrow$ bispecific antibody).
5. **`node_confluence`**: Scans rolling 48-hour window for entity convergence across $\ge 3$ distinct signal types. **For congress/publication signals, first asks *"is this part of an existing development?"*** — if a matching `development_id` exists, the signal is linked into the existing development/evidence chain instead of becoming a new intelligence card (NEW EVIDENCE ABOUT EXISTING DEVELOPMENT vs NEW DEVELOPMENT).
6. **`node_lifecycle`**: Advances asset state machine (`announced → in_trial → interim_result → final_result → congress_publication → regulatory_development → approved → post_market | discontinued`). Every event records **`event_type` · `event_date` · `development_id` · `source_id`** so a trial → congress abstract → oral presentation → poster → publication chain stays ONE development timeline.
7. **`node_redteam`**: Runs pairwise NLI entailment/contradiction checks using local `facebook/bart-large-mnli`.
8. **`node_missing_signal`**: Evaluates FSM state against max lag rules to flag absent expected milestones. Supports **stakeholder-defined WATCH RULES** (source_event → expected/interesting next event → monitoring window → responsible function → status). Statuses: `watching` → `new_evidence_detected` / `no_new_evidence` / `watch_expired` / `human_review_required`. Wording is always *"Watch for…" / "Expected/possible next evidence" / "Not observed yet"* — never a claim that the event will happen.
9. **`node_synthesize`**: Runs the **evidence-sufficiency check** (retrieve evidence → sufficient? → YES: generate grounded interpretation; NO: restrict output to verified facts / "Insufficient evidence to support an interpretation" + request human review). Generates 1-sentence summaries (BART batch), **Fact / Interpretation / Speculation labels**, and Four-Question briefs via the Gemma 3 reasoning LLM, anchored strictly in source excerpts.
10. **`node_calibrate`**: Updates function-scoring weights based on stakeholder feedback ratings (`StakeholderCalibrationService`) → improved future routing/prioritization. **Calibration scope is not limited to priority** — stakeholders can influence priority, routing, actions, watch rules, and relevance criteria (BEFORE/AFTER shown in demo).

### Technology Stack:
* **Frontend:** Next.js 15 (React 19, TypeScript, TailwindCSS 4, shadcn/ui)
* **Backend API:** FastAPI (Python 3.11 ASGI)
* **Workflow Orchestration:** LangGraph 0.1+ (10-node state graph)
* **Database & Vector Storage:** PostgreSQL 16 + `pgvector` extension
* **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (**384-dimensional vector embeddings**)
* **Reasoning LLM (default):** `google/gemma-3-4b-it` — Gemma 3 4B Instruct, a local instruction-tuned LLM (Q4-quantized for CPU) driving narrative synthesis, Four-Question reasoning, AI-suggested actions, and Ask Athena. Auto-falls back to BART if unavailable.
* **Batch Summarizer:** `facebook/bart-large-cnn` — fast CPU seq2seq model for 1-sentence signal summaries (< 60s per 100 signals); also the demo-safety fallback.
* **Cache & Rate Limiting:** Redis 7 (2h TTL hot cache, 500 req/day API rate limiting)
* **Async Workers & Scheduler:** Celery 5.3 + APScheduler (2-hour periodic fetch execution)

---

## **5. DATA SOURCES**

### Live Ingestion Sources (MVP):
1. **PubMed Central API:** Clinical literature, Phase 2/3 trial readouts, academic reviews (Free REST API).
2. **NewsAPI:** Industry news, press releases, competitor corporate announcements (500 free requests/day).

### System Data Polling & Availability:
* **Source Polling Frequency:** Every 2 hours (via Celery + APScheduler).
* **Dashboard Availability:** Continuously available near-real-time radar.

### Synthetic Demo Fallback:
* **500-Signal Pre-Curated Synthetic Dataset:** Local JSON fallback guaranteeing flawless offline demo execution even if public APIs experience rate limits or network failures.

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
* **Engineering Tasks:** Docker Compose environment setup (FastAPI, Next.js 15, PostgreSQL 16 + pgvector, Redis 7). Implement PubMed Central & NewsAPI connectors with `httpx` async fetching. Database schema initialization (`signals`, `entities`, `raw_signals_bronze`).
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
* **Ingestion Resilience:** $100\%$ graceful degradation (zero dashboard crashes) when external APIs fail or return 429/500 errors.
* **Data Replayability:** $100\%$ verbatim raw payload persistence in `raw_signals_bronze` before processing.
* **Traceability:** $100\%$ of generated AI insights contain valid source links, timestamps, and quotes.
* **Testing:** Automated unit & integration tests covering critical pipeline nodes (ingestion, entity extraction, confluence clustering, calibration service).

**The Five Hackathon Success Metrics (explicit, non-negotiable):**
1. **Source-linked summaries = 100%** — every high-priority AI insight carries source name, URL, publication date, source type, excerpt, evidence level, confidence, timestamp, AI-generated label.
2. **Classification accuracy ≥ 85%** — on a B.Pharm-labelled validation dataset (disease · patient type · signal type · priority · impacted function), reporting accuracy, precision, recall, confusion matrix.
3. **Top-signal discovery time ≤ 5 minutes** — reproducible test on a 100-signal weekly batch vs a manual browsing baseline.
4. **Confidential / patient data = 0** — public and synthetic data only; PII scrubber; audit scan.
5. **Stakeholder-calibrated improvement** — measurable routing/priority improvement before vs after feedback (e.g., agreement uplift ≥ 10 points).

**F-I-S compliance:** 100% of high-priority outputs carry a Fact / Interpretation / Speculation label; speculation is never presented as fact; insufficient evidence yields "Insufficient evidence to support an interpretation."

**Routing explainability:** every high-priority signal carries `primary_function` + `secondary_functions[]` + per-function relevance scores + a **routing reason** ("why this function, why now"); routing is never a bare badge. Initial routing matrix is seed-only; calibration adjusts it (mechanism 5).

**Congress/Publication linking:** congress and publication signals participate in Confluence, Lifecycle, Red-Team, priority scoring, function routing, the evidence chain, and stakeholder calibration — they are first-class signal types, not generic news. A congress abstract for an existing trial must attach to that trial's development chain (NEW EVIDENCE ABOUT EXISTING DEVELOPMENT) rather than spawn an unrelated card.

**Watch-for-Next coverage:** the demo dataset includes the watch-rule scenario ("watch this competitor trial for future congress disclosures") with the full flow: trial detected → watch created → congress signal detected → linked to existing development → functions notified; plus the no-evidence variant returning *"No subsequent congress evidence observed during the configured monitoring window."*

---

## **11. KNOWN LIMITATIONS**

1. **Public API Quotas:** NewsAPI free tier is capped at 500 requests/day. Mitigated by Redis caching and 2-hour fetch polling.
2. **Local Model Capabilities:** Inference runs entirely on local CPU (`google/gemma-3-4b-it` reasoning LLM, `facebook/bart-large-cnn` batch summarizer, BART MNLI, spaCy, MiniLM embeddings). Reasoning depth and speed are bounded by CPU RAM constraints compared to commercial LLMs; the system automatically falls back to BART when the Gemma model cannot be loaded.
3. **Stakeholder Feedback Scope:** True organizational feedback across global pharma teams is unavailable in a hackathon setting; the calibration loop is demonstrated using persona-driven simulated feedback.
4. **Absence Alerting Precision:** Missing-signal detection relies on rule-based time lag thresholds ($t_{\text{max\_lag}}$); abnormal market delays may trigger false-positive alerts, which are strictly gated behind mandatory human review.

---

*Master Specification Approved & Frozen: August 2026*  
*Novo Nordisk GBS Hackathon 2026 — Problem Statement #3*  
*Team: MSRIT (2 CSE + 3 B.Pharm)*
