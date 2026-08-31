<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="frontend/public/icon.svg">
    <source media="(prefers-color-scheme: light)" srcset="frontend/public/icon-light.svg">
    <img src="frontend/public/icon.svg" alt="MetaRadar Logo" width="120" height="120" />
  </picture>

  # MetaRadar

  ### From Inbox Noise to Strategic Signal

  **Evidence-Grounded Competitive Intelligence Radar for Rare Diseases (Haemophilia A & B)**

  [![Hackathon](https://img.shields.io/badge/Novo%20Nordisk%20GBS%20Hackathon-2026-blue)](#)
  [![Problem Statement](https://img.shields.io/badge/Problem%20Statement-%233%20Rare%20Disease%20Radar-purple)](#)
  [![Pilot](https://img.shields.io/badge/Pilot-Haemophilia%20A%20%26%20B-red)](#)
  [![Status](https://img.shields.io/badge/Status-Hackathon%20Evaluation%20Build-blue)](#)
  [![Tests](https://img.shields.io/badge/Pytest-186%20Passed%2C%201%20Skipped-brightgreen)](#)
  [![Contract](https://img.shields.io/badge/OpenAPI%203.1-Synchronized-blue)](#)
  [![Data](https://img.shields.io/badge/Data-8%20Monitored%20Sources-green)](#)
  [![Governance](https://img.shields.io/badge/Governance-Database--Enforced%20Audit-orange)](#)
</div>

> **"A conventional AI summarizes documents. MetaRadar builds an evidence story around a development."**

MetaRadar organizes fragmented public information across the haemophilia treatment landscape into **evidence-linked developments, multi-source confluence alerts, zero-shot contradiction flags, missing milestone alerts, and role-scoped intelligence briefs**.

The platform is purpose-built for the **Novo Nordisk GBS Hackathon 2026 — Problem Statement #3 (Rare Disease Competitive Intelligence Radar)**, with **Haemophilia A and Haemophilia B** as the initial clinical pilot.

---

## 🏆 Hackathon Final Submission Package

| Submission Deliverable | Location & Description |
|---|---|
| **1. Master Presentation Deck** | [`pitch/PITCH.md`](pitch/PITCH.md) — Master 7-Slide presentation deck and Q1–Q10 technical defense guide covering Project Overview, Problem & Innovation, Solution Summary, Technical Implementation, Verification Metrics, Roadmap, and Business Impact. |
| **2. Interactive Prototype / Demo** | Full-stack application running at `http://localhost:3000` with 13 specialized workspace views, 3D holographic persona switcher, live 8-source ingestion, Athena AI Copilot with streaming citations, and Executive Sign-Off Queue. |
| **3. Visual Architecture Diagrams** | Ultra-HD 2800px Vector SVGs & PNGs in [`pitch/`](pitch/): [System Architecture](pitch/architecture.svg), [Data Flow](pitch/dataflow.svg), and [Decision Governance Flow](pitch/responsibility_flow.svg). |
| **4. Domain Knowledge Layer** | Curated haemophilia ontology covering 12 modalities, canonical competitor assets, and 19 Red-Team evidence checks in [`config/haemophilia.yaml`](config/haemophilia.yaml). |
| **5. Deep Technical Documentation** | Comprehensive architecture specifications, design documents, and engineering standards in [`docs/`](docs/). |
| **6. 20-Session Engineering History** | Complete root-cause analysis and resolution history across all 20 debugging sessions documented in Section 8 of [`pitch/PITCH.md`](pitch/PITCH.md). |

---

## Current Status & Verification Record

- **Automated Test Suite:** `pytest tests/` → **186 automated tests — 186 passed, 1 skipped, 0 failures** across connectors, LangGraph nodes, privacy invariants, failure injection, provenance, and observability.
- **Frontend Build & Types:** `npm run build` → **Compiled cleanly with 0 errors** in Next.js 16 (Turbopack) with strict TypeScript checking (`tsc --noEmit`).
- **Contract Synchronization:** `python scripts/export_openapi.py` → **0 contract drift** (Pydantic v2 schemas synchronized with `frontend/types/api.ts`).
- **Database Migrations:** Alembic revisions applied across 22 PostgreSQL tables with zero schema drift.
- **Audit Immutability:** PostgreSQL trigger (`block_audit_log_mutation`) enforces append-only protection on `audit_logs` by disallowing `UPDATE` and `DELETE` operations.

---

## Table of Contents

- [Problem & Context](#problem--context)
- [Solution Overview](#solution-overview)
- [How MetaRadar Is Different](#how-metaradar-is-different)
- [Five Core Intelligence Mechanisms](#five-core-intelligence-mechanisms)
- [Four-Question Decision Framework](#four-question-decision-framework)
- [Deterministic Mathematical Priority Model](#deterministic-mathematical-priority-model)
- [Platform Architecture](#platform-architecture)
- [8 Monitored Intelligence Sources](#8-monitored-intelligence-sources)
- [Technology Stack](#technology-stack)
- [Haemophilia Knowledge Layer](#haemophilia-knowledge-layer)
- [Governance, Responsible AI & Security](#governance-responsible-ai--security)
- [Demo Flow & Role Personas](#demo-flow--role-personas)
- [Getting Started & Quickstart](#getting-started--quickstart)
- [Repository Structure](#repository-structure)
- [Deep Documentation](#deep-documentation)
- [Team](#team)

---

# Problem & Context

The haemophilia treatment landscape is rapidly transitioning across:
- **Recombinant & Plasma-Derived Factors** (Factor VIII & Factor IX)
- **Extended Half-Life (EHL) Factors** (Altuviiio, Esperoct, Idelvion)
- **Non-Factor Bispecific Antibodies** (emicizumab/Hemlibra, Mim8)
- **Anti-TFPI Rebalancing Agents** (concizumab/Alhemo, marstacimab/Hympavzi)
- **RNAi Therapeutics** (fitusiran)
- **AAV Gene Therapies** (etranacogene dezaparvovec/Hemgenix, valoctocogene roxaparvovec/Roctavian, fidanacogene elaparvovec/Beqvez)

Pharmaceutical cross-functional teams face three systemic challenges:

1. **Information Silos**: Trial readouts, FDA/EMA filings, safety signals, and market access shifts arrive through isolated channels.
2. **Ungrounded AI Summaries**: Generic LLMs can fabricate citations or blur clinical nuances, creating unacceptable risk for biopharma decisions.
3. **Decision Latency & Governance Gaps**: Critical signals often arrive without structured ownership routing, cross-functional review workflows, or auditable decision records.

---

# Solution Overview

MetaRadar treats external disclosures as **signals belonging to interconnected evidence stories**:

```text
                       8 MONITORED INTELLIGENCE SOURCES
       Primary: ClinicalTrials.gov · PubMed · FDA · EMA · DailyMed
       Secondary: BioPharma Dive · FiercePharma · Global Medical News
                                       │
                       AUTONOMOUS INGESTION / MANUAL SYNC
            (PostgreSQL Advisory Locks · Exponential Backoff · SHA-256 Deduplication)
                                       │
                         APPEND-ONLY RAW SIGNAL ARCHIVE
                               (raw_signals_bronze)
                                       │
                      PII/PHI SCRUBBER & EMBEDDING ENGINE
                         (pgvector 384-dim HNSW Index)
                                       │
                    11-NODE LANGGRAPH INTELLIGENCE PIPELINE
  Ingest → Validate → Embed → NLP Extract → Ontology → Confluence → Lifecycle
            → Red-Team → Missing Signal → Synthesize → Calibrate
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
    CONFLUENCE                     LIFECYCLES                    RED-TEAM
 (48h Multi-Source              (7-Stage Asset               (Zero-Shot NLI
 Evidence Linkage)             State Progression)            Contradictions)
         │                             │                             │
         └─────────────────────────────┼─────────────────────────────┘
                                       │
                          MISSING SIGNAL & WATCH FSM
                   (Expected Milestone Silence Lag Detection)
                                       │
                        DETERMINISTIC 4-FACTOR SCORING
                           (Score 0–100 · Math Model)
                                       │
                          FOUR-QUESTION DECISION BRIEF
                    ([FACT] · [INTERPRETATION] · [ACTION])
                                        │
                         ROLE-SCOPED DECISION WORKSPACES
   (Medical Affairs · Regulatory · Safety/PV · Market Access · Comms · Executive Queue)
                                       │
                        DATABASE-ENFORCED AUDIT TRAIL
```

---

# How MetaRadar Is Different

| Dimension | Generic LLM / ChatGPT | Commercial News Feed | **MetaRadar** |
|---|---|---|---|
| **Evidence Grounding** | High hallucination risk; fabricated trial citations. | Raw text snippets with no clinical synthesis. | **Source-linked evidence with provenance** linked directly to primary records (ClinicalTrials.gov, PubMed, FDA). |
| **Decision Framework** | Generic bulleted summaries. | Keyword alert emails. | **Four-Question Decision Brief** (`What Changed`, `Why It Matters`, `Who Should Act`, `Suggested Action`). |
| **Cross-Source Linkage** | Disconnected document queries. | Siloed feeds. | **Autonomous Confluence Detector** linking multi-source signals within a 48h rolling window. |
| **Contradiction Analysis** | Accepts user premise blindly. | No contradiction detection. | **Red-Team Contradiction Engine** using zero-shot NLI to surface conflicting clinical claims. |
| **Missing Milestones** | Only reports what happened. | Only reports what happened. | **Missing Signal FSM Tracker** flags expected trial readouts that fail to appear on time. |
| **Cross-Functional Steer**| No role scoping or workflow. | Static email distribution. | **Role-Scoped Routing + Executive Leadership Approval Workflow** with auditable history. |
| **Deployment Privacy** | Cloud API lock-in. Data sent externally. | Cloud vendor lock-in. | **Local LLM execution with optional hosted reasoning** protected by a pre-transmission privacy gate. |

---

# Five Core Intelligence Mechanisms

### 1. Confluence Detection
- **Core Question**: *Are multiple independent evidence streams pointing to the same underlying development?*
- **Mechanism**: Evaluates signals across distinct source types within a 48h rolling window using cosine embedding similarity and shared entity identifiers. Scores confluence based on source diversity, velocity, and semantic coherence.

### 2. Signal Lifecycle Tracking
- **Core Question**: *Where is this asset in its overall clinical-to-market journey?*
- **Mechanism**: Tracks candidate molecules across a 7-stage finite state progression: `PRECLINICAL` → `PHASE_1` → `PHASE_2` → `PHASE_3` → `REGULATORY_REVIEW` → `APPROVED` → `POST_MARKET`.

### 3. Red-Team Contradiction Analysis
- **Core Question**: *What evidence challenges or qualifies the competitor's claim?*
- **Mechanism**: Uses zero-shot NLI (BART-Large-MNLI) to evaluate pairs of claims against baseline clinical endpoints (e.g., highlighting differences between clinical trial ABR claims and published real-world cohort data), surfacing potential contradictions for human expert review.

### 4. Missing-Signal Detection & Silence Tracker
- **Core Question**: *What should have happened next, and has it failed to occur?*
- **Mechanism**: 6-state FSM (`WITHIN_WINDOW`, `DUE`, `OVERDUE`, `SATISFIED`, `SUPPRESSED`, `INSUFFICIENT_DATA`) tracking milestone deadlines. If an expected trial readout does not appear within the expected window, the absence of data becomes an active intelligence signal.

### 5. Stakeholder Calibration (Human-in-the-Loop)
- **Core Question**: *Does the system's scoring match expert stakeholder judgment?*
- **Mechanism**: Stakeholders rate relevance (1–5 stars) and submit structured feedback. The HITL Calibration Engine dynamically adjusts 4-factor scoring weights and persona routing matrices without code redeployment.

---

# Four-Question Decision Framework

Every ingested signal synthesizes into an epistemically tagged Four-Question Decision Brief:

- **Q1 — What changed?** Concise description of the event grounded in source evidence and tagged with strict epistemic classification (`[FACT]`).
- **Q2 — Why does it matter?** Clinical, competitive, and therapeutic context supported by primary citations (`[INTERPRETATION]`).
- **Q3 — Which function should review it?** Relevance-based routing to the appropriate enterprise stakeholder (Medical Affairs, Regulatory, Safety, Market Access, Comms, Leadership).
- **Q4 — What internal action may be required?** Controlled, auditable next step chosen from an action vocabulary rather than an unconstrained AI instruction (`[ACTION]`).

---

# Deterministic Mathematical Priority Model

Every signal is scored on a **transparent 4-factor mathematical formula** ($0\text{--}100$):

$$\text{Priority Score} = \text{Novelty } [0\text{–}25] + \text{Clinical Significance } [0\text{–}30] + \text{Regulatory Relevance } [0\text{–}25] + \text{Recency } [0\text{–}20]$$

| Factor | Max Points | Calculation Method |
|---|:---:|---|
| **Novelty** | 25 | Cosine distance from signal embedding to nearest existing signal embedding in pgvector. |
| **Clinical Significance** | 30 | Regex matching against 12 clinical keyword patterns (ABR, prophylaxis, inhibitors, Factor VIII/IX). 3 pts per match (max 30). |
| **Regulatory Relevance** | 25 | Regex matching against 14 regulatory keyword patterns (FDA, EMA, CHMP, PDUFA, BLA, NDA). 5 pts per match (max 25). |
| **Recency** | 20 | Exponential decay with a 72-hour half-life: $20 \times e^{-0.693 \times \frac{\text{hours}}{72}}$. |

| Score Range | Priority Level | Badge Color | Expected Action |
|---|---|---|---|
| ≥ 75 | **CRITICAL** | Red | Immediate cross-functional alert; executive review required |
| ≥ 50 | **HIGH** | Orange | Functional queue review required within 24–48 hours |
| ≥ 25 | **MEDIUM** | Blue | Standard surveillance feed; weekly review |
| < 25 | **LOW** | Slate | Background archive; historical trend correlation |

---

# Platform Architecture

```text
                                   METARADAR
                                       │
 ┌─────────────────────────────────────┴─────────────────────────────────────┐
 │                                                                           │
 ▼                                                                           ▼
Frontend (Next.js 16 / React 19)                            Backend (FastAPI 0.115 / Python 3.11+)
• Turbopack SSR & 13 Specialized Workspace Views            • 11-Node LangGraph Intelligence Pipeline
• 3D Holographic Persona Switcher                           • Autonomous Async SourceScheduler
• Athena Copilot (Live SSE Streaming + Citations)           • 8 Monitored Connector Adapters
• Evidence Drawer & Provenance Badges                       • Truthful Source Health Telemetry
• Global 'Ingest Data' & Semantic Search (⌘K)               • PII/PHI De-identification Layer
                                                            • REST API (OpenAPI 3.1 Synchronized)
                                                                           │
                                                                           ▼
                                                            Persistence (PostgreSQL 16 + Redis 7)
                                                            • 22 Relational Tables (Alembic Managed)
                                                            • pgvector (384-dim HNSW Vector Index)
                                                            • Append-Only Raw Ingestion Archive
                                                            • Database-Enforced Audit Log Trigger
```

---

# 8 Monitored Intelligence Sources

The platform monitors eight biomedical and industry intelligence sources:

### Primary / Regulatory & Literature Sources
| Source | Connector Type | Polling Interval | Data Retrieved |
|---|---|---|---|
| **ClinicalTrials.gov** | REST API v2 | 60 min | Trial protocols, status transitions, milestone completion dates |
| **NCBI PubMed** | E-utilities REST (Medline XML) | 60 min | Peer-reviewed biomedical research, clinical abstracts, PMIDs |
| **OpenFDA** | Drugs@FDA + FAERS REST | 30 min | Drug approvals, safety communications, MedWatch adverse events |
| **EMA EPAR** | RSS & Document Portal | 30 min | CHMP opinions, marketing authorizations, European safety dossiers |
| **DailyMed** | Drug Labeling REST | 30 min | Structured U.S. drug labeling, prescribing information, and label updates |

### Secondary / Industry Intelligence Sources
| Source | Connector Type | Polling Interval | Data Retrieved |
|---|---|---|---|
| **BioPharma Dive** | Industry RSS | 15 min | Clinical trial readouts, biopharma strategy, pipeline updates |
| **Fierce Pharma / Biotech** | Industry RSS | 15 min | Commercial announcements, licensing deals, corporate M&A |
| **Global Medical News (NewsAPI)** | REST API | 15 min | International healthcare headlines (quota-governed with backoff) |

---

# Technology Stack

| Layer | Technology | Key Details |
|---|---|---|
| **Frontend** | Next.js 16.3.0 / React 19 | TypeScript 5.7, Turbopack, Vanilla CSS Design Tokens, 3D Tilt ProfileCard |
| **Backend** | FastAPI 0.115.8 | Python 3.11/3.12/3.13, Pydantic v2, Structlog JSON logging |
| **AI Orchestration** | LangGraph | 11-node stateful workflow execution DAG (`PipelineRunner`) |
| **Database** | PostgreSQL 16 + pgvector | 22 tables, 384-dim HNSW cosine vector index, mutation-protected audit log |
| **Local LLM** | Gemma-3 4B GGUF | `google/gemma-3-4b-it` (llama-cpp-python / CUDA offload / CPU thread-safe executor) |
| **Hosted LLM Fallback** | xAI Grok API | Opt-in reasoning fallback protected by pre-transmission privacy gate |
| **NLI Contradiction Engine** | BART-Large-MNLI | Zero-shot natural language inference for claim pair testing |
| **Embeddings** | sentence-transformers | `all-MiniLM-L6-v2` (384-dimensional dense vectors) |
| **Cache & Locking** | Redis 7 | Distributed advisory locking and rate limiting |
| **Migrations** | Alembic | 14 applied schema migrations (`001_initial` → `014_governance_hardening`) |
| **Testing** | pytest | 186 automated tests — 186 passed, 1 skipped |

---

# Haemophilia Knowledge Layer

Curated by the domain team covering:
- **Diseases**: Haemophilia A (Factor VIII deficiency) and Haemophilia B (Factor IX deficiency).
- **Inhibitor Cohorts**: With inhibitors (high/low titer), without inhibitors, previously untreated patients (PUPs).
- **Therapeutic Modalities**: Recombinant Factor, Extended Half-Life (EHL) Factors, Non-Factor Bispecifics, Anti-TFPI, RNAi, AAV Gene Therapies.
- **Canonical Competitor Assets**: `concizumab` (Alhemo), `mim8`, `emicizumab` (Hemlibra), `etranacogene dezaparvovec` (Hemgenix), `valoctocogene roxaparvovec` (Roctavian), `fidanacogene elaparvovec` (Beqvez), `fitusiran`, `marstacimab` (Hympavzi), `efanesoctocog alfa` (Altuviiio).

---

# Governance, Responsible AI & Security

- **Evidence-Grounded Generation**: Decision brief claims and Athena Copilot answers carry inline provenance badges linking back to primary source records (PMIDs, NCT IDs, FDA URLs).
- **Database-Enforced Immutability**: PostgreSQL trigger (`block_audit_log_mutation`) strictly forbids `UPDATE` or `DELETE` operations on the `audit_logs` table.
- **PII/PHI Scrubbing**: Pre-persistence regex scrubber sanitizes personal identifiers, MRNs, phone numbers, email addresses, and dates of birth.
- **Privacy-Gated Reasoning**: Local Gemma-3 4B execution keeps inference local; when hosted reasoning is enabled, the privacy gate ensures only `PUBLIC` or `SYNTHETIC` data leaves the environment.
- **Session Security**: Session tokens use bcrypt password hashing, signed cookies with HttpOnly and SameSite protection, and session-bound CSRF tokens.

> **Note:** This software is a hackathon prototype designed for technology evaluation. It does not constitute a validated GxP production deployment or regulatory compliance certification.

---

# Demo Flow & Role Personas

### Evaluation Demo Flow

```text
Login → Select Persona → Inspect Scoped Signal Feed → View 4-Question Decision Brief
  → Review Evidence & Contradiction Flags → Take Action / Escalate → Executive Review → Audit Trail
```

### Role Personas

MetaRadar provides 7 stakeholder personas with scoped RBAC permissions and cross-functional governance workflows:

| Role Persona | Stakeholder Domain | Primary Responsibilities |
|---|---|---|
| **Dr. Elena Vance** | **Medical Affairs** | Clinical trial readouts, ABR efficacy benchmarks, publication surveillance, and leadership approval escalation. |
| **Marcus Vance** | **Regulatory Affairs** | FDA/EMA dossier filings, label changes, CHMP opinions, breakthrough designations, and milestone tracking. |
| **Dr. Sarah Chen** | **Safety & Pharmacovigilance** | Adverse events (thrombosis, microangiopathy), black box warnings, DSMB reviews, and risk minimization. |
| **David Ross** | **Market Access & Pricing** | ICER/NICE value assessments, formulary placement, reimbursement barriers, and competitor price tracking. |
| **Rachel Green** | **Communications & IR** | Press releases, congress abstracts (ASH, EHA, WFH), media coverage, and competitive positioning. |
| **Alex Mercer** | **Executive Leadership** | Portfolio steer, cross-functional approval queue sign-offs (`/functions`), high-impact escalations, and executive briefing. |
| **System Administrator** | **Platform Admin** | Ingestion health, source connector telemetry, model parameters, cache eviction, and audit log inspection. |

> **Persona Selection**: Navigate to `http://localhost:3000/login` to use the interactive 3D-tilt **ProfileCard** interface and one-click quick-fill demo persona buttons. Demo credentials are provided separately in the hackathon submission package.

---

# Getting Started & Quickstart

### Prerequisites
- **Git**
- **Docker Desktop / Docker Engine** (for PostgreSQL 16 + Redis 7)
- **Python 3.11+**
- **Node.js 20+** & **npm** or **pnpm**

### 1. Environment Initialization
Run the automated environment setup wizard:

```bash
python setup.py
```

Optional flags:
```bash
python setup.py --download-model    # Download local Gemma 3 4B GGUF model (~2.48 GB)
python setup.py --api-key <KEY>     # Optional: configure xAI Grok API key for hosted reasoning
```

### 2. Start All Services
Launch Docker backing services, apply database migrations, and start both backend (port 8000) and frontend (port 3000) with a single command:

```bash
python start.py
```

- Web Application: **`http://localhost:3000`**
- Interactive API Documentation: **`http://localhost:8000/docs`**

---

# Repository Structure

```text
MetaRadar/
├── backend/
│   └── app/
│       ├── api/          # FastAPI REST endpoints & SSE streaming routes
│       ├── connectors/   # 8 Monitored source adapters (PubMed, CT.gov, FDA, EMA, etc.)
│       ├── core/        # Security, config, PII scrubbing, privacy gate
│       ├── db/          # PostgreSQL session management & base models
│       ├── models/      # SQLAlchemy ORM schemas
│       ├── providers/   # Local Gemma & hosted Grok LLM providers
│       ├── schemas/     # Pydantic v2 data contracts
│       ├── services/    # Scoring math, NLI Red-Team, Confluence, Lifecycle FSM
│       └── workflows/   # 11-Node LangGraph intelligence pipeline (PipelineRunner)
├── frontend/
│   ├── app/             # Next.js 16 App Router (13 workspace views)
│   ├── components/      # Shared UI tokens, 3D ProfileCard, Evidence Drawer
│   ├── context/         # Auth & persona state providers
│   ├── lib/             # API client, SSE streaming reader, utilities
│   └── types/           # Synchronized TypeScript data contracts
├── config/              # Haemophilia domain ontology (haemophilia.yaml)
├── docs/                # Architecture, design, governance, and engineering standards
├── pitch/               # Master pitch deck (PITCH.md) & Ultra-HD diagrams
├── scripts/             # Setup, startup, OpenAPI export, and PNG conversion
└── tests/               # 186 automated test cases (pytest)
```

---

# Deep Documentation

Detailed technical documentation is organized in [`docs/`](docs/):

- **Master Plan & Architecture**: [`docs/METARADAR_MASTER_PLAN_v5.0.md`](docs/METARADAR_MASTER_PLAN_v5.0.md) & [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md)
- **Software Design Document**: [`docs/3_SOFTWARE_DESIGN_DOCUMENT.md`](docs/3_SOFTWARE_DESIGN_DOCUMENT.md)
- **Requirements Specification**: [`docs/2_SRS_Software_Requirements_Specification.md`](docs/2_SRS_Software_Requirements_Specification.md)
- **Risk, Guardrails & Governance**: [`docs/9_RISK_AND_GUARDRAILS.md`](docs/9_RISK_AND_GUARDRAILS.md)
- **Step-by-Step Demo Script**: [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md)
- **Engineering Standards & DoD**: [`docs/rules/ENGINEERING_STANDARDS.md`](docs/rules/ENGINEERING_STANDARDS.md) & [`docs/rules/DEFINITION_OF_DONE.md`](docs/rules/DEFINITION_OF_DONE.md)
- **Codebase Mapping Reports**: [`.planning/codebase/`](.planning/codebase/)

---

# Team

**MS Ramaiah Institute of Technology (MSRIT), Bangalore, Karnataka, India**  
*Novo Nordisk GBS Hackathon 2026 — Problem Statement #3: Rare Disease Competitive Intelligence Radar*

- **Sanjana Rathore B.** (Team Lead) — B.Pharm (Domain Owner, Medical Affairs Strategy, Clinical Endpoints)
- **Ishaaq Ahmed Khan** — B.Pharm (Haemophilia Treatment Map, Asset Lifecycles, Expected Events FSM)
- **Usha Rathore** — B.Pharm (Evidence Quality, Red-Team Contradictions, Safety & Access Context)
- **Omprakash Panda** — ISE/CSE (System Architecture, Data Ingestion, LangGraph Orchestration, Full-Stack Engine)
- **Veerendra Desai** — ISE/CSE (Vector Search, Database, Telemetry, Performance & Deployment)

*Faculty Sponsor: Faculty Advisory Board, Dept. of Pharmacy Practice & Dept. of Computer Science and Engineering, MSRIT*