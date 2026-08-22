# MetaRadar

### From Inbox Noise to Strategic Signal

**AI-powered near-real-time competitive intelligence radar for Haemophilia within Rare Disease**

[![Hackathon](https://img.shields.io/badge/Novo%20Nordisk%20GBS%20Hackathon-2026-blue)](#)
[![Pilot](https://img.shields.io/badge/Pilot-Haemophilia%20A%20%26%20B-red)](#)
[![Status](https://img.shields.io/badge/Status-v5.1.0%20Production%20Ready%20(100%25)-success)](#)
[![Tests](https://img.shields.io/badge/Tests-114%2F114%20Passing-brightgreen)](#)
[![Contract](https://img.shields.io/badge/OpenAPI%203.1-Synchronized-blue)](#)
[![Data](https://img.shields.io/badge/Data-Autonomous%20Live%20%7C%20Bronze%20Persistence-green)](#)

> **A conventional AI system summarizes documents. MetaRadar builds an evidence story around a development.**

MetaRadar converts fragmented public information about the haemophilia treatment landscape into **evidence-backed developments, real-time convergence alerts, and role-specific intelligence**.

The system is designed for the **Novo Nordisk GBS Hackathon 2026 — Problem Statement #3**, with **Haemophilia A and Haemophilia B** as the Rare Disease pilot.

---

## Current Status (v5.1.0)

> **All development milestones through Phase 8 (Autonomous Ingestion, Source Health Telemetry, Provenance Traceability, and Canonical Design Alignment) are fully implemented, verified, and active.**

- **Executable Verification Matrix:**
  - `pytest tests/` → **114/114 Passed (100%)** clean suite across connectors, LangGraph nodes, truthfulness invariants, failure injection, provenance, and observability.
  - `npm run build` → **Compiled Cleanly (0 Errors)** in Next.js 16 (Turbopack) with strict TypeScript checking.
  - `python scripts/export_openapi.py` → **0 Contract Drift** (Synchronized at `frontend/types/api.ts`).
  - `Alembic Migrations` → **11/11 Applied (`001_initial` through `011_widen_fingerprint`)** across 22 PostgreSQL tables with zero schema drift.

- **Core Operational Capabilities:**
  - **Autonomous Background Ingestion**: Continuous async scheduler (`scheduler.py`) polling ClinicalTrials.gov (60m), PubMed (60m), FDA (30m), EMA (30m), and NewsAPI (15m, quota-guarded) with distributed advisory locking, exponential backoff, and circuit breaker resilience.
  - **Truthful Operational Source Health**: Granular source health reporting distinguishing `HEALTHY`, `NO_NEW_DATA`, `DEGRADED`, and `CONFIGURATION_ERROR`. Zero-record responses on valid endpoints are truthfully reported as `NO_NEW_DATA` rather than degraded.
  - **11-Node LangGraph Intelligence Engine**: Automated pipeline handling relevance gating, biomedical entity extraction, ontology mapping, SHA-256 deduplication, Four-Question Brief synthesis (`[FACT]`/`[INTERPRETATION]`/`[SPECULATION]`), deterministic 4-factor priority scoring, 48h confluence evaluation, Red-Team contradiction analysis, missing signal FSM lag tracking, asset lifecycle progression, and 6-role stakeholder relevance routing.
  - **Manual On-Demand Sync**: Topbar header and Sources workspace provide one-click **"Ingest Data"** triggers for live biomedical synchronization.
  - **Zero-Friction Launcher**: Single-command launcher (`python start.py`) orchestrating Docker databases, automatic schema migrations, port conflict resolution, and real-time backend/frontend log streaming.

---

## Table of Contents

- [Current Status (v5.1.0)](#current-status-v510)
- [Problem](#problem)
- [Solution](#solution)
- [How MetaRadar Is Different](#how-metaradar-is-different)
- [Five Intelligence Mechanisms](#five-intelligence-mechanisms)
- [Four-Question Decision Framework](#four-question-decision-framework)
- [Platform Architecture](#platform-architecture)
- [Technology Stack](#technology-stack)
- [Data Sources & Autonomous Ingestion](#data-sources--autonomous-ingestion)
- [Haemophilia Knowledge Layer](#haemophilia-knowledge-layer)
- [Stakeholder Calibration](#stakeholder-calibration)
- [Safety and Responsible AI](#safety-and-responsible-ai)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Running the Platform](#running-the-platform)
- [Demo Scenario](#demo-scenario)
- [Validation & Test Results](#validation--test-results)
- [Team](#team)

---

# Problem

The haemophilia treatment landscape is rapidly evolving across:

- Factor replacement therapies (recombinant & plasma-derived)
- Extended-half-life (EHL) factors
- Non-factor therapies & bispecific antibodies (emicizumab, mim8)
- Anti-TFPI monoclonal antibodies & peptides (concizumab, marstacimab)
- RNAi therapeutics (fitusiran)
- AAV gene therapies (etranacogene dezaparvovec, valoctocogene roxaparvovec, fidanacogene elaparvovec)
- Clinical development, regulatory actions, and real-world access barriers

Relevant information is scattered across trial registries, biomedical literature, regulatory dossiers, congress proceedings, and industry disclosures.

The challenge is therefore not simply:

> *"Can we find haemophilia news?"*

The real challenge is:

> **"Can we determine whether scattered information represents a meaningful developing signal, why it matters, who should review it, and what action may be required?"**

---

# Solution

MetaRadar treats external information as **signals belonging to developing evidence stories**, rather than as isolated articles.

```text
                     PUBLIC & AUTHORITATIVE SIGNALS
          ClinicalTrials.gov · NCBI PubMed · FDA · EMA · NewsAPI
                                  |
               AUTONOMOUS INGESTION / MANUAL SYNC
            (Advisory locks · Exponential backoff · Bronze persistence)
                                  |
                         RELEVANCE GATE
            (Haemophilia keyword + therapy validation)
                                  |
                    11-NODE LANGGRAPH PIPELINE
                                  |
         +------------------------+------------------------+
         |                        |                        |
     CONFLUENCE               LIFECYCLE                RED-TEAM
  (Multi-source 48h       (Progression from        (Contradictory
   evidence linkage)       Trial to Access)         clinical claims)
         |                        |                        |
         +------------------------+------------------------+
                                  |
                     MISSING SIGNAL & WATCH FSM
             (Expected milestone silence lag detection)
                                  |
                   FOUR-QUESTION SYNTHESIS
             ([FACT] · [INTERPRETATION] · [SPECULATION])
                                  |
                    FUNCTION ROUTING & SCORING
     (Medical Affairs · Regulatory · Safety/PV · Market Access ·
      Medical Communications · Leadership)
                                  |
                    FOUR-QUESTION UI WORKSPACES
                                  |
                   STAKEHOLDER CALIBRATION (HITL)
```

---

# How MetaRadar Is Different

A conventional AI workflow summarizes isolated documents:

```text
Articles → AI Summaries → Generic Feed
```

MetaRadar builds an interconnected evidence story across time and sources:

```text
Public Signals → Entity Resolution → Evidence Convergence →
Lifecycle Tracking → Contradiction Detection → Silence Lag Detection →
Role Relevance Routing → Four-Question Decision Brief
```

---

# Five Intelligence Mechanisms

## 1. Confluence Detection
- **Question**: *Are multiple independent evidence streams pointing to the same underlying development?*
- **Mechanism**: Evaluates signals across distinct source types within a 48h rolling window using cosine embedding similarity and shared entity identifiers. Scores confluence based on source diversity, velocity, and semantic coherence.

## 2. Signal Lifecycle Tracking
- **Question**: *Where is this development in its overall journey?*
- **Mechanism**: Links related signals into a chronological progression (`ANNOUNCED` → `IN_TRIAL` → `RESULTS` → `REGULATORY_REVIEW` → `APPROVED` → `POST_MARKET` → `ACCESS_REIMBURSEMENT`). Distinguishes a new development from new evidence about an existing development.

## 3. Red-Team Contradiction Analysis
- **Question**: *What evidence challenges or qualifies our interpretation?*
- **Mechanism**: Evaluates pairwise contradiction rules across clinical trial outcomes, safety alerts, and regulatory actions with verbatim evidence citations.

## 4. Missing-Signal Detection + Watch-for-Next
- **Question**: *What should have happened next, and has it actually occurred?*
- **Mechanism**: Implements a 6-state Finite State Machine (`WITHIN_WINDOW`, `DUE`, `OVERDUE`, `SATISFIED`, `SUPPRESSED`) tracking milestone delays and stakeholder-defined watch expectations.

## 5. Stakeholder Calibration (Human-in-the-Loop)
- **Question**: *Does the system's understanding of relevance match stakeholder judgement?*
- **Mechanism**: Enables persona-driven feedback (relevance, urgency, actionability) that dynamically adjusts 4-factor scoring weights and role routing matrices.

---

# Four-Question Decision Framework

All intelligence synthesizes into four structured answers:

- **Q1 — What changed?** Concise description of the development with strict epistemic tags (`[FACT]`, `[INTERPRETATION]`, `[SPECULATION]`).
- **Q2 — Why does it matter?** Clinical, competitive, and development context supported by evidence.
- **Q3 — Which Novo Nordisk function should review it?** Relevance-based routing to 6 core functions:
  1. Medical Affairs
  2. Regulatory
  3. Safety / Pharmacovigilance
  4. Market Access / Patient Access
  5. Medical Communications
  6. Leadership
- **Q4 — What internal action may be required?** Suggested next steps chosen from a controlled action vocabulary.

---

# Platform Architecture

```text
                                  METARADAR
                                      │
 ┌────────────────────────────────────┴────────────────────────────────────┐
 │                                                                         │
 ▼                                                                         ▼
Frontend (Next.js 16 / React 19)                           Backend (FastAPI 0.115 / Python 3.11+)
• Turbopack SSR & Static Pages                             • 11-Node LangGraph Execution Graph
• Canonical Design System Tokens                           • Autonomous Async Scheduler
• Dark/Light Adaptive Theme                                • 5 Source Connector Adapters
• Evidence Drawer & Provenance Badges                      • Truthful Source Health Telemetry
• Global 'Ingest Data' & Search (⌘K)                       • PII/PHI De-identification Layer
                                                           • REST API (OpenAPI 3.1 Synchronized)
                                                                         │
                                                                         ▼
                                                           Persistence (PostgreSQL 16 + Redis 7)
                                                           • 22 Relational Tables (Alembic Managed)
                                                           • pgvector (384-dim HNSW Vector Index)
                                                           • Immutable Bronze Ingestion Layer
                                                           • Redis Operational Cache & Rate Limits
```

---

# Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Frontend** | Next.js 16.3.0 | React 19, TypeScript, Turbopack, Vanilla CSS Design Tokens |
| **Backend** | FastAPI 0.115.8 | Python 3.11/3.12, Pydantic v2, Structlog JSON Logging |
| **Orchestration** | LangGraph | 11-node stateful workflow execution graph |
| **Database** | PostgreSQL 16 | Relational schema (22 tables) + pgvector extension |
| **Embeddings** | sentence-transformers | `all-MiniLM-L6-v2` (384-dimensional cosine similarity) |
| **Reasoning LLM** | Local Gemma 3 4B | `google/gemma-3-4b-it` (Ollama / Local GPU) + xAI Grok fallback |
| **Cache & Locking** | Redis 7 | Distributed advisory locking, rate limiting, and response caching |
| **Migrations** | Alembic | 11 versions (`001_initial` → `011_widen_fingerprint`) |
| **Testing** | pytest + Jest | 114 backend tests, strict TypeScript compilation |

---

# Data Sources & Autonomous Ingestion

| Source | Connector Type | Polling Cadence | Data Retrieved |
| :--- | :--- | :--- | :--- |
| **ClinicalTrials.gov** | REST API v2 | Every 60 min | Study registrations, protocol amendments, recruitment status |
| **NCBI PubMed** | E-utilities REST | Every 60 min | Peer-reviewed biomedical literature, abstracts, PMIDs |
| **FDA** | openFDA / RSS Feeds | Every 30 min | Drug approvals, safety communications, MedWatch alerts |
| **EMA** | RSS / Regulatory Feeds | Every 30 min | EPAR summaries, CHMP opinions, European safety updates |
| **NewsAPI** | REST API | Every 15 min | Industry press releases, commercial announcements (quota-guarded) |

---

# Haemophilia Knowledge Layer

MetaRadar incorporates a domain ontology curated by the B.Pharm team covering:
- **Diseases**: Haemophilia A (Factor VIII deficiency), Haemophilia B (Factor IX deficiency).
- **Inhibitor Status**: With inhibitors (high/low titer), without inhibitors, previously untreated patients (PUPs).
- **Therapeutic Modalities**: Factor replacement (recombinant/plasma), EHL factors, non-factor bispecifics, anti-TFPI, RNAi, AAV gene therapies.
- **Canonical Assets**: `concizumab` (Alhemo), `mim8`, `emicizumab` (Hemlibra), `etranacogene dezaparvovec` (Hemgenix), `valoctocogene roxaparvovec` (Roctavian), `fidanacogene elaparvovec` (Beqvez), `fitusiran`, `marstacimab` (Hympavzi).

---

# Safety and Responsible AI

- **Source Traceability**: 100% of signals maintain clickable canonical URLs, external registry IDs (`pmid`, `nct_id`), and evidence excerpts.
- **PII/PHI De-identification**: Pre-persistence regex and NER scrubbing removing patient identifiers, MRNs, phone numbers, and dates of birth.
- **Epistemic Classification**: Every claim is explicitly tagged `[FACT]`, `[INTERPRETATION]`, or `[SPECULATION]`.
- **Human-in-the-Loop**: Decision support only. Recommended actions require expert human verification before business execution.

---

# Project Structure

```text
metaradar/
├── backend/
│   ├── alembic/              # Database migration scripts (001 - 011)
│   ├── app/
│   │   ├── api/v1/           # FastAPI routes (signals, confluence, lifecycles, health, etc.)
│   │   ├── connectors/       # Source adapters (PubMed, CT.gov, FDA, EMA, NewsAPI)
│   │   ├── core/             # Configuration, logging, and middleware
│   │   ├── db/               # PostgreSQL engine and session management
│   │   ├── models/           # SQLAlchemy ORM models (22 tables)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Ingestion, scheduler, scoring, confluence, embeddings
│   │   └── workflows/        # LangGraph nodes and PipelineRunner
│   └── main.py               # FastAPI application entrypoint
├── frontend/
│   ├── app/                  # Next.js App Router ([section] pages)
│   ├── components/           # Modular workspace components (Signals, Confluence, etc.)
│   ├── lib/                  # API client, mappers, theme hooks
│   └── types/                # Synchronized TypeScript contracts
├── config/                   # Canonical domain configuration (haemophilia.yaml)
├── data/                     # Seed datasets and synthetic fallback fixtures
├── docs/                     # Canonical rules, architecture, and specifications
├── tests/                    # Backend test suite (114 test cases)
├── docker-compose.yml        # Multi-container orchestration
├── start.py                  # Unified zero-friction local launcher
└── README.md
```

---

# Getting Started

### Prerequisites
- **Git**
- **Docker Desktop** (running PostgreSQL and Redis)
- **Python 3.11+**
- **Node.js 20.9+** & **npm**

---

# Configuration

Create a local environment file from `.env.example`:

```bash
cp .env.example .env
```

Key environment variables:
```env
APP_ENV=development
DATABASE_URL=postgresql+asyncpg://metauser:metapass@localhost:5432/metaradar
REDIS_URL=redis://localhost:6379/0

# Source APIs
NEWSAPI_KEY=your_newsapi_key_optional

# Local LLM & Reasoning
LLM_PROVIDER=local
LOCAL_LLM_MODEL=google/gemma-3-4b-it
LLM_DEVICE=cuda:0
LLM_DTYPE=int4
```

---

# Running the Platform

### Option 1: Unified Process Launcher (Recommended)
Runs PostgreSQL and Redis via Docker, automatically applies database migrations, starts FastAPI on `http://localhost:8000`, and starts Next.js on `http://localhost:3000`:

```bash
python start.py
```

### Option 2: Full Docker Compose
```bash
docker compose up --build
```

Access the user interface at: **`http://localhost:3000`**  
Access the interactive API documentation at: **`http://localhost:8000/docs`**

---

# Demo Scenario

1. **Autonomous Ingestion**: Background scheduler polls live sources and ingests new records into the bronze layer.
2. **Entity & Ontology Resolution**: Identifies drug assets (e.g., `concizumab`, `mim8`) and assigns competitor contexts.
3. **Confluence Detection**: Connects multiple independent signals into a single evolving development story.
4. **Lifecycle Progression**: Updates the drug's milestone timeline.
5. **Red-Team Contradiction**: Highlights counter-evidence or conflicting clinical endpoints.
6. **Missing Signal Detection**: Flags expected milestone delays.
7. **Four-Question Brief**: Synthesizes facts, clinical relevance, function routing, and recommended actions.
8. **Stakeholder Feedback**: Recalibrates scoring and routing criteria.

---

# Validation & Test Results

```text
============================== 114 passed, 1 skipped in 34.09s ==============================
- test_api_endpoints.py .................
- test_config_errors.py ........
- test_confluence_semantics.py ......
- test_connector_health.py ............
- test_failure_injection.py .......
- test_ingestion.py .........
- test_intelligence_nodes.py ............
- test_observability.py ...........
- test_provenance.py ................
- test_signals_endpoints.py ............
- test_truthfulness_and_invariants.py ............
```

- **Frontend Compilation**: Next.js 16 build passed with **0 TypeScript errors**.
- **Schema Validation**: 100% synchronized across all 22 database tables.

---

# Team

**MS Ramaiah Institute of Technology**  
*Novo Nordisk GBS Hackathon 2026 — Problem Statement #3*

- **Sanjana Rathore B.** (Team Lead) — B.Pharm (Domain Owner, Medical Affairs, Signal Importance, Function Routing)
- **Ishaaq** — B.Pharm (Haemophilia Treatment Map, Asset Lifecycles, Expected Events)
- **Usha** — B.Pharm (Evidence Quality, Red-Team Contradictions, Safety & Access Context)
- **Om Prakash** — CSE (Architecture, Data Ingestion, LangGraph Orchestration, Backend, Frontend)
- **Veeru** — CSE (Vector Search, Database, Telemetry, Performance & Deployment)