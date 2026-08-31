<div align="center">

<img src="frontend/public/icon.svg" alt="MetaRadar" width="96">

# MetaRadar

### From Inbox Noise to Strategic Signal

**Evidence-grounded competitive intelligence for haemophilia A & B**

Built for the **Novo Nordisk GBS Hackathon 2026 — Problem Statement #3: Rare Disease Competitive Intelligence Radar**

</div>

---

## Why MetaRadar

Pharmaceutical teams do not have an information shortage. They have a **decision latency problem**.

Clinical-trial updates, regulatory actions, publications, safety information, and industry news arrive through separate sources. The difficult task is determining:

1. **What changed?**
2. **Why does it matter?**
3. **Who needs to review it?**
4. **What action may be required?**

MetaRadar turns those fragmented public signals into **evidence-linked, prioritized, role-scoped decision intelligence** for cross-functional haemophilia teams.

> **A conventional AI summarizes documents. MetaRadar builds an evidence story around a development.**

---

## What the Prototype Does

MetaRadar continuously ingests public biomedical and biopharma information, processes it through an 11-node intelligence pipeline, and presents the resulting signals through stakeholder-specific workspaces.

### Core capabilities

| Capability | What it does |
|---|---|
| **Multi-source ingestion** | Connects to PubMed, ClinicalTrials.gov, FDA, EMA, NewsAPI, BioPharma Dive, FiercePharma, and ET Pharma |
| **Evidence linkage** | Connects related signals across independent sources using semantic similarity and entity relationships |
| **Lifecycle tracking** | Tracks assets across clinical and regulatory development stages |
| **Contradiction analysis** | Uses NLI-based analysis to surface evidence that challenges or qualifies claims |
| **Missing-signal detection** | Tracks expected milestones and flags overdue or absent events |
| **Priority scoring** | Produces an explainable 0–100 signal priority score |
| **Stakeholder routing** | Routes signals to Medical, Regulatory, Safety, Market Access, Communications, and Leadership functions |
| **Human-in-the-loop calibration** | Uses structured stakeholder feedback to refine scoring and routing |
| **Decision governance** | Supports review, action, escalation, leadership resolution, and audit history |
| **Athena Copilot** | Provides evidence-grounded intelligence assistance with source provenance |

---

## The Decision Loop

```text
PUBLIC INFORMATION
        │
        ▼
8 SOURCE CONNECTORS
        │
        ▼
BRONZE INGESTION
        │
        ▼
PII/PHI SCRUBBING
        │
        ▼
EMBEDDING + NLP EXTRACTION
        │
        ▼
11-NODE INTELLIGENCE PIPELINE
        │
        ├── Confluence
        ├── Lifecycle
        ├── Red-Team Contradictions
        ├── Missing Signals
        └── Synthesis
        │
        ▼
EXPLAINABLE PRIORITY SCORE
        │
        ▼
FOUR-QUESTION DECISION BRIEF
        │
        ▼
ROLE-SCOPED REVIEW QUEUE
        │
        ▼
DECISION → ESCALATION → LEADERSHIP RESOLUTION
        │
        ▼
AUDIT TRAIL
```

---

## What Makes It Different

| Traditional approach | MetaRadar |
|---|---|
| Search individual sources | **Ingests multiple source classes into one intelligence layer** |
| Summarize documents | **Builds evidence stories around developments** |
| Alert on keywords | **Prioritizes signals using an explainable scoring model** |
| Report only what happened | **Tracks expected milestones and missing signals** |
| Accept claims at face value | **Surfaces contradictory or qualifying evidence** |
| Send information to everyone | **Routes intelligence by stakeholder function** |
| Human decisions outside the system | **Review, action, escalation, and audit are part of the workflow** |
| Cloud-only reasoning | **Local Gemma inference is available; hosted reasoning is privacy-gated** |

---

# Five Intelligence Mechanisms

### 1. Confluence Detection

Identifies when independent evidence streams point toward the same underlying development using semantic similarity, shared entities, source diversity, and temporal proximity.

### 2. Asset Lifecycle Tracking

Maps assets through a defined clinical-to-market lifecycle so an isolated event is interpreted in development context.

### 3. Red-Team Contradiction Analysis

Uses natural-language inference to identify evidence that challenges, contradicts, or qualifies an important claim.

### 4. Missing-Signal Detection

Turns silence into a structured signal by tracking expected milestones and identifying events that become overdue.

### 5. Stakeholder Calibration

Uses human feedback to improve the relationship between system scoring and stakeholder judgment.

---

# Four-Question Decision Framework

Every decision-oriented signal is organized around:

**Q1 — What changed?**  
A concise description of the observed event, grounded in source evidence.

**Q2 — Why does it matter?**  
Clinical, competitive, regulatory, or therapeutic context.

**Q3 — Who should review it?**  
Routing to the stakeholder function most relevant to the signal.

