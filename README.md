# MetaRadar

### From Inbox Noise to Strategic Signal

**AI-powered near-real-time competitive intelligence radar for Haemophilia within Rare Disease**

[![Hackathon](https://img.shields.io/badge/Novo%20Nordisk%20GBS%20Hackathon-2026-blue)](#)
[![Pilot](https://img.shields.io/badge/Pilot-Haemophilia%20A%20%26%20B-red)](#)
[![Status](https://img.shields.io/badge/Status-Hackathon%20Prototype-orange)](#)
[![Data](https://img.shields.io/badge/Data-Public%20%7C%20Synthetic-green)](#)

> **A conventional AI system summarizes documents. MetaRadar builds an evidence story around a development.**

MetaRadar converts fragmented public information about the haemophilia treatment landscape into **evidence-backed developments and role-specific intelligence**.

The prototype is designed for the **Novo Nordisk GBS Hackathon 2026 — Problem Statement #3**, with **Haemophilia A and Haemophilia B** as the Rare Disease pilot.

---

## Table of Contents

- [Problem](#problem)
- [Solution](#solution)
- [How MetaRadar Is Different](#how-metaradar-is-different)
- [Five Intelligence Mechanisms](#five-intelligence-mechanisms)
- [Four-Question Decision Framework](#four-question-decision-framework)
- [MVP Scope](#mvp-scope)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Data Sources](#data-sources)
- [Haemophilia Knowledge Layer](#haemophilia-knowledge-layer)
- [Stakeholder Calibration](#stakeholder-calibration)
- [Safety and Responsible AI](#safety-and-responsible-ai)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [Demo Scenario](#demo-scenario)
- [Validation](#validation)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [Documentation](#documentation)
- [Team](#team)

---

# Problem

The haemophilia treatment landscape is evolving across:

- Factor replacement therapies
- Extended-half-life factors
- Non-factor therapies
- Bispecific antibodies
- Anti-TFPI approaches
- RNAi therapies
- Gene therapies
- Clinical development
- Regulatory activity
- Congress presentations
- Scientific publications
- Patient and access narratives

Relevant information is distributed across different public sources.

The challenge is therefore not simply:

> "Can we find haemophilia news?"

The real challenge is:

> **"Can we determine whether scattered information represents a meaningful developing signal, why it matters, who should review it, and what action may be required?"**

---

# Solution

MetaRadar treats external information as **signals belonging to developing evidence stories**, rather than as isolated articles.

The high-level workflow is:

```text
                    PUBLIC SIGNALS
         News · Company announcements · Clinical trials ·
         Publications · Congresses · Regulatory · Patient/access
                         |
                     INGESTION
                         |
                     VALIDATION
                         |
                ENTITY + ONTOLOGY
                         |
              INTELLIGENCE WORKFLOW
                         |
        +----------------+----------------+
        |                |                |
    CONFLUENCE       LIFECYCLE        RED-TEAM
    (link to existing  (NEW DEV vs    (contradicting
     development?)     NEW EVIDENCE)   evidence)
        |                |                |
        +----------------+----------------+
                         |
            MISSING-SIGNAL + WATCH-FOR-NEXT
                         |
               EVIDENCE + PRIORITY
                         |
               FACT / INTERPRETATION / SPECULATION
                         |
                 FUNCTION ROUTING
         Medical Affairs · Regulatory · Safety/PV ·
         Market Access · Medical Communications · Leadership
                         |
                  FOUR QUESTIONS
                         |
             FUNCTION-SPECIFIC UI (six functions)
                         |
             STAKEHOLDER CALIBRATION (feedback
             updates relevance/routing/action/watch rules)
````

The MVP is intentionally constrained to a small number of public live sources and a synthetic fallback dataset so the complete workflow remains demonstrable within the four-week hackathon.

---

# How MetaRadar Is Different

A conventional AI workflow often looks like:

```text
Articles
   ↓
AI summaries
   ↓
Dashboard
```

MetaRadar instead attempts to reason over the relationship between signals:

```text
Public signals
      ↓
Entity + event understanding
      ↓
Evidence convergence
      ↓
Development lifecycle
      ↓
Contradictory / limiting evidence
      ↓
Expected-but-missing developments
      ↓
Stakeholder feedback
      ↓
Role-specific intelligence
```

The key distinction is:

> **MetaRadar does not simply ask "What was published?"**
>
> **It asks "What is developing, how strong is the evidence, what challenges the interpretation, what should we watch for, and who needs to act?"**

---

# Five Intelligence Mechanisms

The five mechanisms are not five unrelated AI features.

They are **five questions MetaRadar asks about an important development**.

## 1. Confluence Detection

### Question

> **Are multiple independent evidence streams pointing to the same underlying development?**

Signals from different source types can be connected into one underlying development.

For example:

```text
Scientific publication
        +
Company announcement
        +
Clinical-trial update
        ↓
ONE DEVELOPING SIGNAL
```

The system does not treat repeated reporting of the same announcement as equivalent to independent evidence.

For **congress and publication signals**, Confluence first asks *"is this part of an existing development?"* — a congress abstract, oral presentation, poster and publication from the same trial (e.g., FRONTIER4/denecimig at ISTH 2026) link into ONE development chain as new evidence events, never as four unrelated cards. Novo Nordisk's own public ISTH 2026 material (multiple presentations/analyses per development, incl. FRONTIER4/denecimig and Explorer10/concizumab) demonstrates why congress data must attach to its development lifecycle.

---

## 2. Signal Lifecycle Tracking

### Question

> **Where is this development in its overall journey?**

MetaRadar links related signals into a chronological development story.

Example:

```text
Announced
    ↓
In Trial
    ↓
Results
    ↓
Regulatory Review
    ↓
Approved
    ↓
Post-Market
```

This prevents users from viewing every update as an isolated event. Every lifecycle event records `event_type · event_date · development_id · source_id`; the system distinguishes a **NEW DEVELOPMENT** from **NEW EVIDENCE ABOUT AN EXISTING DEVELOPMENT** (e.g., a trial → congress abstract → oral presentation → poster → publication stays one timeline).

### First-class signal types

**CONGRESS** and **PUBLICATION** are canonical signal types, not generic news:

* Congress subtypes: congress abstract · oral presentation · poster · new congress data · updated congress analysis · presentation of previously known data · congress-related safety/efficacy/PRO/mechanism-dosing
* Publication subtypes: peer-reviewed · preprint · real-world evidence · post-hoc analysis · long-term follow-up · safety publication · patient-reported outcomes · mechanistic

Both participate in Confluence, Lifecycle, Red-Team, priority scoring, function routing, the evidence chain, and stakeholder calibration. Publications connect to their company, asset, trial, development, disease and patient population.

---

## 3. Red-Team Contradiction Analysis

### Question

> **What evidence challenges or qualifies our interpretation?**

For important signals, MetaRadar looks for evidence that:

* contradicts the claim
* limits the interpretation
* represents a different patient population
* provides a different outcome
* reduces confidence in the conclusion

The purpose is not to make the AI "prove itself correct."

The purpose is to prevent the system from presenting an overly confident interpretation without showing relevant counter-evidence.

---

## 4. Missing-Signal Detection + Watch-for-Next

### Question

> **What should have happened next, and has it actually happened?**

> **What should we watch for next?**

MetaRadar uses predefined development sequences and time-lag rules **plus stakeholder-defined watch expectations**.

Example:

```text
Phase 3 milestone
       ↓
Expected regulatory development
       ↓
No corresponding signal detected
       ↓
MISSING-SIGNAL ALERT (WATCH item)
```

A missing signal is **not treated as proof that something is wrong**.

It becomes a watch item requiring human review.

**Watch-for-Next (stakeholder-defined):** a stakeholder may say *"Monitor this competitor trial for subsequent congress disclosures."* MetaRadar stores a **WATCH RULE** — source_event → expected/interesting next event (e.g., congress disclosure) → monitoring window → responsible function → status. Statuses: `watching` · `new_evidence_detected` · `no_new_evidence` · `watch_expired` · `human_review_required`. When the next congress signal arrives it links into the SAME development chain (confluence/lifecycle) and the responsible functions are notified. If nothing appears: *"No subsequent congress evidence observed during the configured monitoring window."* — absence is never interpreted as proof that no activity occurred. Wording is limited to "Watch for / Expected/possible next evidence / Not observed yet".

---

## 5. Stakeholder Calibration

### Question

> **Does the system's understanding of relevance match stakeholder judgement?**

The AI produces an initial relevance and routing assessment.

A stakeholder persona can then provide feedback.

```text
AI assessment
      ↓
Stakeholder review
      ↓
Relevance / urgency / actionability
      ↓
Calibration
      ↓
Updated scoring
```

The hackathon prototype uses **simulated stakeholder feedback** rather than confidential Novo Nordisk information.

---

# Four-Question Decision Framework

All intelligence ultimately feeds one decision interface.

## Q1 — What changed?

A concise description of the important development.

## Q2 — Why does it matter?

Clinical, competitive and development context supported by evidence.

## Q3 — Which Novo Nordisk function should review it?

**Relevance-based routing — "Not every signal needs to go to everyone."**

MetaRadar first understands a signal, then determines which internal functions need to pay attention to it. It does NOT broadcast every update to every user:

```text
External Signal → Understand → Classify → Determine relevance → Route to relevant function(s) → Role-specific explanation/action
```

The MVP routes each signal to the six kickoff functions from **one intelligence engine**:

* Medical Affairs
* Regulatory
* Safety / Pharmacovigilance
* Market Access / Patient Access
* Medical Communications
* Leadership

Commercial, R&D, Clinical Development, Competitive Intelligence, and Strategy are retained in the routing matrix as **extended/secondary stakeholders** only — they never replace the six primary functions. Each signal identifies a **primary function** and **secondary functions[]**, with `function_relevance_score`, a **routing reason** (explainable: "why this function, why now"), and role-specific explanations — all sharing the same evidence chain. The initial routing matrix is a seed (major clinical efficacy → Medical Affairs + MedComms/Leadership; safety signal → Safety/PV + Medical Affairs/Regulatory; regulatory decision → Regulatory + Medical Affairs/Market Access/Leadership; patient outcome/QoL → Medical Affairs + Market Access/MedComms; congress data → Medical Affairs + MedComms/Regulatory; access/reimbursement event → Market Access + Leadership/Medical Affairs; major competitor development → Medical Affairs + Leadership; trial lifecycle change → Medical Affairs + Regulatory/Leadership) and is **adjustable through stakeholder calibration** — never a hard-coded universal rule.

## Q4 — What internal action may be required?

A suggested next step based on the available evidence.

**Human review is required.**

---

# MVP Scope

To keep the project executable within four weeks, the MVP is intentionally locked to:

| Component        | MVP                                         |
| ---------------- | ------------------------------------------- |
| Therapy area     | Haemophilia                                 |
| Diseases         | Haemophilia A + B                           |
| Functions        | Medical Affairs · Regulatory · Safety/PV ·  |
|                  | Market Access · Medical Communications ·    |
|                  | Leadership (one engine; extended:           |
|                  | Commercial, R&D)                            |
| Live sources     | NCBI PubMed (E-utilities) + NewsAPI +       |
|                  | ClinicalTrials.gov (LIVE); FDA/EMA/Congress/ |
|                  | Reddit ADAPTER-READY                        |
| Offline fallback | 500-signal synthetic dataset (SYNTHETIC)     |
| Intelligence     | Five mechanisms                             |
| UI               | Four-Question Decision Interface             |
| Signal model     | Fact / Interpretation / Speculation labels  |
| Feedback         | Simulated stakeholder calibration            |
| AI               | Local/open models                           |
| Deployment       | Docker Compose                              |

### Future extensions

The following are outside the locked MVP:

* Extended role activation (Commercial, R&D, and further functions as data-driven matrix rows)
* Additional live data connectors (full FDA/EMA/congress live integration)
* Custom model fine-tuning
* Large-scale predictive modelling
* Production pharmaceutical deployment
* Confidential/internal Novo Nordisk data

---

# Architecture

## Conceptual Architecture

```text
                         META RADAR
                             |
        +--------------------+--------------------+
        |                    |                    |
    UNDERSTAND            CONNECT             CHALLENGE
        |                    |                    |
   Entity extraction     Confluence          Red-Team
   Haemophilia ontology  Lifecycle           Contradiction
        |                    |                    |
        +--------------------+--------------------+
                             |
                          DETECT
                             |
                      Missing Signals
                             |
                           LEARN
                             |
                  Stakeholder Calibration
                             |
                             ↓
                    FOUR QUESTIONS
                             |
                             ↓
                  ROLE-SPECIFIC INTEL
```

## Technical Architecture

```text
                         Next.js 15
                    React + TypeScript
                             |
                             ↓
                          FastAPI
                             |
                             ↓
                    LangGraph Workflow
                             |
          +------------------+------------------+
          |                  |                  |
      Ingestion          Intelligence       Calibration
          |                  |                  |
          |          +-------+-------+          |
          |          |       |       |          |
          |      Confluence Lifecycle Red-Team |
          |                  |                  |
          |          Missing-Signal             |
          |                  |                  |
          +------------------+------------------+
                             |
                             ↓
                    PostgreSQL + pgvector
                             |
                  +----------+----------+
                  |                     |
              Semantic Search       Structured Data
                  |
                Redis
                  |
          Cache + Rate Limiting
```

---

# Technology Stack

| Layer                  | Technology                               |
| ---------------------- | ---------------------------------------- |
| Frontend               | Next.js 15                               |
| UI                     | React 19 + TypeScript                    |
| Styling                | Tailwind CSS                             |
| Components             | shadcn/ui                                |
| Backend                | FastAPI                                  |
| Language               | Python 3.11                              |
| Workflow               | LangGraph                                |
| Database               | PostgreSQL 16                            |
| Vector search          | pgvector                                 |
| **Role** | **Default** | **Alternative** |
|---|---|---|
| Reasoning / Four Questions / Athena | `google/gemma-3-4b-it` (Gemma 3 4B Instruct, **local GPU** — RTX 3050 4 GB VRAM, Q4/int4) | xAI Grok API (`LLM_PROVIDER=xai`; privacy-gated) |
| Degraded factual summary | `facebook/bart-large-cnn` | — |
| Batch summarization | `facebook/bart-large-cnn` | — |
| NLI | `facebook/bart-large-mnli` | — |
| NER | spaCy `en_core_sci_md` | — |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | — |
| Cache                  | Redis 7                                  |
| Scheduler              | APScheduler (single, in-process)         |
| HTTP                   | httpx                                    |
| Deployment             | Docker Compose                           |

The architecture intentionally keeps vector search inside PostgreSQL rather than introducing a separate vector database.

---

# Data Sources

## Source Tiers (honest labeling)

| Tier | Sources | Status |
| --- | --- | --- |
| **LIVE** | NCBI PubMed (E-utilities) · NewsAPI · ClinicalTrials.gov | Actually fetched on demo day (≥3 live, per SRS AC-1) |
| **OPTIONAL/EXTENSION** | PubMed Central (PMC) full-text services | Not an MVP source; only where full-text is genuinely needed |
| **ADAPTER-READY** | FDA (openFDA) · EMA · Congress archives (ASH/ISTH/WFH/EHA) · Reddit/advocacy | Connector scaffold + rate limits; may be seeded from synthetic for demo; never claimed as fully live unless it is |
| **SYNTHETIC-DEMO** | 500 curated, deterministic, labelled haemophilia signals | Offline demonstrations, API failure, rate-limit protection, reproducible testing; `is_synthetic=true`, never presented as real |

### NCBI PubMed / E-utilities (LIVE)

Used for: PubMed literature retrieval — scientific publications, clinical evidence, trial readouts, reviews, emerging treatment evidence. **PubMed Central (PMC) APIs/services for eligible full-text content are an optional extension**, not the same endpoint as PubMed literature retrieval.

### NewsAPI (LIVE)

Used for: industry news, company announcements, competitive developments, public announcements. Quota-aware connector (free tier is modest; degrades to cache/synthetic).

### ClinicalTrials.gov (LIVE)

Used for: trial registrations, status changes, protocol amendments, enrolment signals. Free keyless public v2 API.

### Synthetic Fallback

A curated synthetic dataset is maintained for offline demonstrations, API failure, rate-limit protection, reproducible testing, and feature demonstrations. The fallback dataset is never presented as real-world Novo Nordisk information.

---

# Haemophilia Knowledge Layer

The B.Pharm team maintains a haemophilia-specific ontology connecting:

```text
Disease
   |
   +-- Haemophilia A
   +-- Haemophilia B

Therapy
   |
   +-- Factor replacement
   +-- Extended half-life factor
   +-- Bispecific / non-factor
   +-- Anti-TFPI
   +-- RNAi
   +-- Gene therapy

Asset
   |
   +-- Mechanism
   +-- Company
   +-- Indication
   +-- Development stage
   +-- Competitor relationships
```

Example relationship:

```text
emicizumab
    ↓
bispecific antibody
    ↓
Haemophilia A
    ↓
Roche
```

The ontology helps prevent the system from treating every mention of "haemophilia" as equally meaningful.

## Domain Classification (v4.0 — from B.Pharm research)

Every normalized signal carries canonical haemophilia domain fields — populated only when supported by evidence, **never guessed**:

- **Disease:** Haemophilia A · B · Both · Unknown (bare "haemophilia" → `unknown` until entity resolution via source/product/trial/context)
- **Factor:** FVIII · FIX · Unknown
- **Inhibitor status:** With inhibitor · Without inhibitor · Mixed · Unknown — a core segmentation variable (WFH maintains separate guidance for inhibitors, outcome assessment, and AAV gene therapy)
- **Population:** Adult · Adolescent · Child · Other/Unknown (where available)
- **Therapy/modality:** Factor replacement · EHL factor · Non-factor · Bispecific antibody · siRNA · Gene therapy · AAV · Lentiviral · Gene editing · Other

## Evidence Maturity (v4.0)

Every important signal carries `source_type` · `source_authority` · `evidence_maturity` · `source_date`. Maturity is an **evidence-context indicator, not a truth ranking**:

| Tier | Source |
|---|---|
| **Very High** | Regulatory decision / official regulatory assessment |
| **High** | Peer-reviewed publication · ClinicalTrials.gov structured update |
| **Medium/High** | Congress abstract/presentation |
| **Medium** | Official company announcement |
| **Lower** | Secondary media / commentary |

A congress abstract can be extremely important but preliminary; a company announcement is an important early signal, never independently verified evidence. Confidence upgrades only on peer-reviewed/registry/regulatory confirmation.

## Access Is Separate From Approval (v4.0)

> **Approval ≠ Reimbursement ≠ Commercial availability ≠ Actual patient access.**

Access is tracked as a distinct intelligence event with its own signal types: `ACCESS_REIMBURSEMENT_EVENT` · `RESTRICTED_REIMBURSEMENT` · `SUPPLY_ACCESS_RISK` · `GEOGRAPHIC_ACCESS_GAP` · `BUDGET_IMPACT_SIGNAL` · `OUTCOME_BASED_ACCESS_MODEL` · `REAL_WORLD_ACCESS_GAP` · `ACCESS_SUPPORT`, each with country/jurisdiction, effective date, restrictions, and intended-vs-actual access. The Red-Team layer enforces the approval/access distinction (checks M/N/O).

---

# Stakeholder Calibration

The prototype uses a Human-in-the-Loop approach.

Example:

```text
AI:
Signal relevance = 82%

Medical Affairs Persona:
Relevance = 5/5
Urgency = 4/5
Actionability = 5/5
```

Feedback is stored and used by the calibration service to adjust role-relevance scoring. **Stakeholders can influence priority, routing, actions, watch rules and relevance criteria** — a comment such as *"monitor this competitor trial for upcoming congress disclosures"* creates a watch rule and visibly changes the output (BEFORE/AFTER comparison shown in the demo).

The prototype does **not** claim to have learned from confidential Novo Nordisk stakeholder data.

---

# Safety and Responsible AI

MetaRadar is a hackathon prototype.

## Allowed data

* Public information
* Public APIs
* Public scientific publications
* Public company announcements
* Mock data
* Synthetic data

## Prohibited data

* Confidential Novo Nordisk strategy
* Internal forecasts
* Patient-level data
* Non-public information
* Confidential documents

## AI safeguards

MetaRadar is designed to:

* preserve source links
* retain evidence excerpts
* expose supporting evidence
* expose contradictory evidence
* label every output FACT / INTERPRETATION / SPECULATION (never present speculation as fact)
* run an evidence-sufficiency gate: insufficient evidence → "Insufficient evidence to support an interpretation."
* distinguish missing-signal WATCH items (monitoring signals, not claims) from confirmed events
* require human review for recommended actions (controlled action vocabulary)
* use synthetic stakeholder personas in the prototype
* degrade gracefully when external sources fail

**MetaRadar is INTERNAL DECISION SUPPORT ONLY.** It must not: provide treatment recommendations; make medical conclusions; claim product superiority without appropriate evidence; make unsupported competitor comparisons; determine safety causality; replace expert review; or autonomously execute business actions. For safety/regulatory/high-impact signals: AI suggests → human reviews → human decides. MetaRadar is **not** intended to make autonomous medical, regulatory, safety, commercial, or patient-care decisions.

---

# Project Structure

A recommended repository layout is:

```text
metaradar/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── public/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agents/
│   │   ├── intelligence/
│   │   ├── ontology/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── data/
│   ├── synthetic/
│   └── ontology/
│
├── workers/
│
├── docker-compose.yml
│
├── docs/
│   ├── METARADAR_MASTER_PLAN_v5.0.md
│   ├── SRS.md
│   ├── SDD.md
│   └── presentation/
│
├── .env.example
├── .gitignore
└── README.md
```

Adjust this structure to the actual repository before committing it.

---

# Getting Started

## Prerequisites

Recommended development environment:

* Git
* Docker Desktop
* Docker Compose
* Node.js 20.9+
* Python 3.11+

Next.js currently documents Node.js 20.9 as the minimum for the current installation flow. ([Next.js][2])

Docker is the preferred route for the complete local stack.

---

# Configuration

Create a local environment file:

```bash
cp .env.example .env
```

Configure the public API credentials required by the connectors.

Example:

```env
# Application
APP_ENV=development

# Database
DATABASE_URL=postgresql://metauser:metapass@postgres:5432/metaradar

# Redis
REDIS_URL=redis://redis:6379

# Public data sources
NEWSAPI_KEY=your_newsapi_key

# Model configuration (all local by default, zero API cost)
# Reasoning layer (provider-agnostic): local | xai | auto
LLM_PROVIDER=local
# Reasoning LLM (local default, GPU-first): narrative synthesis, Four-Question briefs, Ask Athena
LOCAL_LLM_MODEL=google/gemma-3-4b-it
LOCAL_LLM_TASK=text-generation
# Gemma runs on the local GPU (NVIDIA RTX 3050, 4 GB VRAM) as Q4/int4.
# 4 GB VRAM does NOT guarantee inference — on init/failure the provider chain
# falls back to Grok (if enabled) → BART degraded factual → source + human review.
LLM_DEVICE=cuda:0
LLM_DTYPE=int4
MAX_CONTEXT_TOKENS=4096
MAX_OUTPUT_TOKENS=1024
# Optional hosted reasoning provider (xAI Grok) — only when LLM_PROVIDER=xai|auto.
# Grok calls are gated by the external-LLM privacy gate (public/synthetic data only).
XAI_API_KEY=
XAI_MODEL=
XAI_TIMEOUT=30
# Fast batch summarizer (also the degraded factual fallback if no reasoning provider is available)
SUMMARIZER_MODEL=facebook/bart-large-cnn
SUMMARIZER_TASK=summarization
```

Never commit real API keys or secrets.

---

# Running with Docker

From the repository root:

```bash
docker compose up --build
```

The expected local services are:

```text
Frontend
http://localhost:3000

Backend
http://localhost:8000

PostgreSQL
localhost:5432

Redis
localhost:6379
```

The exact ports should be verified against the repository's current `docker-compose.yml`.

To stop the system:

```bash
docker compose down
```

To remove persistent database volumes during a clean reset:

```bash
docker compose down -v
```

---

# Running Without Live APIs

MetaRadar includes a synthetic fallback dataset for reproducible demonstrations.

Use the project's configured fallback/demo mode when:

* API credentials are unavailable
* an external API is rate-limited
* internet access is unavailable
* deterministic demo data is required

The fallback dataset should always be clearly labelled as synthetic.

---

# Demo Scenario

The primary demonstration follows one evolving haemophilia development.

```text
1. Public signals arrive (news · trials · publications · congresses · regulatory)
          ↓
2. Entity extraction identifies the asset/company
          ↓
3. Confluence connects related signals — and links congress/publication
   signals to their existing development (NEW EVIDENCE, not a new card)
          ↓
4. Lifecycle places the development in context (event_type/event_date/
   development_id/source_id recorded per event)
          ↓
5. Red-Team searches for contradictory/limiting evidence
          ↓
6. Missing-Signal checks expected milestones + stakeholder watch rules
   (Watch-for-Next: statuses watching → new_evidence_detected / no_new_evidence)
          ↓
7. Evidence + priority: every claim labeled FACT / INTERPRETATION / SPECULATION
          ↓
8. Four Questions convert evidence into intelligence
          ↓
9. Function routing: primary + secondary functions with a routing reason
   ("not every signal goes to everyone")
          ↓
10. Stakeholder feedback recalibrates priority/routing/action/watch rules
    (visible BEFORE/AFTER change)
```

The demo should focus on one coherent story rather than displaying unrelated news items.

---

# Validation

The prototype should be evaluated at both technical and intelligence levels.

## The Five Hackathon Success Metrics

1. **Source-linked summaries = 100%** — every high-priority AI insight carries source name, URL, publication date, source type, excerpt, evidence level, confidence, timestamp, AI-generated label.
2. **Classification accuracy ≥ 85%** — on a B.Pharm-labelled dataset (disease · patient type · signal type · priority · impacted function) with accuracy, precision, recall, confusion matrix.
3. **Top-signal discovery time ≤ 5 minutes** — reproducible test on a 100-signal weekly batch vs a manual browsing baseline.
4. **Confidential / patient data = 0 (evaluation target)** — public and synthetic data only; a dedicated PII/PHI detection + redaction layer runs before persistence (spaCy NER contributes to entity detection but is not a guaranteed scrubber; low-confidence content is rejected/quarantined); audit scan. A target, not a mathematical guarantee.
5. **Stakeholder-calibrated improvement** — measurable routing/priority improvement before vs after feedback.

These are the primary success metrics; engineering latency targets support them, they do not replace them.

## Technical

Track:

* API response time
* database query time
* cache hit rate
* signal processing throughput
* source availability
* workflow failures
* data freshness

## Intelligence

Track:

* entity extraction quality
* confluence quality
* lifecycle state accuracy
* contradiction false-positive rate
* missing-signal false-positive rate
* source traceability
* stakeholder routing feedback

The project prioritizes **verifiable measurements** over unsupported claims about model quality.

---

# Limitations

### Public API limitations

NewsAPI has request limits. Redis caching and periodic polling reduce unnecessary requests.

### Reasoning providers

MetaRadar's reasoning layer is provider-agnostic (default local, no API key required): `LLM_PROVIDER=local` uses **Gemma 3 4B Instruct** locally; `LLM_PROVIDER=xai` uses the **hosted xAI Grok API**; `LLM_PROVIDER=auto` tries Gemma then Grok. All external (Grok) calls pass a mandatory privacy gate — only public or synthetic prototype data may leave the machine; blocked content falls back to local Gemma → BART → source-only display. Grok responses use JSON-Schema structured outputs and are validated at application level (evidence IDs, source URLs, controlled vocabularies, no fabricated entities). Every output records model metadata (provider/model/fallback reason).

Local models may provide lower-quality generation than larger commercial models, particularly on constrained hardware. MetaRadar defaults to Gemma 3 4B Instruct (Q4/int4) on the **local GPU — NVIDIA RTX 3050, 4 GB VRAM**. **4 GB VRAM does not guarantee inference success** — model weights, KV cache, runtime overhead, and context length are budgeted separately (`LLM_DEVICE`, `LLM_DTYPE`, `MAX_CONTEXT_TOKENS`, `MAX_OUTPUT_TOKENS`); if Gemma cannot initialize or execute, the provider chain falls back to Grok (if configured) → BART degraded factual → source-grounded factual signal + human-review flag. The application never crashes because a model does not fit. When no reasoning provider is available the system enters **degraded mode — BART performs factual summarization only** (it is NOT a reasoning-equivalent replacement; no unsupported interpretation and no reasoning-based action recommendation are generated; the UI shows "AI reasoning unavailable — showing source-grounded factual summary"). Degraded mode is clearly marked and human review applies where necessary.

### Stakeholder feedback

Actual internal Novo Nordisk stakeholder data is not available to the prototype.

Stakeholder calibration is therefore demonstrated with synthetic/persona-driven feedback.

### Missing-signal detection

Absence is inherently ambiguous.

A missing expected event may result from:

* delayed public disclosure
* incomplete source coverage
* changed company strategy
* data-source limitations
* genuinely delayed development

Therefore missing-signal alerts require human review.

### Prototype status

MetaRadar is a hackathon prototype and is not a production pharmaceutical intelligence platform.

---

# Roadmap

## Phase 1 — Hackathon MVP

* Haemophilia A/B (disease + inhibitor/patient-type classification)
* Six functions (Medical Affairs, Regulatory, Safety/PV, Market Access, Medical Communications, Leadership) from one engine
* Relevance-based routing (primary/secondary functions + routing reason; seed matrix adjustable via calibration)
* Congress + Publication as first-class signal types with subtypes, linked to development lifecycles
* LIVE sources: NCBI PubMed (E-utilities) · NewsAPI · ClinicalTrials.gov (+ adapters, + synthetic; PMC full-text optional)
* Haemophilia ontology
* Fact / Interpretation / Speculation labeling + evidence-sufficiency gate
* Confluence · Lifecycle · Red-Team · Missing-Signal (WATCH items + stakeholder watch rules)
* Role-specific actions (controlled vocabulary per function)
* Stakeholder calibration (visible BEFORE/AFTER; influences priority/routing/action/watch)
* Weekly function-filtered digest · watchlists
* Four-Question UI · Synthetic fallback · Source traceability

## Phase 2 — Future Expansion

Potential extensions include:

* Full live integration of FDA/EMA/congress adapters
* Extended role activation (Commercial, R&D, further functions)
* More sophisticated temporal knowledge graphs
* Expanded conversational intelligence
* Additional model providers
* Production hardening and enterprise deployment

---

# Four-Week Development Plan

## Week 1 — Foundation

* Docker Compose
* FastAPI
* Next.js
* PostgreSQL + pgvector
* Redis
* NCBI PubMed (E-utilities) connector
* NewsAPI connector
* Raw signal persistence
* Basic dashboard
* Haemophilia ontology foundation

**Milestone:** Live signals appear on the dashboard.

## Week 2 — Intelligence Core

* Entity extraction
* Ontology enrichment
* Deduplication
* Confluence detection
* Lifecycle tracking
* Four-Question interface

**Milestone:** Multiple documents become one development story.

## Week 3 — Differentiation

* Red-Team contradiction analysis
* Missing-signal detection
* Stakeholder calibration
* Evidence-chain display

**Milestone:** MetaRadar challenges, tracks and prioritizes its own intelligence.

## Week 4 — Hardening

* API fallback
* Synthetic demo mode
* Testing
* Logging
* Performance tuning
* UI polish
* Citation verification
* End-to-end demo rehearsal

**Milestone:** Reliable hackathon demonstration.

---

# Documentation

The repository contains deeper documentation for different audiences.

| Document                              | Purpose                                           |
| ------------------------------------- | ------------------------------------------------- |
| `METARADAR_MASTER_PLAN_v5.0.md`       | Canonical project specification                   |
| `SRS.md`                              | Functional and non-functional requirements        |
| `SDD.md`                              | Detailed software architecture and implementation |
| `GAP_ANALYSIS_AND_OPTIMIZATIONS.md`   | Architectural decisions, risks and resolutions    |
| `PITCH_AND_PRESENTATION_NARRATIVE.md` | Demo and presentation narrative                   |

**Important:** The Master Plan is the authoritative specification. Other documents are supporting or historical references.

---

# Team

**MS Ramaiah Institute of Technology**

Cross-disciplinary team:

* 2 × Computer Science & Engineering
* 3 × Bachelor of Pharmacy

The team structure intentionally combines:

### B.Pharm (domain owners — kickoff assignment)

* **Sanjana** — Medical Affairs perspective; signal importance; priority rules; function routing; suggested actions; stakeholder questions
* **Ishaaq** — haemophilia treatment map; disease classification; inhibitor status; asset/product categories; lifecycle stages; signal types; expected-event rules
* **Usha** — evidence quality; Fact/Interpretation/Speculation rules; Red-Team questions; safety context; patient/access context; human-review triggers
* Their combined output becomes the labelled evaluation dataset and domain rules

Shared B.Pharm contributions: haemophilia domain knowledge, treatment landscape, pharma ontology, signal relevance, clinical interpretation, stakeholder perspective.

### CSE

* Data ingestion
* NLP/entity extraction
* Backend
* Workflow orchestration
* Database/vector search
* Frontend
* Testing and deployment

The goal is not to add AI to a pharmaceutical dashboard.

The goal is to combine **pharmaceutical domain reasoning with computational intelligence**.

---

# Core Principle

> **MetaRadar does not replace human judgement.**
>
> **It reduces the effort required to find, connect, challenge and interpret important external developments.**

```text
SCATTERED INFORMATION
        ↓
   EVIDENCE STORY
        ↓
  WHAT CHANGED?
        ↓
 WHY DOES IT MATTER?
        ↓
 WHO SHOULD REVIEW?
        ↓
 WHAT ACTION MAY BE REQUIRED?
        ↓
     HUMAN REVIEW
```

---

## Hackathon

**Novo Nordisk GBS Hackathon 2026**

**Problem Statement #3 — From Inbox Noise to Strategic Signal**

**Pilot Area — Haemophilia within Rare Disease**

**Team — Aura Pharmers**  
**Team Lead — Sanjana Rathore B.**

---
```