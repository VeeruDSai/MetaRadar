# MetaRadar v5.1 — Project Charter & Context

> **Project Name:** MetaRadar  
> **Subtitle:** Near-Real-Time Competitive Intelligence Radar  
> **Version:** 5.1 (Canonical Master Architecture Specification)  
> **Target Pilot Domain:** Haemophilia within Rare Disease (Novo Nordisk GBS Hackathon Problem Statement #3)  
> **Core Principle:** *"A conventional AI system summarizes documents. MetaRadar builds an evidence story around a development."*

---

## What This Is

MetaRadar is a near-real-time competitive intelligence platform that converts fragmented multi-source public signals (PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, EMA RSS, congress abstracts) into structured evidence stories, development timelines, and role-tailored strategic actions for Novo Nordisk cross-functional teams.

## Core Value

*"A conventional AI system summarizes documents. MetaRadar builds an evidence story around a development."* — Transforming raw biomedical noise into calibrated strategic intelligence across Medical Affairs, Regulatory, Safety, Market Access, Comms, and Leadership.

## Requirements

### Validated
- [x] Phase 0: Baseline Stabilization & Quality Governance (Next.js 16 + FastAPI 0.115 + Alembic + PII/PHI scrubber + Red-Team engine)
- [x] Phase 2: LangGraph 10-Node Intelligence Engine (MetaRadarState + 10 workflow nodes + PipelineRunner + 51 unit/integration tests)

### Active
- [ ] Phase 3: Vector Search & LLM Provider Execution (fastembed 384-dim embeddings + pgvector HNSW cosine search + Ollama Gemma 3 4B + Grok privacy gate)
- [ ] Phase 4: Frontend API Integration & Real-Time Workspace (Next.js App Router live REST client + portfolio momentum + confluence radar)
- [ ] Phase 5: Calibration & End-to-End Verification (Stakeholder feedback loop + haemophilia demo story + Definition of Done audit)

### Out of Scope
- Fine-tuning local LLM weights (deferred to dedicated model training phase)
- Multi-tenant cloud identity provider integration (scoped to local role-based simulation)
- Autonomous internet scraper loops (all data acquired through governed API connectors and bronze staging)

---

## Executive Summary

Instead of broadcasting unlinked news feeds to every user, MetaRadar processes external signals through a 10-node stateful workflow, identifies development timelines and evidence confluences, detects clinical contradictions, flags missing filings, and routes tailored intelligence to six target functions.

---

## Core Stakeholder Personas & Target Functions

1. **Medical Affairs**: Focuses on clinical trial readouts, efficacy durability, biomarker expression (e.g. Factor IX/VIII levels), and congress abstracts.
2. **Regulatory**: Tracks FDA/EMA submissions, CHMP opinions, orphan drug designations, and PDUFA target dates.
3. **Safety / Pharmacovigilance**: Monitors adverse event signals, inhibitor development, liver toxicity, and thrombotic event reports.
4. **Market Access**: Evaluates ICER reports, pricing decisions, reimbursement hurdles, and country-specific access barriers.
5. **Medical Communications**: Monitors press release positioning, trial result disclosures, and congress presentation framing.
6. **Leadership (Commercial & R&D)**: Requires strategic executive overviews, portfolio momentum charts, and competitive risk assessments.

---

## Technology Stack & Hardened Baseline

- **Frontend**: Next.js 16.3.0 (App Router), React 19, TypeScript 5.7.3, Tailwind CSS v4 (CSS-first `@theme inline`), Framer Motion 13, Recharts 3, Base UI / shadcn "base-nova" UI primitives. Strict TypeScript (`ignoreBuildErrors: false`) and ESLint 10 flat config (`eslint.config.mjs`).
- **Backend**: Python 3.11+, FastAPI `>=0.110.0`, Pydantic v2 (`>=2.6.0`), SQLAlchemy 2.0 async (`asyncpg`), Alembic async migration engine. PII/PHI scrubber (`PIIPHIScrubber`), Red-Team 19-rule registry (`RedTeamNLIService`), and an 18-point `pytest` test suite.
- **Database & Storage**: PostgreSQL 16 + pgvector (`384-dim` HNSW vector index with cosine similarity), Redis 7 (caching & non-blocking readiness healthchecks).
- **AI/ML Reasoning Chain**: Local Gemma 3 4B (`LLM_PROVIDER=local` on RTX 3050 4GB VRAM) -> xAI Grok Hosted Fallback (gated by strict `validate_privacy_gate`) -> Degraded BART Factual Summary Mode (`reasoning_available = False`).
- **Contract & CI Governance**: Automated OpenAPI 3.1 export to `contracts/openapi.json` and unified canonical contract at `frontend/types/api.ts`. GitHub Actions CI (`.github/workflows/ci.yml`) enforcing pytest, contract sync, `tsc`, `eslint`, and `next build` with least-privilege token permissions.

---

## Five Core Intelligence Mechanisms

1. **Confluence Detection**: Identifies independent multi-source alignment (≥3 signal types within 48h) confirming a strategic shift.
2. **Signal Lifecycle Tracking**: Advances assets through a 9-stage finite state machine (Announced -> Preclinical -> Phase I -> Phase II -> Phase III -> Regulatory Submission -> Approved -> Post-Market / Discontinued).
3. **Red-Team Contradiction Analysis**: Evaluates pairwise contradictions across a 19-rule registry (Rules A–S) covering dosing, safety, efficacy, and regulatory claims.
4. **Missing-Signal Detection**: Monitors expected regulatory/trial milestones and stakeholder WATCH rules, flagging unexpected delays.
5. **Stakeholder Calibration Loop**: Adapts relevance scoring weights and function routing based on human-in-the-loop (HITL) expert feedback.

---

## Four-Question Decision Interface

Every routed signal is presented via four structured decision panels:
- **Q1: What changed?** (Factual evidence summary with source provenance)
- **Q2: Why does it matter?** (Strategic impact on Novo Nordisk's portfolio vs. competitors like emicizumab, Hemgenix, Roctavian)
- **Q3: Which function is impacted?** (Relevance scores for Medical Affairs, Regulatory, Safety, Access, Comms, Leadership)
- **Q4: What action is recommended?** (Specific, role-tailored strategic recommendations with FACT/INTERPRETATION/SPECULATION labels)
