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

* **Primary MVP Role:** **Medical Affairs** (Novo Nordisk Rare Disease Franchise).
* **Primary Focus:** Monitoring clinical trials, publication readouts, congress abstracts, safety signals, and competitor drug positioning affecting Novo Nordisk's haemophilia portfolio (concizumab, mim8) against key market competitors (Roche's emicizumab, CSL Behring's Hemgenix, BioMarin's Roctavian, Sanofi's fitusiran, Pfizer's marstacimab).
* **Future Secondary Roles (Phase 2):** Regulatory Affairs, Market Access & HEOR, Commercial Strategy, Clinical R&D.

---

## **3. MVP SCOPE**

To guarantee execution discipline within a 4-week hackathon window, the MVP scope is strictly locked to:

* **One Role:** Medical Affairs
* **One Disease Area:** Haemophilia within Rare Disease (Haemophilia A & Haemophilia B)
* **Two Primary Live Sources:** PubMed Central API + NewsAPI (backed by a 500-signal synthetic demo fallback dataset)
* **Five Intelligence Mechanisms:**
  1. Confluence Detection
  2. Signal Lifecycle Tracking
  3. Red-Team Contradiction Analysis
  4. Missing-Signal Detection
  5. Stakeholder Calibration Prototype (HITL)
* **One UI Interface:** Four-Question Decision Interface (Q1: What changed? → Q2: Why matters? → Q3: Which function? → Q4: What action?)
* **One End-to-End Demo Story:** A haemophilia competitive development involving mim8 / emicizumab / Hemgenix durability data.

*Everything else (additional roles, extra scrapers, custom LLM fine-tuning) is classified as Phase 2 future extensions.*

---

## **4. ARCHITECTURE**

MetaRadar implements a **10-Node LangGraph Workflow** orchestrating data flow from public ingestion to decision panels:

```text
                               PUBLIC SIGNALS
                               /            \
                           PubMed         NewsAPI
                               \            /
                                INGESTION
                                    ↓
                                VALIDATION
                                    ↓
                            ENTITY + ONTOLOGY
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
                                SYNTHESIS
                                    ↓
                         STAKEHOLDER CALIBRATION
                                (HITL)
                                    ↓
                             FOUR QUESTIONS
                                    ↓
                           MEDICAL AFFAIRS UI
```