**Q4 — What action may be required?**  
A controlled, auditable next step rather than an unconstrained AI instruction.

---

# Explainable Priority Model

MetaRadar uses a deterministic four-factor score:

```text
Priority Score =
    Novelty              0–25
  + Clinical Significance 0–30
  + Regulatory Relevance  0–25
  + Recency               0–20

Total: 0–100
```

The model is deliberately inspectable. The system does not hide prioritization behind an opaque single model score.

Priority bands:

| Score | Priority | Intended handling |
|---:|---|---|
| ≥ 75 | Critical | Immediate cross-functional attention |
| ≥ 50 | High | Functional review |
| ≥ 25 | Medium | Routine surveillance |
| < 25 | Low | Background intelligence |

---

# Technical Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                     NEXT.JS + REACT                          │
│  Dashboard · Signals · Athena · Functions · Calibration      │
└─────────────────────────────┬────────────────────────────────┘
                              │ REST / SSE
┌─────────────────────────────▼────────────────────────────────┐
│                         FASTAPI                              │
│ Auth · Signals · Search · Intelligence · Ingestion · Audit  │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                    LANGGRAPH PIPELINE                        │
│ Ingest → Validate → Embed → NLP → Ontology → Confluence     │
│ → Lifecycle → Red-Team → Missing Signal → Synthesize        │
│ → Calibrate                                                  │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                       DATA LAYER                             │
│ PostgreSQL 16 · pgvector · Redis 7 · Alembic                │
│ Bronze → Silver → Gold signal architecture                  │
└──────────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          Local Gemma / Ollama        Optional xAI Grok
          privacy-preserving path     PUBLIC/SYNTHETIC only
```

### Data architecture

- **Bronze:** raw source payloads and connector metadata
- **Silver:** validated evidence and development relationships
- **Gold:** enriched signals, embeddings, scores, routing, review state, and provenance

The architecture is designed so that provenance survives the transformation from raw source material to decision-facing intelligence.

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript 5.7 |
| Styling | Tailwind CSS 4, custom design tokens |
| UI | Base UI / shadcn, Lucide React, Framer Motion |
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| Orchestration | LangGraph |
| Database | PostgreSQL 16 + pgvector |
| Cache / coordination | Redis 7 |
| Local AI | Gemma 3 4B GGUF via llama-cpp-python / Ollama |
| Hosted AI fallback | xAI Grok, privacy-gated |
| Embeddings | FastEmbed / all-MiniLM-L6-v2, 384 dimensions |
| Testing | pytest, pytest-asyncio, pytest-httpx |
| Infrastructure | Docker Compose |

The codebase follows a typed React/TypeScript frontend and async Python backend architecture. fileciteturn12file2L31-L51

---

# Data Sources

The current connector layer contains eight source adapters:

1. **NCBI PubMed**
2. **ClinicalTrials.gov**
3. **OpenFDA**
4. **EMA**
5. **NewsAPI**
6. **BioPharma Dive**
7. **FiercePharma**
8. **ET Pharma**

The connectors use asynchronous HTTP clients, source-specific parsing, freshness handling, retries, and quota controls where applicable. fileciteturn12file1L7-L34

---

# Responsible AI & Security

MetaRadar is designed around evidence provenance and controlled data boundaries.

### Evidence grounding

Decision-facing intelligence is tied back to source records and provenance rather than treating generated text as authoritative.

### Privacy boundary

The local Gemma path supports local inference. When hosted Grok reasoning is enabled, the privacy gate permits only `PUBLIC` or `SYNTHETIC` data to leave the environment. fileciteturn13file8L559-L569

### PII / PHI protection

The platform includes a dedicated scrubber for identifiers including emails, phone numbers, SSNs, MRNs, dates of birth, and national IDs. fileciteturn13file9L631-L635

### Authentication

Session-based authentication uses bcrypt password hashing, signed session tokens, HttpOnly cookies, SameSite protection, and session-bound CSRF tokens. fileciteturn12file1L78-L88

### Auditability

Decision workflows record audit events, and the project includes database-level controls intended to prevent unauthorized audit-log mutation. fileciteturn12file6L60-L75

> **Important:** This is a hackathon prototype and should not be represented as a validated GxP production system or as regulatory/compliance certification.

---

# Verification

The repository contains a broad automated test suite covering authentication, RBAC, connectors, intelligence nodes, privacy boundaries, provenance, red-team behavior, review-state transitions, retrieval, and end-to-end workflows.

The current project verification record reports **186 automated tests with 100% passing**. fileciteturn13file0L35-L47

Core verification commands include:

```bash
pytest
python scripts/export_openapi.py
cd frontend && npx tsc --noEmit
npm --prefix frontend run build
node scripts/check-banned-classes.mjs
```

The testing configuration uses pytest with async support and ASGI-based FastAPI endpoint testing. fileciteturn13file1L63-L81

---

# Quick Start

## Prerequisites

- Git
- Docker Desktop / Docker Engine
- Python 3.11+
- Node.js 20+
- npm or pnpm

The repository's stack specifies Python 3.11+, Node.js ≥20.9, Docker Compose, and pnpm 9.15.5 as the preferred frontend package manager. fileciteturn12file2L18-L26

## 1. Initialize the environment

```bash
python setup.py
```

The setup script initializes the environment and prepares the backing services and model configuration. fileciteturn13file4L276-L284

## 2. Start MetaRadar

```bash
python start.py
```

Then open:

```text
http://localhost:3000
```

API documentation:

```text
http://localhost:8000/docs
```

---

# Demo Flow

For an evaluation or live presentation, the strongest path is:

```text
Login
  ↓
