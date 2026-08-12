<!-- refreshed: 2026-08-13 -->
# Architecture

**Analysis Date:** 2026-08-13

> **Current state:** This repository contains the *specification* of the MetaRadar architecture (docs only). The architecture below is the **prescribed design** defined in the canonical [`docs/METARADAR_MASTER_PLAN_v3.0.md`](docs/METARADAR_MASTER_PLAN_v3.0.md) §4 and detailed in [`docs/3_SOFTWARE_DESIGN_DOCUMENT.md`](docs/3_SOFTWARE_DESIGN_DOCUMENT.md). No implementation exists yet.

## System Overview

```text
┌──────────────────────────────────────────────────────────────────┐
│                     PUBLIC EXTERNAL SIGNALS                        │
│  LIVE: PubMed/PMC · NewsAPI · ClinicalTrials.gov                  │
│  ADAPTER-READY: FDA · EMA · Congress (ASH/ISTH/WFH/EHA) · Reddit  │
│  SYNTHETIC-DEMO: 500 curated labelled haemophilia signals          │
└───────────────────────────────┬──────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                 10-NODE LANGGRAPH WORKFLOW (backend)              │
│  ingest → validate → nlp_extract → ontology_enrich → confluence   │
│  → lifecycle → redteam → missing_signal → synthesize → calibrate  │
└───────────────────────────────┬──────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  FOUR-QUESTION DECISION INTERFACE (Next.js 15 frontend)          │
│  Q1 What changed? · Q2 Why it matters · Q3 Which function?        │
│  Q4 What action? + Evidence chain + F-I-S labels                  │
└───────────────────────────────┬──────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  PostgreSQL 16 + pgvector · Redis 7 · Celery/APScheduler         │
│  (relational + vector store, cache/rate-limit, 2h fetch schedule) │
└──────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | Source spec |
|-----------|----------------|------|
| Frontend dashboard | Four-Question panels, signal cards, lifecycle timelines, calibration BEFORE/AFTER widget | [`docs/4_UI_DESIGN_DOCUMENT.md`](docs/4_UI_DESIGN_DOCUMENT.md) |
| FastAPI backend API | REST endpoints, serves dashboard + Ask Athena (RAG Q&A) | [`docs/3_SOFTWARE_DESIGN_DOCUMENT.md`](docs/3_SOFTWARE_DESIGN_DOCUMENT.md) |
| LangGraph workflow | 10-node orchestration of ingestion → intelligence → calibration | [`docs/METARADAR_MASTER_PLAN_v3.0.md`](docs/METARADAR_MASTER_PLAN_v3.0.md) §4 |
| Ingestion connectors | `httpx` async fetch from live APIs, `tenacity` retries | `docs/METARADAR_MASTER_PLAN_v3.0.md` §4 node 1 |
| Haemophilia ontology | B.Pharm-maintained knowledge graph (disease/therapy/asset/company) | `README.md` "Haemophilia Knowledge Layer" |
| StakeholderCalibrationService | HITL weight recalibration of function scoring, WORM logging | `docs/METARADAR_MASTER_PLAN_v3.0.md` §6 mech 5 |

## Pattern Overview

**Overall:** Event-sourced intelligence pipeline — public signals are treated as *evidence events belonging to developing stories*, orchestrated as a stateful LangGraph workflow (`docs/METARADAR_MASTER_PLAN_v3.0.md` §4).

**Key Characteristics:**
- Signal-first, evidence-linked modeling: each signal persists to `raw_signals_bronze` (verbatim) before processing
- Lifecycle FSM: `announced → in_trial → interim_result → final_result → congress_publication → regulatory_development → approved → post_market | discontinued`
- Every lifecycle event records `event_type · event_date · development_id · source_id`
- F-I-S labeling (FACT / INTERPRETATION / SPECULATION) on all AI outputs with evidence-sufficiency gate
- One engine routes to six functions (Medical Affairs, Regulatory, Safety/PV, Market Access, Medical Communications, Leadership) + extended roles (Commercial, R&D)

## Layers

**Frontend Layer:**
- Purpose: Decision-first UI — Four-Question panels, evidence chain, function routing badges, watch items
- Location: `frontend/` (planned, per `README.md` "Project Structure")
- Contains: `app/`, `components/`, `lib/`, `public/`, `package.json`
- Depends on: FastAPI backend via REST
- Used by: Stakeholder personas (Medical Affairs, Regulatory, etc.)

**API Layer:**
- Purpose: Expose workflow results; serve dashboard queries and Ask Athena
- Location: `backend/app/api/` (planned)
- Contains: FastAPI routers, request/response schemas
- Depends on: LangGraph workflow + services
- Used by: Frontend

**Intelligence/Workflow Layer:**
- Purpose: The 10-node LangGraph graph — ingestion validation, NER + ontology enrichment, Confluence, Lifecycle, Red-Team, Missing-Signal, Synthesis, Calibration
- Location: `backend/app/intelligence/` + `backend/app/agents/` (planned)
- Depends on: local models (spaCy, BART, Gemma), ontology, DB
- Used by: API layer

**Persistence Layer:**
- Purpose: Raw signal replay, normalized signals, entities, vector embeddings, calibration history, WORM audit log
- Location: PostgreSQL 16 + pgvector (planned `docker-compose.yml`); Redis 7 cache
- Used by: All layers

## Data Flow

### Primary Request Path (signal → intelligence card)

1. Signal fetch — `node_ingest` pulls raw JSON via `httpx` from PubMed/NewsAPI/ClinicalTrials.gov; persists verbatim to `raw_signals_bronze` (`docs/METARADAR_MASTER_PLAN_v3.0.md` §4 node 1)
2. Validation — `node_validate` filters short (<50 chars), non-English, out-of-scope content; PII scrub (`docs/METARADAR_MASTER_PLAN_v3.0.md` §4 node 2)
3. Extraction — `node_nlp_extract` spaCy `en_core_sci_md` NER (drugs, companies, indications, trial IDs) (`node 3`)
4. Ontology enrichment — `node_ontology_enrich` maps entities (e.g., Hemlibra → emicizumab → Roche → bispecific) (`node 4`)
5. Intelligence — Confluence (48h window, ≥3 signal types; congress/publication link to existing development), Lifecycle FSM advance, Red-Team NLI contradiction, Missing-Signal WATCH evaluation (`nodes 5–8`)
6. Synthesis — evidence-sufficiency gate → F-I-S labels → Four-Question brief via Gemma 3 4B (`node 9`)
7. Calibration — stakeholder feedback updates scoring weights via `StakeholderCalibrationService`, WORM-logged (`node 10`)

### Ask Athena (RAG Q&A)

1. User question → vector search over saved signals via pgvector (all-MiniLM-L6-v2 384-dim)
2. Retrieve top relevant signal excerpts → grounded prompt to local LLM
3. Answer constrained to retrieved evidence; insufficient → "insufficient" response, never invented (`docs/4_UI_DESIGN_DOCUMENT.md` §1.1, `docs/3_SOFTWARE_DESIGN_DOCUMENT.md`)

**State Management:**
- Postgres (authoritative), Redis 2h-TTL hot cache; LangGraph state machine carries workflow state; FSM lifecycle state per development

## Key Abstractions

**Signal:**
- Purpose: Unit of public intelligence (article, trial result, filing, forum post) with entity tags
- Examples: congress abstract, publication, clinical trial update (schema in `docs/2_SRS_Software_Requirements_Specification.md` §2 terms; `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` schema)
- Pattern: normalized haemophilia signal: disease · patient/inhibitor type · company · asset · asset type · signal type · priority · impacted function

**Development (evidence story):**
- Purpose: Linked chain of signals forming one storyline with a lifecycle state
- Examples: "mim8 competitive landscape shift" demo scenario (`README.md` "Demo Scenario")
- Pattern: event sourcing (`event_type/event_date/development_id/source_id`)

**F-I-S Label:**
- Purpose: Honest epistemic status of every AI claim
- Pattern: FACT requires multi-source corroboration; speculation never presented as fact (`docs/9_RISK_AND_GUARDRAILS.md` R1/R2)

**WATCH Rule (Watch-for-Next):**
- Purpose: Stakeholder-defined monitoring expectation (`source_event → expected next event → window → responsible function → status`)
- Statuses: `watching · new_evidence_detected · no_new_evidence · watch_expired · human_review_required` (`docs/METARADAR_MASTER_PLAN_v3.0.md` §3)

## Entry Points

**Backend API:**
- Location: `backend/app/main.py` (planned, per `README.md` "Project Structure")
- Triggers: dashboard HTTP requests, Ask Athena
- Responsibilities: FastAPI app wiring, routers

**Scheduler:**
- APScheduler + Celery (planned `workers/`)
- Triggers: every 2 hours
- Responsibilities: periodic fetch of live sources

**Frontend app:**
- Location: `frontend/app/` (planned)
- Responsibilities: route to dashboard pages (Four-Question, signals, watchlists, calibration)

## Architectural Constraints

- **Threading:** Async-first (`httpx` async, FastAPI ASGI); local model inference runs CPU-bound (Gemma Q4 ~2.6GB, ~4.5–7.5GB RAM) (`docs/2_SRS_Software_Requirements_Specification.md`)
- **Global state:** LangGraph shared workflow state; no module-level singletons prescribed
- **Fallback chain:** Redis cache → bronze DB → 500-signal synthetic dataset; 100% graceful degradation, zero dashboard crashes (`docs/METARADAR_MASTER_PLAN_v3.0.md` §10)
- **No autonomous decisions:** AI suggests → human reviews → human decides; controlled action vocabulary (`docs/9_RISK_AND_GUARDRAILS.md` §1.2)
- **Data boundaries:** public + synthetic only; PII/PHI scrubbed before persistence; `.env` secrets never committed (`docs/9_RISK_AND_GUARDRAILS.md` §1.1)

## Anti-Patterns

### Broadcast-Style Routing

**What happens:** Seed routing matrix routes signals to too many or too few functions (`docs/9_RISK_AND_GUARDRAILS.md` R16).
**Why it's wrong:** Violates the "not every signal needs to go to everyone" principle; inbox noise returns.
**Do this instead:** Relevance-based routing with `primary_function` + `secondary_functions[]` + per-function scores + `routing_reason`; adjustable via calibration (`docs/METARADAR_MASTER_PLAN_v3.0.md` §2).

### Presenting Absence as Fact

**What happens:** Missing-signal silence interpreted as "nothing is happening" (`docs/9_RISK_AND_GUARDRAILS.md` R8/R18).
**Why it's wrong:** Absence is ambiguous (delayed disclosure, coverage gaps, changed strategy).
**Do this instead:** WATCH items with guarded wording — "Watch for…", "Expected/possible next evidence", "Not observed yet" — never a claim (`README.md` "Missing-Signal Detection").

### Summarizer Model Drift

**What happens:** Historical docs cited `sshleifer/distilbart-cnn-12-6` for summarization while canonical spec says `facebook/bart-large-cnn` (`docs/8_CORRECTED_UNIFIED_PLAN.md` C6).
**Why it's wrong:** Ambiguity breaks the model-agnostic config contract.
**Do this instead:** Canonical `SUMMARIZER_MODEL=facebook/bart-large-cnn` via env var; master plan is authoritative (`docs/8_CORRECTED_UNIFIED_PLAN.md` resolution rule).

## Error Handling

**Strategy:** `tenacity` exponential backoff (2s/4s/8s) on external APIs; fallback cascade (Redis → bronze → synthetic) on failure; per-source health status surfaced in UI (`docs/9_RISK_AND_GUARDRAILS.md` R11).

**Patterns:**
- 100% ingestion resilience — external API failure never crashes dashboard
- Verbatim replay from `raw_signals_bronze` for re-processing
- Evidence-sufficiency gate blocks generation when retrieval confidence is low (R1)

## Cross-Cutting Concerns

**Logging:** application logs; WORM `audit_log` for calibration/ontology changes; source-status footers (`docs/9_RISK_AND_GUARDRAILS.md`)
**Validation:** `node_validate` quality filters; B.Pharm-labelled evaluation dataset (≥85% classification); confusion matrix review (`docs/METARADAR_MASTER_PLAN_v3.0.md` §10)
**Authentication:** lightweight API token (hackathon scope) (`docs/3_SOFTWARE_DESIGN_DOCUMENT.md`)
**Traceability:** 100% of high-priority AI insights carry source name, URL, publication date, source type, excerpt, evidence level, confidence, timestamp, AI label (`docs/METARADAR_MASTER_PLAN_v3.0.md` §10)

---

*Architecture analysis: 2026-08-13*
