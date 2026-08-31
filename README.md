<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="frontend/public/icon.svg">
    <source media="(prefers-color-scheme: light)" srcset="frontend/public/icon-light.svg">
    <img src="frontend/public/icon.svg" alt="MetaRadar Logo" width="120" height="120" />
  </picture>

  # MetaRadar

  ### From Inbox Noise to Strategic Signal

  **Autonomous, Evidence-Grounded Competitive Intelligence Radar for Rare Diseases (Haemophilia A & B)**

  [![Hackathon](https://img.shields.io/badge/Novo%20Nordisk%20GBS%20Hackathon-2026-blue)](#)
  [![Problem Statement](https://img.shields.io/badge/Problem%20Statement-%233%20Rare%20Disease%20Radar-purple)](#)
  [![Pilot](https://img.shields.io/badge/Pilot-Haemophilia%20A%20%26%20B-red)](#)
  [![Status](https://img.shields.io/badge/Status-Production%20Ready%20(100%25)-success)](#)
  [![Tests](https://img.shields.io/badge/Pytest-186%2F186%20Passing-brightgreen)](#)
  [![Contract](https://img.shields.io/badge/OpenAPI%203.1-Synchronized-blue)](#)
  [![Data](https://img.shields.io/badge/Data-8%20Autonomous%20Connectors-green)](#)
  [![Audit](https://img.shields.io/badge/Governance-WORM%20Immutable-orange)](#)
</div>

> **"A conventional AI summarizes documents. MetaRadar builds an evidence story around a development."**

MetaRadar converts fragmented public information about the haemophilia treatment landscape into **evidence-backed developments, real-time confluence alerts, zero-shot contradiction warnings, missing milestone alerts, and role-scoped intelligence briefs**.

The platform is purpose-built for the **Novo Nordisk GBS Hackathon 2026 — Problem Statement #3 (Rare Disease Competitive Intelligence Radar)**, with **Haemophilia A and Haemophilia B** as the initial clinical pilot.

---

## 🏆 Hackathon Final Submission Package

This repository contains the complete final project readout package for the **Novo Nordisk GBS Hackathon 2026**:

| Submission Deliverable | Location & Description |
|---|---|
| **1. Final Presentation Deck** | [`pitch/PITCH.md`](pitch/PITCH.md) — Master 7-Slide presentation deck structured according to the organizing committee's requested flow, covering Project Overview, Problem & Innovation, Solution Summary, Technical Implementation, Results/Metrics, Roadmap, and Business Impact. |
| **2. Interactive Prototype / Demo** | Full-stack application running at `http://localhost:3000` with 13 specialized workspaces, 3D holographic persona switcher, live 8-source ingestion, Athena AI Copilot with streaming citations, and Executive Sign-Off Queue. |
| **3. Supporting Documentation** | Comprehensive architecture specifications, domain ontology YAMLs, and engineering standards in [`docs/`](docs/) and [`config/haemophilia.yaml`](config/haemophilia.yaml). |
| **4. Visual Materials & Diagrams** | Ultra-HD 2800px Vector & PNG diagrams in [`pitch/`](pitch/): [System Architecture](pitch/architecture.svg), [Data Flow](pitch/dataflow.svg), and [Decision Governance Flow](pitch/responsibility_flow.svg). |
| **5. 20-Session Engineering Odyssey** | Complete history of all 20 debugging and hardening sessions documented in Section 8 of [`pitch/PITCH.md`](pitch/PITCH.md). |

---

## Current Status & Verification Matrix

> **All development milestones through Phase 12 (Autonomous Ingestion, Source Health Telemetry, Provenance Traceability, NLI Contradictions, and Security Hardening) are fully active and verified.**

- **Executable Verification Matrix:**
  - `pytest tests/` → **186/186 Passed (100%)** clean suite across connectors, LangGraph nodes, truthfulness invariants, failure injection, provenance, and observability.
  - `npm run build` → **Compiled Cleanly (0 Errors)** in Next.js 16 (Turbopack) with strict TypeScript checking.
  - `python scripts/export_openapi.py` → **0 Contract Drift** (Synchronized at `frontend/types/api.ts`).
  - `Alembic Migrations` → **11/11 Applied (`001_initial` through `011_widen_fingerprint`)** across 22 PostgreSQL tables with zero schema drift.
  - `Security & Governance` → **PostgreSQL WORM physical trigger** prevents unauthorized mutation of audit logs; session cookies auto-secured in production.

---

## Table of Contents

- [Problem & Context](#problem--context)
- [Solution Overview](#solution-overview)
- [How MetaRadar Is Different](#how-metaradar-is-different)
- [Five Core Intelligence Mechanisms](#five-core-intelligence-mechanisms)
- [Four-Question Decision Framework](#four-question-decision-framework)
- [Deterministic Mathematical Priority Model](#deterministic-mathematical-priority-model)
- [Platform Architecture](#platform-architecture)
- [Technology Stack](#technology-stack)
- [8 Authoritative Data Sources](#8-authoritative-data-sources)
- [Haemophilia Knowledge Layer](#haemophilia-knowledge-layer)
- [Safety, Responsible AI & GxP Compliance](#safety-responsible-ai--gxp-compliance)
- [Project Structure](#project-structure)
- [Getting Started & Quickstart](#getting-started--quickstart)
- [Role Personas & Demo Credentials](#role-personas--demo-credentials)
- [Running the Platform](#running-the-platform)
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
1. **Information Silos**: Trial readouts, FDA/EMA filings, safety signals, and market access shifts live in separate repositories.
2. **AI Hallucination Risk**: Generic LLMs invent trial identifiers and PMIDs, creating unacceptable risk for biopharma decisions.
3. **No Cross-Functional Governance**: Critical signals arrive without structured accountability, ownership routing, or auditable sign-off records.

---

# Solution Overview

MetaRadar treats external disclosures as **signals belonging to interconnected evidence stories**:

```text
                      8 AUTHORITATIVE BIOMEDICAL SOURCES
     ClinicalTrials.gov · NCBI PubMed · FDA · EMA · BioPharma Dive · FiercePharma · DailyMed · NewsAPI
                                       │
                      AUTONOMOUS INGESTION / MANUAL SYNC
           (PostgreSQL Advisory Locks · Exponential Backoff · SHA-256 Deduplication)
                                       │
                         BRONZE WORM IMMUTABLE STORE
                                       │
                      PII/PHI SCRUBBER & EMBEDDING ENGINE
                         (pgvector 384-dim HNSW Index)
                                       │
                          10-NODE LANGGRAPH DAG
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
                   ([FACT] · [INTERPRETATION] · [SPECULATION])
                                       │
                         ROLE-SCOPED DECISION WORKSPACES
   (Medical Affairs · Regulatory · Safety/PV · Market Access · Comms · Executive Queue)
```

---

# How MetaRadar Is Different

| Dimension | Generic LLM / ChatGPT | Commercial News Feed | **MetaRadar** |
|---|---|---|---|
| **Evidence Grounding** | High hallucination risk; fabricated citations. | Raw text snippets with no clinical synthesis. | **100% Verifiable Citations** linked directly to ClinicalTrials.gov, PubMed, and FDA dossiers. |
| **Decision Framework** | Generic bulleted summaries. | Keyword alert emails. | **Four-Question Brief** (`What Changed`, `Why It Matters`, `Who Should Act`, `Suggested Action`). |
| **Cross-Source Linkage** | Disconnected document queries. | Siloed feeds. | **Autonomous Confluence Detector** linking multi-source signals within 48h. |
| **Scientific Validation** | Accepts premise blindly. | No contradiction detection. | **Red-Team Contradiction Engine** with BART-Large-MNLI zero-shot NLI. |
| **Missing Milestones** | Only reports what happened. | Only reports what happened. | **Missing Signal FSM Tracker** flags absent trial readouts (silence becomes alert). |
| **Cross-Functional Steer**| No role scoping. | Static distribution list. | **7-Persona Scoped RBAC + Executive Leadership Approval Workflow**. |
| **Deployment Privacy** | Cloud API lock-in. | Cloud vendor lock-in. | **100% Air-Gapped Local Gemma-3 4B GGUF** (CUDA/CPU) or Hybrid Grok API. |

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
- **Mechanism**: Uses BART-Large-MNLI zero-shot NLI to evaluate pairs of claims against baseline clinical endpoints (e.g., comparing clinical trial ABR 0.0 against real-world Phase 4 ABR 0.8).

### 4. Missing-Signal Detection & Silence Tracker
- **Core Question**: *What should have happened next, and has it failed to occur?*
- **Mechanism**: 6-state FSM (`WITHIN_WINDOW`, `DUE`, `OVERDUE`, `SATISFIED`, `SUPPRESSED`) tracking milestone deadlines. If a promised trial readout does not appear within the expected window, the absence of data becomes an active intelligence signal.

### 5. Stakeholder Calibration (Human-in-the-Loop)
- **Core Question**: *Does the system's scoring match expert stakeholder judgement?*
- **Mechanism**: Stakeholders rate relevance (1–5 stars) and submit structured feedback. The HITL Calibration Engine dynamically adjusts 4-factor scoring weights and persona routing matrices without code redeployment.

---

# Four-Question Decision Framework

Every ingested signal synthesizes into an epistemically tagged Four-Question Decision Brief:

- **Q1 — What changed?** Concise description of the event tagged with strict epistemic classification (`[FACT]`).
- **Q2 — Why does it matter?** Clinical, competitive, and therapeutic context supported by citations (`[INTERPRETATION]`).
- **Q3 — Which Novo Nordisk function should review it?** Relevance-based routing to 6 core functions (Medical Affairs, Regulatory, Safety, Market Access, Comms, Leadership).
- **Q4 — What internal action may be required?** Concrete next step chosen from a controlled action vocabulary (`[ACTION]`).

---

# Deterministic Mathematical Priority Model

Every signal is scored on a **transparent 4-factor mathematical formula** ($0\text{--}100$):

$$\text{Priority Score} = \text{Novelty } [0\text{–}25] + \text{Clinical Significance } [0\text{–}30] + \text{Regulatory Relevance } [0\text{–}25] + \text{Recency } [0\text{–}20]$$

| Factor | Max Points | Calculation Method |
|---|:---:|---|
| **Novelty** | 25 | Cosine distance from signal embedding to nearest existing signal in pgvector. |
| **Clinical Significance** | 30 | Regex matching against 12 clinical patterns (ABR, prophylaxis, inhibitors, Factor VIII/IX). 3 pts per match (max 30). |
| **Regulatory Relevance** | 25 | Regex matching against 14 regulatory patterns (FDA, EMA, CHMP, PDUFA, BLA, NDA). 5 pts per match (max 25). |
| **Recency** | 20 | Exponential decay with 72-hour half-life: $20 \times e^{-0.693 \times \frac{\text{hours}}{72}}$. |

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
 ┌────────────────────────────────────┴────────────────────────────────────┐
 │                                                                         │
 ▼                                                                         ▼
Frontend (Next.js 16 / React 19)                           Backend (FastAPI 0.115 / Python 3.11+)
• Turbopack SSR & 13 Workspaces                            • 10-Node LangGraph Execution Graph
• 3D Holographic Persona Switcher                          • Autonomous Async SourceScheduler
• Athena Copilot (Live SSE Stream)                         • 8 Public Connector Adapters
• Evidence Drawer & Provenance Badges                      • Truthful Source Health Telemetry
• Global 'Ingest Data' & Search (⌘K)                       • PII/PHI De-identification Layer
                                                           • REST API (OpenAPI 3.1 Synchronized)
                                                                         │
                                                                         ▼
                                                           Persistence (PostgreSQL 16 + Redis 7)
                                                           • 22 Relational Tables (Alembic Managed)
                                                           • pgvector (384-dim HNSW Vector Index)
                                                           • Immutable Bronze Ingestion Layer (WORM)
                                                           • Physical PostgreSQL Audit Trigger
```

---

# Technology Stack

| Layer | Technology | Key Details |
|---|---|---|
| **Frontend** | Next.js 16.3.0 / React 19 | TypeScript, Turbopack, Vanilla CSS Design Tokens, 3D Tilt ProfileCard |
| **Backend** | FastAPI 0.115.8 | Python 3.11/3.12/3.13, Pydantic v2, Structlog JSON logging |
| **AI Orchestration** | LangGraph | 10-node stateful workflow execution DAG (`PipelineRunner`) |
| **Database** | PostgreSQL 16 + pgvector | 22 tables, 384-dim HNSW cosine vector index, WORM audit triggers |
| **Local LLM** | Gemma-3 4B GGUF | `google/gemma-3-4b-it` (llama-cpp-python / CUDA RTX offload / CPU) |
| **NLI Red-Team** | BART-Large-MNLI | Facebook MNLI zero-shot natural language inference |
| **Embeddings** | sentence-transformers | `all-MiniLM-L6-v2` (384-dimensional dense vectors) |
| **Cache & Locking** | Redis 7 | Distributed advisory locking and rate limiting |
| **Migrations** | Alembic | 11 applied migrations (`001_initial` → `011_widen_fingerprint`) |
| **Testing** | pytest | 186 automated test cases (100% passing) |

---

# 8 Authoritative Data Sources

| Source | Connector Type | Cadence | Data Retrieved |
|---|---|---|---|
| **NCBI PubMed** | E-utilities REST (Medline XML) | 60 min | Peer-reviewed biomedical research, abstracts, PMIDs |
| **ClinicalTrials.gov** | REST API v2 | 60 min | Trial protocols, status transitions, milestone completion dates |
| **OpenFDA** | Drugs@FDA + FAERS REST | 30 min | Drug approvals, safety communications, MedWatch adverse events |
| **EMA EPAR** | RSS & Document Portal | 30 min | CHMP opinions, marketing authorizations, European safety dossiers |
| **BioPharma Dive** | Industry RSS | 15 min | Clinical trial readouts, biopharma strategy, pipeline updates |
| **Fierce Pharma / Biotech** | Industry RSS | 15 min | Commercial announcements, licensing deals, regulatory updates |
| **DailyMed / Regional** | Drug Labeling REST | 30 min | Label updates, regional market access, packaging changes |
| **Global Medical News (NewsAPI)** | REST API | 15 min | International healthcare headlines (quota-governed with backoff) |

---

# Haemophilia Knowledge Layer

Curated by the pharmacy domain team at MSRIT covering:
- **Diseases**: Haemophilia A (Factor VIII deficiency) and Haemophilia B (Factor IX deficiency).
- **Inhibitor Cohorts**: With inhibitors (high/low titer), without inhibitors, previously untreated patients (PUPs).
- **Therapeutic Modalities**: Recombinant Factor, Extended Half-Life (EHL) Factors, Non-Factor Bispecifics, Anti-TFPI, RNAi, AAV Gene Therapies.
- **Canonical Assets**: `concizumab` (Alhemo), `mim8`, `emicizumab` (Hemlibra), `etranacogene dezaparvovec` (Hemgenix), `valoctocogene roxaparvovec` (Roctavian), `fidanacogene elaparvovec` (Beqvez), `fitusiran`, `marstacimab` (Hympavzi), `efanesoctocog alfa` (Altuviiio).

---

# Safety, Responsible AI & GxP Compliance

- **Zero Hallucinated Citations**: Every claim in Athena Copilot and Decision Briefs links directly to primary records (PMID, NCT ID, FDA URL).
- **WORM Immutability**: PostgreSQL physical trigger (`block_audit_log_mutation`) strictly forbids `UPDATE` or `DELETE` on the `audit_logs` table.
- **PII/PHI De-identification**: Pre-persistence regex scrubber sanitizing patient identifiers, MRNs, phone numbers, and dates of birth.
- **Air-Gapped Private Execution**: Local Gemma-3 4B GGUF ensures zero patient or proprietary data leaves the local machine.

---

# Role Personas & Demo Credentials

MetaRadar provides 7 purpose-built stakeholder personas with scoped RBAC permissions and cross-functional governance workflows:

| Role Persona | Stakeholder Domain | Demo Email | Fixed Password | Primary Responsibilities |
|---|---|---|---|---|
| **Dr. Elena Vance** | **Medical Affairs** | `medical.affairs@metaradar.internal` | `MedAffairs2026!` | Clinical trial readouts, ABR efficacy benchmarks, publication surveillance, and leadership approval escalation. |
| **Marcus Vance** | **Regulatory Affairs** | `regulatory@metaradar.internal` | `Regulatory2026!` | FDA/EMA dossier filings, label changes, CHMP opinions, breakthrough designations, and milestone tracking. |
| **Dr. Sarah Chen** | **Safety & Pharmacovigilance** | `safety@metaradar.internal` | `Safety2026!` | Adverse events (thrombosis, microangiopathy), black box warnings, DSMB reviews, and risk minimization. |
| **David Ross** | **Market Access & Pricing** | `market.access@metaradar.internal` | `Access2026!` | ICER/NICE value assessments, formulary placement, reimbursement barriers, and competitor price tracking. |
| **Rachel Green** | **Communications & IR** | `comms@metaradar.internal` | `Comms2026!` | Press releases, congress abstracts (ASH, EHA, WFH), media coverage, and competitive positioning. |
| **Alex Mercer** | **Executive Leadership** | `leadership@metaradar.internal` | `Leader2026!` | Portfolio steer, cross-functional approval queue sign-offs (`/functions`), high-impact escalations, and executive briefing. |
| **System Administrator** | **Platform Admin** | `admin@metaradar.internal` | `Admin2026!` | Ingestion health, source connector telemetry, model parameters, cache eviction, and audit log inspection. |

> **Login Page**: Navigate to `http://localhost:3000/login` to interact with the 3D-tilt **ProfileCard** interface and one-click quick-fill persona buttons.

---

# Getting Started & Quickstart

### Prerequisites
- **Git**
- **Docker Desktop** (for PostgreSQL + Redis)
- **Python 3.11+**
- **Node.js 20+** & **npm** or **pnpm**

### 1. Zero-Config Environment & Model Setup
Run the automated environment setup wizard:

```bash
python setup.py
```

Options:
```bash
python setup.py --download-model    # Automatically download local Gemma 3 4B GGUF model (~2.48 GB)
python setup.py --api-key <KEY>     # Configure xAI Grok API key for hosted reasoning
```

### 2. Start All Services
Launch Docker backing services, apply database migrations, and start both backend (port 8000) and frontend (port 3000) with a single command:

```bash
python start.py
```

- Open the web application: **`http://localhost:3000`**
- Interactive Swagger API docs: **`http://localhost:8000/docs`**

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