Select stakeholder persona
  ↓
Open prioritized signal
  ↓
Inspect evidence + provenance
  ↓
Review decision brief
  ↓
Take authorized action
  ↓
Escalate when required
  ↓
Leadership resolves escalation
  ↓
Inspect audit trail
```

The productionization work explicitly defines this cross-functional vertical slice across Medical Affairs, Regulatory, Safety, Market Access, Communications, and Leadership. fileciteturn14file5L310-L335

---

# Repository Structure

```text
MetaRadar/
├── backend/
│   └── app/
│       ├── api/
│       ├── connectors/
│       ├── core/
│       ├── db/
│       ├── models/
│       ├── providers/
│       ├── schemas/
│       ├── services/
│       └── workflows/
├── frontend/
│   ├── app/
│   ├── components/
│   ├── context/
│   ├── lib/
│   └── types/
├── config/
├── models/
├── scripts/
├── tests/
├── pitch/
├── .planning/
├── docker-compose.yml
├── setup.py
└── start.py
```

The codebase map identifies the frontend, backend, connectors, intelligence workflows, services, tests, configuration, and planning layers shown above. fileciteturn12file3L8-L55

---

# Hackathon Deliverables

| Deliverable | Location |
|---|---|
| Presentation | `pitch/PITCH.md` |
| Architecture diagram | `pitch/architecture.svg` |
| Data-flow diagram | `pitch/dataflow.svg` |
| Governance flow | `pitch/responsibility_flow.svg` |
| Domain configuration | `config/haemophilia.yaml` |
| Engineering documentation | `docs/` |
| Automated tests | `tests/` |

---

# Business Impact

MetaRadar is designed to improve the decision layer between **information arrival and cross-functional action**.

Potential value areas:

- Reduce time spent manually monitoring fragmented sources
- Surface important developments earlier
- Make the evidence behind a signal inspectable
- Reduce unnecessary information distribution through role-based routing
- Create a common decision workflow across functions
- Preserve an auditable history of review and escalation
- Provide a path toward scalable rare-disease intelligence beyond haemophilia

These are **intended business outcomes**, not measured production results. Any quantitative business-impact claim should be supported by a pilot measurement rather than presented as an achieved KPI.

---

# Feasibility & Next Steps

The prototype is deliberately built around technologies that can run locally or in a conventional containerized environment:

- FastAPI + PostgreSQL + Redis
- Docker Compose
- Local Gemma inference
- Public biomedical APIs and RSS sources
- Typed REST contracts
- Automated testing
- Role-based authentication and authorization

A practical next stage would be a controlled pilot with:

1. A defined stakeholder group
2. A limited set of validated data sources
3. Human evaluation of signal precision and usefulness
4. Measurement of review latency and decision throughput
5. Model and scoring calibration against expert judgments
6. Formal security, privacy, validation, and governance review before any regulated deployment

---

# Team

**MS Ramaiah Institute of Technology (MSRIT), Bangalore, Karnataka, India**

**Novo Nordisk GBS Hackathon 2026 — Problem Statement #3**

- **Sanjana Rathore B.** — Team Lead, Medical Affairs Strategy & Clinical Endpoints
- **Ishaaq Ahmed Khan** — Haemophilia Treatment Map, Asset Lifecycles & Expected Events
- **Usha Rathore** — Evidence Quality, Red-Team Contradictions, Safety & Access Context
- **Omprakash Panda** — System Architecture, Data Ingestion, LangGraph & Full-Stack Engineering
- **Veerendra Desai** — Vector Search, Database, Telemetry, Performance & Deployment

---

# Project Status

**Hackathon-ready prototype — evaluation build**

The project has been hardened across authentication, privacy boundaries, connector reliability, pipeline concurrency, resource lifecycle, contract synchronization, and automated testing. fileciteturn13file4L270-L284

This repository is intended to demonstrate the **innovation, technical implementation, business value, and feasibility** of the MetaRadar approach. It is not a claim of production validation, regulatory approval, or clinical decision-making authority.

