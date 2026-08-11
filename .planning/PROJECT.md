# MetaRadar — Project Context

## What This Is

> **One-Line Pitch:** MetaRadar is an AI-powered Haemophilia intelligence radar that converts scattered public signals — clinical trials, regulatory decisions, congress abstracts, competitor pipeline moves, and patient access narratives — into four targeted answers: **What changed? Why does it matter? Which Novo Nordisk function should review it? What action may be required?**

MetaRadar is built for the **Novo Nordisk GBS Hackathon 2026** (Problem Statement #3: "From Inbox Noise to Strategic Signal" | **Pilot Area: Haemophilia within Rare Disease**).

It converts fragmented external signals into role-specific, actionable intelligence for Novo Nordisk's **Medical Affairs**, **Regulatory**, **Market Access**, **Commercial**, and **R&D** teams.

### The Problem We're Solving
Haemophilia is undergoing its most significant paradigm shift in decades: from intravenous factor replacement to subcutaneous bispecific antibodies (emicizumab, concizumab, mim8) and single-administration gene therapies (Hemgenix, Roctavian). Critical signals about this shift are scattered across congress abstracts, PubMed publications, FDA/EMA filings, patient advocacy forums, and competitor announcements. No single function can monitor all of it manually. Current approaches (newsletters, manual search, email alerts) are fragmented, reactive, and slow.

### Core Architecture & Innovation
- **Multi-Source Ingestion:** Automated fetching every 2 hours from PubMed, NewsAPI, ClinicalTrials.gov, FDA OpenFDA, EMA RSS, Reddit PRAW (r/hemophilia, r/raredisease), and Congress Abstract archives (ASH, ISTH, WFH, EHA), plus a 500-signal synthetic demo fallback dataset.
- **6-Agent LangGraph Pipeline:** Ingestion Agent → Validation Agent → NLP Agent → Signal Confluence Agent → Narrative Synthesis Agent → Four-Question Brief Agent.
- **Signal Confluence Detection:** Detects when multiple independent signal types (e.g. clinical trial + regulatory decision + patient forum post) converge on the same haemophilia entity within a 48-hour window, generating a unified high-priority alert.
- **Four-Question UX Framework:**
  - **Panel 1 — What Changed?** Real-time signal feed tagged by signal type & entities.
  - **Panel 2 — Why Does It Matter?** AI relevance breakdown, confluence alert, & competitive context.
  - **Panel 3 — Which Function Should Review It?** Role-routing badges with confidence scores (Medical Affairs, Regulatory, Market Access, Commercial, R&D).
  - **Panel 4 — What Action May Be Required?** Max 3 AI-suggested action bullets prefaced with *"Suggested — requires human review"*.
- **Stakeholder Calibration Loop (HITL):** Baseline AI scoring is calibrated using structured feedback (relevance 1-5, urgency 1-5, actionability) from simulated Novo Nordisk stakeholder personas (Dr. Meera for Medical Affairs, Arjun for Regulatory, Priya for Market Access) processed by `StakeholderCalibrationService`.
- **Ask Athena RAG:** Natural language query interface using pgvector semantic search and local LLM summarization.

---

## Team & Roles

- **Organization:** MS Ramaiah Institute of Technology (MSRIT)
- **Team Members & Allocation:**
  - **Member 1 (CSE - ISE):** Backend Lead — FastAPI, LangGraph agents, PostgreSQL schema, pgvector RAG.
  - **Member 2 (CSE - ISE):** Frontend Lead — Next.js 15 dashboard, Four-Question UI, Recharts trends, API integration.
  - **Member 3 (B.Pharm):** Domain Lead — Haemophilia ontology, signal taxonomy, entity validation.
  - **Member 4 (B.Pharm):** Clinical Lead — Stakeholder personas, confluence clinical validation, action suggestion review.
  - **Member 5 (B.Pharm):** Narrative Lead — Domain narrative writing, Ask Athena accuracy testing, presentation domain slides.

---

## Timeline (4-Week Prototype Plan)

- **Week 1 (Aug 13-17): Foundation + Domain Architecture**
  - CSE: Next.js 15 + FastAPI skeleton, PostgreSQL + pgvector Docker setup, LangGraph 6-agent skeleton, NewsAPI + PubMed integration (haemophilia query terms), Docker Compose.
  - B.Pharm: Haemophilia signal taxonomy v1, pharmaceutical ontology draft (10 drugs, 6 companies, 2 indications), treatment paradigm mapping (factor → bispecific → gene therapy), role requirements doc.
  - *Milestone:* Working dashboard displaying raw haemophilia signals from 2 sources.

- **Week 2 (Aug 18-24): AI Pipeline + Intelligence Layer**
  - CSE: spaCy + ScispaCy NER (haemophilia entities), B.Pharm ontology JSON integration, DistilBART summarization, zero-shot signal classification, role-relevance scoring, Redis cache (2h TTL), APScheduler 2h fetch cycles.
  - B.Pharm: Ontology review & QA on 20 processed signals, draft stakeholder persona profiles.
  - *Milestone:* Full NLP pipeline working — signals enriched with entities, summaries, signal types, role scores.

- **Week 3 (Aug 25-31): Confluence Engine + Four-Question Dashboard**
  - CSE: Signal Confluence Engine, pgvector embeddings + hybrid search, Ask Athena RAG interface, Four-Question UI (Q1-Q4 panels), signal cards, stakeholder review widget, `StakeholderCalibrationService`.
  - B.Pharm: Validate confluence patterns, review Ask Athena responses, run simulated stakeholder review on 50 signals, validate Q4 action suggestions.
  - *Milestone:* Full MVP: Dashboard + Confluence + Ask Athena + Stakeholder Calibration Loop working.

- **Week 4 (Sep 1-7): Narrative Synthesis + Demo Hardening**
  - CSE: Narrative Synthesis Agent, temporal pattern matching, pre vs post calibration side-by-side demo, error handling, performance tuning (<500ms cached load), unit & integration tests (>60% coverage), demo video recording.
  - B.Pharm: Narrative synthesis clinical QA, demo script & slides, 2-page project report co-authoring.
  - *Milestone:* Final submission package (Docker Compose, 15-slide deck, 2-page report, GitHub repo, demo video).

---

## Key Technical & Architectural Decisions

| Decision | Rationale | Status |
|----------|-----------|--------|
| **PostgreSQL 16 + pgvector** | Unified relational and 384-dim vector storage in one container; eliminates vector DB overhead. | Final |
| **LangGraph 6-Agent Pipeline** | Composable state-machine orchestration for multi-agent ingestion, validation, NLP, confluence, synthesis, and briefing. | Final |
| **All Local AI Models (~870MB total)** | Zero API cost; spaCy `en_core_sci_md` (360MB), DistilBART (310MB), BART MNLI (120MB), `all-MiniLM-L6-v2` (80MB). All CPU-executable. | Final |
| **Stakeholder Calibration Service** | First-class HITL loop updating function relevance weights using stakeholder persona ratings. | Final |
| **Bronze Raw Layer (`raw_signals_bronze`)** | Verbatim raw JSON persistence before processing for complete data replayability. | Final |
| **WORM Audit Trail (`audit_log`)** | GxP / 21 CFR Part 11 compliant append-only table for regulatory traceability. | Final |
| **500-Signal Synthetic Demo Fallback** | Ensures reliable demo execution even if live public APIs fail or lack internet connection. | Final |

---

## Active Requirements

### Core Differentiators
- [ ] Signal Confluence Engine (cross-source convergence within 48h window)
- [ ] Four-Question Dashboard Interface (Q1: What changed?, Q2: Why does it matter?, Q3: Which function?, Q4: What action?)
- [ ] Stakeholder Calibration Loop (HITL feedback & score recalibration)
- [ ] B.Pharm Haemophilia Ontology (Hemlibra → emicizumab → Roche; mim8, concizumab, fitusiran, Hemgenix, Roctavian)
- [ ] Ask Athena RAG Conversational Interface
- [ ] Traceable Evidence Chain on every insight

### Table Stakes
- [ ] Multi-source public fetchers (PubMed, NewsAPI, ClinicalTrials.gov, OpenFDA, EMA RSS, Reddit, Congress archives, Mock 500 signals)
- [ ] Ingestion deduplication (>80% fuzzy title match) & quality validation
- [ ] spaCy ScispaCy NER entity extraction & PII scrubbing
- [ ] Model-agnostic local summarization & BART zero-shot classification
- [ ] PostgreSQL schema + pgvector hybrid search
- [ ] Redis caching & tenacity exponential backoff retry logic
- [ ] Next.js 15 dashboard with 5-role switching, trend charts, and source health telemetry

---

## Compliance & Guardrails
- **Public Data Only:** All data sourced strictly from public APIs and open archives.
- **No Confidential Data:** Zero internal Novo Nordisk strategy, patient-level data, or proprietary forecasts.
- **Human-in-the-Loop:** All action suggestions prefaced with *"Suggested — requires human review"*.
- **Traceable Intelligence:** Every insight links directly to source document URL, timestamp, and excerpt.
- **GxP Audit Compliance:** WORM `audit_log` table with revoked UPDATE/DELETE privileges.

---

*Last updated: August 2026 after Concept Note alignment*
