# MetaRadar v5.1 — Project Charter & Context

> **Project Name:** MetaRadar  
> **Subtitle:** Near-Real-Time Competitive Intelligence Radar  
> **Version:** 5.1 (Canonical Master Architecture Specification)  
> **Target Pilot Domain:** Haemophilia within Rare Disease (Novo Nordisk GBS Hackathon Problem Statement #3)  
> **Core Principle:** *"A conventional AI system summarizes documents. MetaRadar builds an evidence story around a development."*

---

## 1. Executive Summary

MetaRadar converts fragmented, multi-source competitive public signals (NCBI PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, EMA RSS, congress abstracts, and patient community discussions) into connected, evidence-backed developments and role-specific strategic actions for Novo Nordisk teams.

Instead of broadcasting unlinked news feeds to every user, MetaRadar processes external signals through a 10-node stateful workflow, identifies development timelines and evidence confluences, detects clinical contradictions, flags missing filings, and routes tailored intelligence to six target functions.

---

## 2. Core Stakeholder Personas & Target Functions

1. **Medical Affairs**: Focuses on clinical trial readouts, efficacy durability, biomarker expression (e.g. Factor IX/VIII levels), and congress abstracts.
2. **Regulatory**: Tracks FDA/EMA submissions, CHMP opinions, orphan drug designations, and PDUFA target dates.
3. **Safety / Pharmacovigilance**: Monitors adverse event signals, inhibitor development, liver toxicity, and thrombotic event reports.
4. **Market Access**: Evaluates ICER reports, pricing decisions, reimbursement hurdles, and country-specific access barriers.
5. **Medical Communications**: Monitors press release positioning, trial result disclosures, and congress presentation framing.
6. **Leadership (Commercial & R&D)**: Requires strategic executive overviews, portfolio momentum charts, and competitive risk assessments.

---

## 3. Technology Stack & Hardened Baseline

- **Frontend**: Next.js 16.3.0 (App Router), React 19, TypeScript 5.7.3, Tailwind CSS v4 (CSS-first `@theme inline`), Framer Motion 13, Recharts 3, Base UI / shadcn "base-nova" UI primitives. Strict TypeScript (`ignoreBuildErrors: false`) and ESLint 10 flat config (`eslint.config.mjs`).
- **Backend**: Python 3.11+, FastAPI `>=0.110.0`, Pydantic v2 (`>=2.6.0`), SQLAlchemy 2.0 async (`asyncpg`), Alembic async migration engine. PII/PHI scrubber (`PIIPHIScrubber`), Red-Team 19-rule registry (`RedTeamNLIService`), and an 18-point `pytest` test suite.
- **Database & Storage**: PostgreSQL 16 + pgvector (`384-dim` HNSW vector index with cosine similarity), Redis 7 (caching & non-blocking readiness healthchecks).
- **AI/ML Reasoning Chain**: Local Gemma 3 4B (`LLM_PROVIDER=local` on RTX 3050 4GB VRAM) -> xAI Grok Hosted Fallback (gated by strict `validate_privacy_gate`) -> Degraded BART Factual Summary Mode (`reasoning_available = False`).
- **Contract & CI Governance**: Automated OpenAPI 3.1 export to `contracts/openapi.json` and unified canonical contract at `frontend/types/api.ts`. GitHub Actions CI (`.github/workflows/ci.yml`) enforcing pytest, contract sync, `tsc`, `eslint`, and `next build` with least-privilege token permissions.

---

## 4. Five Core Intelligence Mechanisms

1. **Confluence Detection**: Identifies independent multi-source alignment (≥3 signal types within 48h) confirming a strategic shift.
2. **Signal Lifecycle Tracking**: Advances assets through a 9-stage finite state machine (Announced -> Preclinical -> Phase I -> Phase II -> Phase III -> Regulatory Submission -> Approved -> Post-Market / Discontinued).
3. **Red-Team Contradiction Analysis**: Evaluates pairwise contradictions across a 19-rule registry (Rules A–S) covering dosing, safety, efficacy, and regulatory claims.
4. **Missing-Signal Detection**: Monitors expected regulatory/trial milestones and stakeholder WATCH rules, flagging unexpected delays.
5. **Stakeholder Calibration Loop**: Adapts relevance scoring weights and function routing based on human-in-the-loop (HITL) expert feedback.

---

## 5. Four-Question Decision Interface

Every routed signal is presented via four structured decision panels:
- **Q1: What changed?** (Factual evidence summary with source provenance)
- **Q2: Why does it matter?** (Strategic impact on Novo Nordisk's portfolio vs. competitors like emicizumab, Hemgenix, Roctavian)
- **Q3: Which function is impacted?** (Relevance scores for Medical Affairs, Regulatory, Safety, Access, Comms, Leadership)
- **Q4: What action is recommended?** (Specific, role-tailored strategic recommendations with FACT/INTERPRETATION/SPECULATION labels)