### 10-Node LangGraph Execution Breakdown:
1. **`node_ingest`**: Fetches raw JSON from PubMed API & NewsAPI via `httpx` async client.
2. **`node_validate`**: Filters short text (<50 chars), non-English data, and non-haemophilia scope.
3. **`node_nlp_extract`**: Extracts drug names, companies, indications, and clinical trial IDs using spaCy (`en_core_sci_md`).
4. **`node_ontology_enrich`**: Maps extracted entities against B.Pharm Haemophilia Ontology (Hemlibra $\rightarrow$ emicizumab $\rightarrow$ Roche $\rightarrow$ bispecific antibody).
5. **`node_confluence`**: Scans rolling 48-hour window for entity convergence across $\ge 3$ distinct signal types.
6. **`node_lifecycle`**: Advances asset state machine (`announced → in_trial → results_in → under_review → approved → post_market | discontinued`).
7. **`node_redteam`**: Runs pairwise NLI entailment/contradiction checks using local `facebook/bart-large-mnli`.
8. **`node_missing_signal`**: Evaluates FSM state against max lag rules to flag absent expected milestones.
9. **`node_synthesize`**: Generates 1-sentence summaries (BART batch) and Four-Question briefs via the Gemma 3 reasoning LLM, anchored strictly in source excerpts.
10. **`node_calibrate`**: Updates role-scoring weights based on stakeholder feedback ratings (`StakeholderCalibrationService`).

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
| **1. Confluence** | Incoming raw signals | Group by normalized Entity ID over rolling 48h window. Check if distinct `signal_type` count $\ge 3$. Aggregate severity $S = \sum (w_{type} \times \text{credibility})$. | **Convergence Alert** (e.g. ASH + Press Release + Patient Forum in 48h) |
| **2. Lifecycle** | Historical signal logs | FSM State Machine: `announced → in_trial → results_in → under_review → approved → post_market \| discontinued`. Chronological event ordering + expected event calculation. | **Development Timeline** (Current state + expected next milestone + elapsed days) |
| **3. Red-Team** | Claim pairs | Zero-shot NLI entailment check using local `facebook/bart-large-mnli`. Evaluate claim pairs linked to entity in 90d window. Flag `contradiction` if score $> 0.60$. | **Challenge Evidence** (Side-by-side evidence chains + devil's advocate review note) |
| **4. Missing-Signal** | Lifecycle FSM state | Rule evaluation: if current state is $S_i$ and $\Delta t_{\text{last\_signal}} > t_{\text{max\_lag}}$, trigger missing alert with confidence $C = \min(0.40 + 0.002 \times \Delta t_{\text{silence}}, 0.95)$. | **Missing-Event Alert** (Silence early-warning requiring human review) |
| **5. Stakeholder Calibration** | Persona feedback ratings (1–5) | Online gradient update on function scoring weights $\mathbf{W}_{role}$ processed by `StakeholderCalibrationService`, logged in WORM `calibration_history`. | **Revised Relevance Score** (Dynamic role-routing weight adjustment) |

---

## **7. USER INTERFACE (DECISION-FIRST LAYOUT)**

The UI is strictly subordinate to the intelligence. Rather than presenting raw news lists, the interface centers on the **High-Priority Development Card**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ HIGH-PRIORITY DEVELOPMENT                                              │
│ mim8 Competitive Landscape Shift                                       │
│ Overall Confidence: 87% | Confluence Level: CRITICAL                  │
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
│ Medical Affairs (94% confidence — calibrated)                          │
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
* **Engineering Tasks:** Comprehensive fallback testing (Redis cache $\rightarrow$ Bronze DB $\rightarrow$ 500-signal synthetic dataset). Error handling, log verification, performance tuning (<500ms cached dashboard response). UI polish, citation link checks, end-to-end demo rehearsal.
* **Milestone:** Bulletproof submission package (Docker Compose, presentation deck, 2-page report, recorded demo video).

---

## **9. DEMO SCENARIO (THE HEMGENIX 3-YEAR DURABILITY SHIFT)**

The presentation demo tells **one continuous haemophilia story**:

1. **Signals Arrive:** Three signals enter the system (PubMed paper on Hemgenix 3-year data + CSL Behring press release + Reddit patient forum post).
2. **Confluence Connects:** Confluence Engine merges all three into one High-Confluence Strategic Alert.
3. **Lifecycle Tracks:** Lifecycle Tracker places the update at *Post-Market Durability Tracking* on the timeline.
4. **Red-Team Challenges:** Red-Team Agent flags contradicting evidence between trial durability claims and real-world cohort waning.
5. **Missing-Signal Warns:** Missing-Signal Detector flags an expected competitor regulatory submission that remains silent past 120 days.
6. **Four Questions Frame:** Q1–Q4 panels summarize the situation, tag Medical Affairs at 94% confidence, and present a suggested briefing action.
7. **Stakeholder Prototype Calibrates:** A Medical Affairs persona submits feedback, `StakeholderCalibrationService` updates scoring weights, and future routing confidence visibly recalibrates live.

---

## **10. VALIDATION CRITERIA (MEASURABLE TARGETS)**

To maintain absolute technical honesty, system performance is evaluated strictly against verifiable engineering targets:

* **Dashboard Response Time:** $< 500\text{ ms}$ for cached signal views.
* **Ingestion Resilience:** $100\%$ graceful degradation (zero dashboard crashes) when external APIs fail or return 429/500 errors.
* **Data Replayability:** $100\%$ verbatim raw payload persistence in `raw_signals_bronze` before processing.
* **Traceability:** $100\%$ of generated AI insights contain valid source links, timestamps, and quotes.
* **Testing:** Automated unit & integration tests covering critical pipeline nodes (ingestion, entity extraction, confluence clustering, calibration service).

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
