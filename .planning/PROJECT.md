# MetaRadar v5.1 — Project Charter & Context

> **Project Name:** MetaRadar  
> **Subtitle:** Near-Real-Time Competitive Intelligence Radar  
> **Version:** 5.1 (Canonical Master Architecture Specification & Hardened Operational Platform)  
> **Active Milestone:** Milestone v5.1 Extension — Trustworthy Intelligence & Platform Hardening (Phases 07–08: Completed & Verified)  
> **Reference Specification:** [`docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md)  
> **Target Pilot Domain:** Haemophilia within Rare Disease (Novo Nordisk GBS Hackathon Problem Statement #3)  
> **Core Principle:** *"A conventional AI system summarizes documents. MetaRadar builds an evidence story around a development."*

---

## Active Milestone & Current State

- **Milestone v5.1 Shipped (2026-08-19)**: Delivered baseline architecture (Phases 0–6) with 80 passing pytest suites and full doc-to-UI feature synchronization.
- **Milestone v5.1 Extension Shipped (2026-08-21)**: Phases 07 & 08 completed & verified (114 passing pytest tests, 0 ESLint warnings, 0 type errors, Next.js 16 production build, end-to-end source provenance and truthful observability).

---

## What This Is

MetaRadar is a near-real-time competitive intelligence platform that converts fragmented multi-source public signals (PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, EMA RSS, congress abstracts) into structured evidence stories, development timelines, and role-tailored strategic actions for Novo Nordisk cross-functional teams.

## Core Value

*"A conventional AI system summarizes documents. MetaRadar builds an evidence story around a development."* — Transforming raw biomedical noise into calibrated strategic intelligence across Medical Affairs, Regulatory, Safety, Market Access, Comms, and Leadership.

## Requirements

### Shipped Baseline & Hardening (Phases 00–09)
- [x] Phase 0: Baseline Stabilization & Quality Governance (Next.js 16 + FastAPI + Alembic + PII/PHI scrubber + Red-Team engine)
- [x] Phase 1: Ingestion Connectors & Data Pipeline (PubMed, ClinicalTrials, NewsAPI, OpenFDA, EMA RSS + Bronze storage + Deduplication)
- [x] Phase 2: LangGraph 10-Node Intelligence Engine (MetaRadarState + 10 workflow nodes + PipelineRunner + 51 tests)
- [x] Phase 3: Vector Search & LLM Provider Execution (fastembed 384-dim embeddings + pgvector HNSW search + Ollama Gemma 3 4B + Grok privacy gate)
- [x] Phase 4: Frontend API Integration & Real-Time Workspace (Next.js App Router live REST client + portfolio momentum + confluence radar)
- [x] Phase 5: Calibration & End-to-End Verification (Stakeholder feedback loop + haemophilia demo story + Definition of Done audit)
- [x] Phase 6: Full Doc-to-UI Mapping, Parity & Launchers (100% feature parity matrix, 8 dedicated intelligence pages, zero-config `setup.py`, and `start.py`)
- [x] Phase 7: Trustworthy Intelligence Reconciliation & Platform Hardening (Eliminated mock telemetry, synthetic data governance, priority scoring, structured logging, invariant testing)
- [x] Phase 8: Provenance Traceability + Canonical Overview/Lifecycle Design System Hardening (Full end-to-end source provenance, truthful connector observability, unified design system & theme across all 9 workspaces)

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
- **Backend**: Python 3.11+, FastAPI `>=0.110.0`, Pydantic v2 (`>=2.6.0`), SQLAlchemy 2.0 async (`asyncpg`), Alembic async migration engine. PII/PHI scrubber (`PIIPHIScrubber`), Red-Team 19-rule registry (`RedTeamNLIService`), and an 80-point `pytest` test suite.
- **Database & Storage**: PostgreSQL 16 + pgvector (`384-dim` HNSW vector index with cosine similarity), Redis 7 (caching & non-blocking readiness healthchecks).
- **AI/ML Reasoning Chain**: Local Gemma 3 4B (`LLM_PROVIDER=local` on RTX 3050 4GB VRAM) -> xAI Grok Hosted Fallback (gated by strict `validate_privacy_gate`) -> Degraded BART Factual Summary Mode (`reasoning_available = False`).
- **Contract & CI Governance**: Automated OpenAPI 3.1 export to `contracts/openapi.json` and unified canonical contract at `frontend/types/api.ts`. GitHub Actions CI (`.github/workflows/ci.yml`) enforcing pytest, contract sync, `tsc`, `eslint`, and `next build` with least-privilege token permissions.
- **Operations & Orchestration**: Single-command zero-config environment setup (`python setup.py`) and unified process launcher (`python start.py`).

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
