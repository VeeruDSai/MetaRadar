# MetaRadar: Pitch Narrative, Presentation Structure & Technical Defense Guide

**Project:** MetaRadar - Real-Time Haemophilia Competitive Intelligence Radar  
**Version:** 3.1  
**Date:** August 13, 2026  
> **v3.1 (Aug 13, 2026):** Aligned with Master Plan v4.0 B.Pharm domain-research integration — the pitch now reflects canonical haemophilia domain classification (disease/factor/inhibitor/population/modality), the evidence-maturity ladder (regulatory > peer-review/registry > congress > company > media), access-as-separate-event (approval ≠ reimbursement ≠ availability ≠ access), the 19 Red-Team evidence checks, and the seven-question output (Q1–Q4 + evidence strength / uncertainty / watch-next). Six primary functions unchanged.
**Target Event:** Novo Nordisk GBS Hackathon 2026 (Problem Statement #3: "From Inbox Noise to Strategic Signal | Pilot Area: Haemophilia within Rare Disease")  
**Team:** MS Ramaiah Institute of Technology (MSRIT) — Cross-Disciplinary (2 CSE + 3 B.Pharm)

> [!IMPORTANT]
> **HISTORICAL REFERENCE DOCUMENT**  
> *Note: This document is preserved for historical presentation context. The sole canonical and authoritative master specification for MetaRadar is [METARADAR_MASTER_PLAN_v3.0.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/METARADAR_MASTER_PLAN_v3.0.md).*

---

## **1. EXECUTIVE SUMMARY & CORE POSITIONING**

### 1.1 Core Positioning Statement
> **MetaRadar is an intelligence radar that converts fragmented public signals into evidence-backed developments and role-specific actions.**

### 1.2 Central Distinction
> **A conventional AI system summarizes documents. MetaRadar builds an evidence story around a development.**

### 1.3 Key Competitive Statement
> **"If another team uses ChatGPT to summarize five articles, they have five summaries. MetaRadar turns those five signals into one evidence-backed development with a history, evidence challenges, expected next steps, missing-signal awareness and role-specific implications."**

*Nuanced Competitive Claim (Avoids absolute claims):*  
> **"In our comparison of the open-source solutions we evaluated, we did not find one combining these five analyses with a haemophilia-specific ontology and role-based intelligence workflow."**

---

## **2. RESTRUCTURED PITCH FLOW**

The overall intelligence flow of MetaRadar follows five distinct stages:

```
PUBLIC SIGNALS
   │ (PubMed, NewsAPI, ClinicalTrials.gov, FDA, EMA, Reddit, Congress Repositories)
   ▼
ENTITY & EVENT UNDERSTANDING
   │ (spaCy ScispaCy NER + Haemophilia Pharma Ontology mapping)
   ▼
FIVE INTELLIGENCE ANALYSES
   │ (1. Confluence → 2. Lifecycle → 3. Red-Team → 4. Missing-Signal → 5. Stakeholder HITL)
   ▼
FACT / INTERPRETATION / SPECULATION
   │ (evidence-sufficiency gate; never present speculation as fact)
   ▼
FUNCTION ROUTING (six functions + extended)
   ▼
FOUR-QUESTION DECISION INTERFACE
   │ (Q1: What changed? → Q2: Why matters? → Q3: Which function? → Q4: What action?)
   ▼
FUNCTION-SPECIFIC INTELLIGENCE
   (Medical Affairs | Regulatory | Safety/PV | Market Access |
    Medical Communications | Leadership; extended: Commercial, R&D)
```

---

## **3. THE FIVE INTELLIGENCE ANALYSES (FRAMEWORK & QUESTIONS)**

Do **NOT** present these as five unrelated AI features. Present them as **five questions MetaRadar asks about every important development**:

```
                  ┌──────────────────────────────────────────────────┐
                  │           FIVE INTELLIGENCE MECHANISMS           │
                  │       "Five mechanisms feed one decision"        │
                  └────────────────────────┬─────────────────────────┘
                                           │
         ┌───────────────────┬─────────────┴───────┬───────────────────┐
         │                   │                     │                   │
┌────────▼─────────┐┌────────▼─────────┐┌──────────▼──────────┐┌───────▼──────────┐┌──────────────────┐
│  1. CONFLUENCE   ││   2. LIFECYCLE   ││ 3. RED-TEAM CONTRAD.││4. MISSING-SIGNAL ││5. STAKEHOLDER HITL│
│ "Are independent ││ "Where is this   ││ "What evidence      ││ "What should     ││ "Does system     │
│ streams pointing ││ development in   ││ challenges or       ││ have happened,   ││ relevance match  │
│ to same event?"  ││ its journey?"    ││ qualifies this?"    ││ but hasn't?"     ││ function thinking│
└──────────────────┘└──────────────────┘└─────────────────────┘└──────────────────┘└──────────────────┘
```

### Analysis 1: CONFLUENCE
* **Question Asked:** *"Are multiple independent evidence streams pointing to the same underlying development?"*
* **Explanation:** Multiple signals from sources such as publications, clinical trial registries, regulatory filings, congress abstracts, company press releases, or patient/access narratives are connected into one stronger signal rather than being counted as separate news items.
* **Haemophilia Example:** An ASH 2026 abstract on Hemgenix 3-year durability + a CSL Behring press release + an r/Hemophilia patient discussion occurring within 48 hours are merged into a single High-Confluence Gene Therapy Alert.

### Analysis 2: LIFECYCLE TRACKING
* **Question Asked:** *"Where is this development in its overall journey?"*
* **Progression Chain:**  
  `Announced → In Trial → Interim Result → Final Result → Congress/Publication → Regulatory Development → Approved → Post-Market / Discontinued`
* **Explanation:** MetaRadar connects isolated updates into a chronological development story so an analyst immediately sees where an asset sits and where it is going next.
* **Haemophilia Example:** mim8 (Novo Nordisk bispecific): Phase 3 trial initiation (2024) → Primary endpoint readout (Jan 2026) → Regulatory submission expected (Q3 2026).

### Analysis 3: RED-TEAM CONTRADICTION ANALYSIS
* **Question Asked:** *"Before we consider this signal important, what evidence challenges or qualifies it?"*
* **Explanation:** The system presents supporting evidence alongside contradictory or limiting evidence. It does not simply amplify an AI-generated positive conclusion; it actively looks for reasons the conclusion may be incomplete or overstated.
* **Haemophilia Example:** Primary trial claim: *"Sustained Factor IX expression at 3 years"* is presented alongside contradictory real-world cohort data: *"Declining Factor IX activity observed in 15% subset of patients at 36 months"*, flagged with a Devil's-Advocate AI review note.

### Analysis 4: MISSING-SIGNAL DETECTION
* **Question Asked:** *"What should have happened next, and has it actually happened?"*
* **Explanation:** Absence of an expected milestone after a trial or readout is automatically flagged. Absence is **not** automatically treated as proof of a problem; it becomes an alert requiring human review.
* **Haemophilia Example:** Phase 3 trial completed → expected regulatory submission within 180 days → 120 days pass with zero public filings → **WATCH item** created (monitoring signal, NOT a claim): *"Prolonged silence on expected submission — potential clinical query or manufacturing delay. Human review required."*

### Analysis 5: STAKEHOLDER LEARNING / HITL CALIBRATION
* **Question Asked:** *"Does the system's understanding of relevance match how the intended function actually thinks?"*
* **Flow:** `AI Prioritization → Stakeholder Feedback → Recalibration → Improved Future Routing`
* **Explanation:** This is not merely a thumbs-up/thumbs-down feature. Stakeholder ratings dynamically recalibrate role-relevance scoring weights over time so the system adapts to how Medical Affairs, Regulatory, or Market Access teams prioritize signals.

---

## **4. CONNECTION TO THE FOUR-QUESTION DECISION INTERFACE**

The Five Intelligence Mechanisms directly feed the Four-Question Decision Interface:

| Decision Question | Source Mechanism(s) | Operational Content Rendered in UI |
|---|---|---|
| **Q1 — WHAT CHANGED?** | Entity/Event Extraction + **Confluence** | Real-time signal feed, entity tags, signal type badges, converged multi-source alerts |
| **Q2 — WHY DOES IT MATTER?** | **Lifecycle** + **Red-Team Contradiction** + Ontology | Evidence strength, position on lifecycle timeline, competitive impact on Novo Nordisk portfolio, contradicting evidence & devil's advocate review |
| **Q3 — WHICH NOVO NORDISK FUNCTION SHOULD REVIEW IT?** | **Stakeholder Calibration (HITL)** + Matrix Routing | Calibrated function badges with confidence percentages (Medical Affairs, Regulatory, Safety/PV, Market Access, Medical Communications, Leadership; extended: Commercial, R&D) |
| **Q4 — WHAT INTERNAL ACTION MAY BE REQUIRED?** | **Missing-Signal** + Synthesized Evidence | AI-generated action suggestions based on evidence, lifecycle stage, and missing-signal alerts, prefaced *"Suggested — requires human review"* |

---

## **5. CORE PRESENTATION MESSAGES & COMPARISONS**

### 5.1 Main Presentation Message
> ❌ **Do NOT say:** *"We have five cool AI features."*  
> ✅ **SAY:** *"Five intelligence mechanisms feed one decision interface."*

### 5.2 Architecture Comparison

```
TRADITIONAL INTELLIGENCE DASHBOARD:
Sources ──────────────► Summaries ──────────────► Charts

METARADAR INTELLIGENCE RADAR:
Sources
   │
   ▼
Entity / Event Understanding (Haemophilia Ontology)
   │
   ▼
Evidence Confluence (Multi-source convergence)
   │
   ▼
Development Lifecycle (Timeline position & history)
   │
   ▼
Contradiction Analysis (Red-team devil's advocate)
   │
   ▼
Missing-Expected-Event Detection (Silence alerting)
   │
   ▼
Stakeholder Calibration (HITL weight learning)
   │
   ▼
Strategic Intelligence (Four-Question Decision Interface)
```

---

## **6. REVISED ARCHITECTURE PRESENTATION**

### 6.1 Conceptual Architecture (For Non-CS / B.Pharm Audience & Judges)

Present this conceptual diagram FIRST:

```
META RADAR
│
├── UNDERSTAND
│   ├── Entity extraction
│   └── Haemophilia ontology
│
├── CONNECT
│   ├── Confluence
│   └── Lifecycle
│
├── CHALLENGE
│   └── Red-Team contradiction analysis
│
├── DETECT
│   └── Missing signals
│
├── LEARN
│   └── Stakeholder calibration
│
└── FOUR QUESTIONS
    └── Role-specific intelligence
```

### 6.2 Technical Architecture (For CS / IT Technical Judges)

Show this technical diagram SECOND when judges ask about technical execution:

```
Next.js 15 (React 19, TypeScript, TailwindCSS 4, shadcn/ui)
   │
   ▼ REST API / WebSockets
FastAPI (Python 3.11 ASGI)
   │
   ▼ State Graph Orchestration
LangGraph 10-Agent Pipeline
   │ (Ingestion → Validation → NLP → Confluence → Lifecycle → Red-Team → Missing-Signal → Synthesis → Brief → Calibration)
   ├──► PostgreSQL 16 + pgvector (ACID Relational + 384-dim Vector Storage)
   │
   └─► Redis 7 (Hot Signal Cache 2h TTL + Rate Limiting)
        ▲
        │ Async Ingestion & Scheduled Triggers
Celery 5.3 + APScheduler
        ▲
        │ Public API Connectors (with tenacity exponential retries)
Public Data Sources (PubMed, NewsAPI, ClinicalTrials.gov, FDA, EMA, Reddit, Congress Repositories)
```

---

## **7. VERBATIM SPOKEN PITCH SCRIPT (FOR B.PHARM TEAM LEAD)**

> "MetaRadar is an AI-powered competitive intelligence radar for haemophilia.
>
> The problem isn't finding information. It's understanding whether scattered information represents a meaningful development.
>
> Most AI systems retrieve and summarize articles. MetaRadar builds an evidence story.
>
> Our haemophilia ontology understands relationships between therapies, mechanisms, companies, trials and disease context.
>
> Then five intelligence layers analyze each important development.
>
> Confluence determines whether independent sources point to the same underlying event.
>
> Lifecycle tracking shows where that development is in its journey.
>
> Red-Team analysis actively looks for contradictory or limiting evidence.
>
> Missing-Signal detection asks what should have happened next and alerts us when an expected milestone remains absent.
>
> Stakeholder Learning uses feedback from functions such as Medical Affairs and Regulatory to improve future prioritization.
>
> Every output is labeled Fact, Interpretation, or Speculation — speculation is never presented as fact, and when evidence is insufficient we say so.
>
> All of this feeds our Four-Question interface:
>
> What changed?
> Why does it matter?
> Who should review it?
> What action may be required?
>
> So MetaRadar doesn't simply answer 'What is the latest news?'
>
> It answers:
> 'What is developing, how strong is the evidence, what challenges it, where is it going, and what deserves our attention?'
>
> That's the difference between an AI news summarizer and an intelligence radar."

---

## **8. TECHNICAL JUDGE EXPLANATION SECTION (16 DEFENSE QUESTIONS)**

Every answer follows a strict 2-part structure:
1. **One-sentence non-technical answer** (for the B.Pharm lead to state clearly).
2. **Technical implementation details** (for CS/IT judges).

---

### Q1: Why LangGraph?
* **Non-Technical Answer:** LangGraph acts as a strict step-by-step manager that ensures all ten intelligence steps run in exact order without losing track of evidence.
* **Technical Implementation:** We use LangGraph (`langgraph 0.1+`) because standard chain-based orchestration (like LangChain LLMChain) is acyclic and stateless. LangGraph provides stateful, cyclic multi-agent graph execution with strict schema validation (`TypedDict` state), explicit node branching, conditional edges, and checkpoint persistence, allowing 10 specialized agents to pass structured state cleanly.

---

### Q2: Why PostgreSQL + pgvector?
* **Non-Technical Answer:** It stores both structured tables and AI text memory in one single database, keeping our system fast, reliable, and zero-cost.
* **Technical Implementation:** By enabling the `pgvector` extension on PostgreSQL 16, we perform 384-dimensional vector similarity search (`sentence-transformers/all-MiniLM-L6-v2`) alongside relational SQL queries in a single ACID-compliant database. This eliminates the operational overhead, dual-write consistency issues, and resource footprint of deploying a separate vector database like Weaviate or Pinecone.

---

### Q3: Why Redis?
* **Non-Technical Answer:** Redis provides ultra-fast memory storage so repeated user views load instantly without re-processing data.
* **Technical Implementation:** Redis 7 serves as an in-memory key-value cache with a 2-hour TTL for processed hot signals, rate-limiting counter for public API endpoints (e.g. 500 requests/day cap on NewsAPI), and transient pub/sub broker for Celery async tasks.

---

### Q4: How does confluence work?
* **Non-Technical Answer:** It checks if three or more independent sources — like a publication, a trial registry, and a news report — mention the same drug within 48 hours.
* **Technical Implementation:** Confluence Detection scans incoming signals in a rolling 48-hour window, grouping by extracted entity IDs (ontology-normalized). When signals spanning $\ge 3$ distinct `signal_type` categories (e.g. `congress_publication` + `regulatory_decision` + `patient_access_signal`) intersect on an entity, a `confluence_event` record is created in PostgreSQL with an aggregated severity score ($S_{conf} = \sum w_{type} \times \text{credibility}$).

---

### Q5: How does lifecycle tracking work?
* **Non-Technical Answer:** It places every new update on a chronological step-by-step timeline that tracks a drug from its first announcement to final approval.
* **Technical Implementation:** Lifecycle tracking uses a deterministic finite-state machine (FSM) defined per asset: `announced → in_trial → interim_result → final_result → congress_publication → regulatory_development → approved → post_market | discontinued`. The Lifecycle Agent maps extracted signal event metadata to transitions in `lifecycle_chains` and `lifecycle_events` tables, automatically computing `expected_next_event` and `expected_timeline_days`.

---

### Q6: How does contradiction detection work?
* **Non-Technical Answer:** It uses a specialized AI model that compares two claims about the same drug to see if they conflict with each other.
* **Technical Implementation:** Red-Team Contradiction Analysis uses zero-shot Natural Language Inference (NLI) via local `facebook/bart-large-mnli`. For pairs of signals linked to the same entity within a 90-day window, the agent evaluates premise-hypothesis pairs for `contradiction` probability. Pairs scoring $> 0.60$ trigger a `contradictions` entry with linked evidence chains and an automated devil's-advocate review prompt.

---

### Q7: How does missing-signal detection work?
* **Non-Technical Answer:** It calculates when a follow-up step should have happened and alerts us if an expected milestone stays silent for too long.
* **Technical Implementation:** Missing-Signal Detection compares the current state in `lifecycle_chains` against domain rules (`missing_signal_rules` table, e.g. Phase 3 results in $\rightarrow$ max 180 days lag for regulatory submission). If $\Delta t_{\text{last\_signal}} > t_{\text{max\_lag}}$, an alert is created with confidence scoring $C_{missing} = \min(0.40 + 0.002 \times \Delta t_{\text{silence}}, 0.95)$, explicitly flagged as requiring human review.

---

### Q8: How does stakeholder calibration work?
* **Non-Technical Answer:** When experts rate how relevant a signal was, MetaRadar adjusts its scoring formulas so future signals match expert judgment.
* **Technical Implementation:** `StakeholderCalibrationService` receives structured feedback (`POST /api/v1/feedback`) containing 1–5 ratings per role. The Calibration Agent executes an online gradient update on the scoring weight matrix in `scoring_weights`, adjusting role-signal affinity weights $\mathbf{W}_{role}$ and logging the recalibration event in `calibration_history` for full auditability.

---

### Q9: How is hallucination controlled?
* **Non-Technical Answer:** Every single claim in MetaRadar must link directly to a verified public source quote, and AI never generates facts on its own.
* **Technical Implementation:** We enforce strict grounding by anchoring all synthesis in retrieved context (RAG via pgvector cosine distance). Every output text span must map to a `source_id`, `source_url`, and verbatim text `excerpt`. The model temperature is locked to 0.0, and system prompts explicitly instruct the LLM to output "INSUFFICIENT EVIDENCE" if no matching source excerpt exists.

---

### Q10: How are sources made traceable?
* **Non-Technical Answer:** Every card on the dashboard has a clickable proof box showing the original article link, publication date, and exact quote.
* **Technical Implementation:** Every signal database row maintains an immutable `evidence_chain` JSONB object containing `source_name`, `source_url`, `published_at`, `extracted_quote`, `domain_credibility_score`, and `sha256_hash` of raw source text. These are rendered directly in Panel 2 and Panel 4 of the Four-Question UI.

---

### Q11: What happens when an API fails?
* **Non-Technical Answer:** If a public data source breaks or goes offline, MetaRadar retries automatically, uses recent cached data, or switches to a backup dataset so the app never crashes.
* **Technical Implementation:** Ingestion calls use `tenacity` exponential backoff (3 attempts: 2s, 4s, 8s timeout). If an external API fails, the backend seamlessly falls back to Redis hot cache (TTL 24h), then PostgreSQL `raw_signals_bronze` historical data, and finally to our pre-seeded 500-signal synthetic haemophilia demo dataset without throwing 500 errors.

---

### Q12: How does the architecture scale?
* **Non-Technical Answer:** Because our components are lightweight and decoupled, we can process thousands of signals simultaneously across multiple background workers.
* **Technical Implementation:** The architecture separates API serving (FastAPI ASGI under Uvicorn) from async processing (Celery task queues backed by Redis). Read queries hit indexed PostgreSQL/pgvector views or Redis cache. Adding ingestion volume requires scaling Celery worker processes without modifying backend API code.

---

### Q13: Why is this different from a normal RAG chatbot?
* **Non-Technical Answer:** A RAG chatbot only answers questions when you ask it; MetaRadar actively monitors, connects, flags contradictions, and routes signals to the right team automatically.
* **Technical Implementation:** A standard RAG chatbot is passive (User Question $\rightarrow$ Embed $\rightarrow$ Retrieve $\rightarrow$ Generate). MetaRadar is an autonomous intelligence pipeline executing 10 graph-orchestrated agents continuously, constructing stateful lifecycle chains, cross-source confluences, contradiction checks, and silence alerts without user prompting.

---

### Q14: Why is this different from a news dashboard?
* **Non-Technical Answer:** A news dashboard shows a list of individual headlines; MetaRadar turns scattered headlines into an evidence story with clear next steps for Novo Nordisk.
* **Technical Implementation:** News dashboards display unlinked, flat article feeds sorted by timestamp. MetaRadar applies spaCy NER + pharma ontology mapping, 48-hour confluence clustering, FSM lifecycle progression, NLI contradiction detection, and HITL weight calibration to convert raw feeds into strategic decision panels.

---

### Q15: Why is this different from ChatGPT/Claude simply summarizing articles?
* **Non-Technical Answer:** Summarizing five articles gives you five separate summaries; MetaRadar combines them, checks if they contradict, tracks where the drug is on its timeline, and tells each function what to do.
* **Technical Implementation:** Document summarization operates on individual text inputs without domain context or history. MetaRadar performs multi-document entity normalization against a specialized Haemophilia ontology, tracks temporal state across months of data, performs pairwise NLI contradiction checks, and applies role-routing matrices calibrated by Novo Nordisk stakeholder feedback.

---

### Q16: Why is this feasible within a one-month hackathon?
* **Non-Technical Answer:** We use lightweight, free, local open-source AI components with pre-curated fallback data so we don't waste time on complex cloud setups.
* **Technical Implementation:** MetaRadar relies exclusively on local CPU-executable models (spaCy `en_core_sci_md`, BART MNLI, MiniLM embeddings) running inside Docker Compose. By selecting PostgreSQL + pgvector over external vector databases and using standard Python frameworks (FastAPI + LangGraph), we eliminate cloud API dependencies, key management overhead, and deployment friction.

---

## **9. STORY-DRIVEN DEMO NARRATIVE (CONTINUOUS HAEMOPHILIA STORY)**

To ensure judges understand that MetaRadar is an **evidence-to-decision system**, the presentation demo tells **one single haemophilia story** rather than demonstrating disconnected features.

```
                    DEMO STORYLINE: "THE HEMGENIX 3-YEAR DURABILITY SHIFT"
                                    
 Signals Arrive      Confluence      Lifecycle       Red-Team      Missing-Signal    Four Questions    HITL Calibration
 ┌──────────┐       ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
 │ PubMed,  │──────►│ 3 signals│───►│ Results  │───►│ Contradd.│───►│ Submission  │──►│ Q1: What     │──►│ Med Affairs  │
 │ ASH,     │       │ merged in│    │ stage    │    │ flagged: │    │ silence     │   │ Q2: Why      │   │ feedback     │
 │ Reddit   │       │ 48 hours │    │ tracked  │    │ waning   │    │ alert       │   │ Q3: Who      │   │ recalibrates │
 └──────────┘       └──────────┘    └──────────┘    └──────────┘    └─────────────┘   │ Q4: Action   │   │ routing      │
                                                                                      └──────────────┘   └──────────────┘
```

### Step-by-Step Demo Walkthrough:

1. **Step 1: Ingestion & Public Signal Arrival**
   * *Presenter:* "Notice three new public signals arriving: an ASH 2026 abstract reporting 3-year Factor IX durability data for CSL Behring's Hemgenix gene therapy, a CSL Behring press release, and a patient discussion on Reddit."

2. **Step 2: Confluence Connection**
   * *Presenter:* "Instead of listing three separate news cards, MetaRadar's **Confluence Engine** detects that all three signals converge on Hemgenix within a 48-hour window, merging them into one High-Confluence Strategic Alert."

3. **Step 3: Lifecycle Stage Tracking**
   * *Presenter:* "MetaRadar's **Lifecycle Tracker** connects this update to Hemgenix's historical timeline, moving its status from *Approved* to *Post-Market Durability Tracking* and showing where it stands relative to Novo Nordisk's concizumab and mim8."

4. **Step 4: Red-Team Contradiction Analysis**
   * *Presenter:* "Here is where conventional AI fails and MetaRadar excels. Our **Red-Team Contradiction Agent** compares the positive ASH abstract claim (*'Sustained Factor IX expression'*) with a real-world patient cohort publication (*'15% of patients show declining factor expression at 36 months'*). It surfaces BOTH evidence chains with a devil's-advocate review note."

5. **Step 5: Missing-Signal Detection + Watch-for-Next**
   * *Presenter:* "Simultaneously, MetaRadar checks expected follow-ups. A competitor gene therapy trial completed 150 days ago, but no regulatory filing has appeared. MetaRadar flags a **Missing-Signal Alert** as a WATCH item — *'monitoring signal, not a claim'*. It also honours stakeholder-defined watch rules: a stakeholder asked us to *'monitor this competitor Phase III programme for subsequent congress disclosures'* — a WATCH rule is created (status: watching), and when the next congress abstract arrives it links into the SAME development chain and notifies Medical Affairs + Medical Communications."

6. **Step 6: The Four-Question Decision Interface (relevance-based routing)**
   * *Presenter:* "All five mechanisms feed directly into our Four-Question Interface:
     * **Q1 What changed?** Hemgenix 3-year durability data & real-world cohort discrepancy (Confluence alert); ISTH 2026 FRONTIER4 abstract linked as NEW EVIDENCE for the existing trial development.
     * **Q2 Why does it matter?** Directly impacts Novo Nordisk's mim8 subcutaneous positioning vs single-dose gene therapy.
     * **Q3 Who should review it?** Not everyone — relevance-based routing. Medical Affairs (primary, 91%), Medical Communications (82%), Regulatory (64%), with an explicit routing reason: *'Clinical efficacy/safety data with potential implications for scientific understanding and future regulatory review.'*
     * **Q4 What action may be required?** Role-aware actions: *Suggested — Medical Affairs to draft briefing note; Medical Communications to prepare scientific FAQ.* (AI suggests, never executes; human review required.)"

7. **Step 7: Stakeholder Calibration (HITL) with visible BEFORE/AFTER**
   * *Presenter:* "Finally, watch Dr. Meera from Medical Affairs rate this signal. The demo shows a visible BEFORE/AFTER: priority Medium → High, routing Medical Affairs → Medical Affairs (primary) + Medical Communications (secondary), action Monitor → Monitor + prepare internal review, and a WATCH rule created for upcoming congress disclosures. `StakeholderCalibrationService` processes this feedback, recalibrates the weights, and instantly updates future routing confidence — calibration changes output, not just a feedback form."

*Closing Presenter Statement:*  
> **"You have just seen MetaRadar convert scattered public items into one evidence-backed development, complete with history, evidence challenges, missing milestone alerts, stakeholder-defined watch rules, and role-calibrated actions — never broadcasting everything to everyone. That is the power of MetaRadar."**

---

## **10. DOCUMENTATION AUDIT & CONSISTENCY CHECKLIST**

All project documentation files have been audited and verified for complete internal consistency:

| Document | Verified Alignment Status | Key Revisions Applied |
|---|---|---|
| `1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md` | ✅ Complete | Updated to 10-agent LangGraph pipeline, intelligence radar positioning, relative open-source claims |
| `2_SRS_Software_Requirements_Specification.md` | ✅ Complete | Updated purpose, scope, 10-agent pipeline definition, Five Analyses specifications, relative competitive wording |
| `3_SOFTWARE_DESIGN_DOCUMENT.md` | ✅ Complete | Added conceptual architecture before technical architecture, detailed 10-agent LangGraph pipeline, database schemas |
| `4_UI_DESIGN_DOCUMENT.md` | ✅ Complete | Updated positioning, Four-Question UI layout driven by 5 analyses, presenter notes |
| `5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md` | ✅ Complete | Replaced absolute claims with relative evaluated open-source comparison, 10-agent pipeline alignment |
| `6_NOVO_NORDISK_ANALYSIS_AND_HACKATHON_INTELLIGENCE.md` | ✅ Complete | Updated judge defense Q&A to 2-part non-technical first/technical second structure across 16 questions |
| `CLAUDE.md` & `.planning/PROJECT.md` | ✅ Complete | Synchronized project description, 10-agent pipeline list, and core value pitch line |
