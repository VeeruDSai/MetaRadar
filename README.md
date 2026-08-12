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
                   /              \
               PubMed            NewsAPI
                   \              /
                    \            /
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
        |                |                |
        +----------------+----------------+
                         |
                  MISSING-SIGNAL
                         |
                     SYNTHESIS
                         |
              STAKEHOLDER CALIBRATION
                         |
                  FOUR QUESTIONS
                         |
                MEDICAL AFFAIRS UI
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

This prevents users from viewing every update as an isolated event.

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

## 4. Missing-Signal Detection

### Question

> **What should have happened next, and has it actually happened?**

MetaRadar uses predefined development sequences and time-lag rules.

Example:

```text
Phase 3 milestone
       ↓
Expected regulatory development
       ↓
No corresponding signal detected
       ↓
MISSING-SIGNAL ALERT
```

A missing signal is **not treated as proof that something is wrong**.

It becomes a watch item requiring human review.

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

The MVP is focused on **Medical Affairs**.

The architecture allows future extension to:

* Regulatory
* Market Access
* Commercial Strategy
* R&D

## Q4 — What internal action may be required?

A suggested next step based on the available evidence.

**Human review is required.**

---

# MVP Scope

To keep the project executable within four weeks, the MVP is intentionally locked to:

| Component        | MVP                               |
| ---------------- | --------------------------------- |
| Therapy area     | Haemophilia                       |
| Diseases         | Haemophilia A + B                 |
| Primary role     | Medical Affairs                   |
| Live sources     | PubMed Central API + NewsAPI      |
| Offline fallback | 500-signal synthetic dataset      |
| Intelligence     | Five mechanisms                   |
| UI               | Four-Question Decision Interface  |
| Feedback         | Simulated stakeholder calibration |
| AI               | Local/open models                 |
| Deployment       | Docker Compose                    |

### Future extensions

The following are outside the locked MVP:

* Additional business functions
* Additional live data connectors
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
| Embeddings             | `sentence-transformers/all-MiniLM-L6-v2` |
| NLP                    | spaCy                                    |
| Reasoning LLM          | `google/gemma-3-4b-it` (Gemma 3 4B Instruct) |
| Batch summarizer       | `facebook/bart-large-cnn` (CPU + fallback) |
| Contradiction analysis | `facebook/bart-large-mnli`               |
| Cache                  | Redis 7                                  |
| Workers                | Celery                                   |
| Scheduler              | APScheduler                              |
| HTTP                   | httpx                                    |
| Deployment             | Docker Compose                           |

The architecture intentionally keeps vector search inside PostgreSQL rather than introducing a separate vector database.

---

# Data Sources

## MVP Live Sources

### PubMed Central API

Used for:

* Scientific publications
* Clinical evidence
* Trial readouts
* Reviews
* Emerging treatment evidence

### NewsAPI

Used for:

* Industry news
* Company announcements
* Competitive developments
* Public announcements

## Synthetic Fallback

A curated synthetic dataset is maintained for:

* Offline demonstrations
* API failure
* Rate-limit protection
* Reproducible testing
* Feature demonstrations

The fallback dataset is not presented as real-world Novo Nordisk information.

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

Feedback is stored and used by the calibration service to adjust role-relevance scoring.

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
* distinguish missing-signal alerts from confirmed events
* require human review for recommended actions
* use synthetic stakeholder personas in the prototype
* degrade gracefully when external sources fail

MetaRadar is **not** intended to make autonomous medical, regulatory, safety, commercial, or patient-care decisions.

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
│   ├── METARADAR_MASTER_PLAN_v3.0.md
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

# Model configuration (all local, zero API cost)
# Reasoning LLM: narrative synthesis, Four-Question briefs, Ask Athena
LOCAL_LLM_MODEL=google/gemma-3-4b-it
LOCAL_LLM_TASK=text-generation
# Fast batch summarizer (also the automatic fallback if Gemma is unavailable)
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
1. Public signals arrive
          ↓
2. Entity extraction identifies the asset/company
          ↓
3. Confluence connects related signals
          ↓
4. Lifecycle places the development in context
          ↓
5. Red-Team searches for contradictory/limiting evidence
          ↓
6. Missing-Signal checks expected milestones
          ↓
7. Four Questions convert evidence into intelligence
          ↓
8. Medical Affairs reviews the recommendation
          ↓
9. Stakeholder feedback recalibrates future routing
```

The demo should focus on one coherent story rather than displaying unrelated news items.

---

# Validation

The prototype should be evaluated at both technical and intelligence levels.

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

### Local model limitations

Local models may provide lower-quality generation than larger commercial models, particularly on constrained hardware. MetaRadar defaults to Gemma 3 4B Instruct for reasoning and automatically falls back to BART (batch summarization) when the larger model cannot be loaded, so the demo degrades gracefully.

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

* Haemophilia A/B
* Medical Affairs
* PubMed
* NewsAPI
* Haemophilia ontology
* Confluence
* Lifecycle
* Red-Team
* Missing-Signal
* Stakeholder calibration
* Four-Question UI
* Synthetic fallback
* Source traceability

## Phase 2 — Future Expansion

Potential extensions include:

* Regulatory sources
* ClinicalTrials.gov
* FDA/EMA sources
* Congress archives
* Patient/access sources
* Regulatory Affairs
* Market Access
* Commercial Strategy
* R&D
* More sophisticated temporal knowledge graphs
* Expanded conversational intelligence
* Additional model providers

---

# Four-Week Development Plan

## Week 1 — Foundation

* Docker Compose
* FastAPI
* Next.js
* PostgreSQL + pgvector
* Redis
* PubMed connector
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
| `METARADAR_MASTER_PLAN_v3.0.md`       | Canonical project specification                   |
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

### B.Pharm

* Haemophilia domain knowledge
* Treatment landscape
* Pharma ontology
* Signal relevance
* Clinical interpretation
* Stakeholder perspective

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

---
```