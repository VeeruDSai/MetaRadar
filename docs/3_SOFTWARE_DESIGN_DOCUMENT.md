# MetaRadar: Software Design Document (SDD)

**Project:** MetaRadar - Real-Time Haemophilia Competitive Intelligence Radar  
**Version:** 2.4  
**Date:** August 2026  
**Team:** Aura Pharmers — MSRIT (2 CSE + 3 B.Pharm) · **Team Lead: Sanjana Rathore B.**  
**Scope Note:** Revised for Novo Nordisk GBS Hackathon 2026 kickoff (Aug 12, 2026) — added **Stakeholder Calibration Loop (HITL)**, Four-Question Framework wiring, and haemophilia-specific design updates (v2.0), then extended with the **Five Advanced Analyses** (v2.1): Confluence Detection, Signal Lifecycle Tracking, Red-Team Contradiction Analysis, Missing-Signal Detection, and Stakeholder Learning Loop. **v2.2 (Aug 13, 2026):** integrated the B.Pharm domain research (Master Plan v4.0 §12) — canonical domain-classification fields + `DomainClassifier` service, nullable clinical-evidence fields, evidence-maturity ladder, access as a separate intelligence event (8 access subtypes + `access_info` JSONB), and the extended Red-Team evidence-check suite A–S. **v2.3 (Aug 13, 2026):** provider-agnostic reasoning layer (Master Plan v5.0 §13) — `LLMProvider` interface (`LocalGemmaProvider` / `XAIProvider` / `BartDegradedProvider`), `LLM_PROVIDER=local|xai|auto`, two output schemas (FULL INTELLIGENCE vs DEGRADED FACTUAL SUMMARY), external-LLM privacy gate for hosted Grok, Grok JSON-Schema structured-output validation, per-output model metadata. Architecture, data sources, and embedding model are unchanged (Docker Compose footprint unchanged through v2.3 — v2.4 removes Celery → 4 services); the six primary functions remain Medical Affairs · Regulatory · Safety/PV · Market Access · Medical Communications · Leadership. **v2.4 (Aug 13, 2026):** pre-implementation architecture hardening (Master Plan v5.1 §14) — Gemma deployment target corrected to **local GPU (NVIDIA RTX 3050, 4 GB VRAM, Q4/int4)** with `LLM_DEVICE`/`LLM_DTYPE`/`MAX_CONTEXT_TOKENS`/`MAX_OUTPUT_TOKENS`; scheduling consolidated to **ONE in-process APScheduler** (Celery removed — 4-service Docker Compose, `/models` volume, healthchecks); canonical entity layer added to the schema (`sources · companies · assets · trials · developments · events` + evidence relationships); scoring/calibration versioning fields (`scoring_model_version`, `scoring_config_version`, `score_breakdown`, baseline-vs-calibrated routing, `calibration_version`); formal LangGraph state contract (reducers, initial state, `node_calibrate → END`); health endpoints `/api/v1/health/ready|models|connectors`; deterministic dedup + source-independence before Confluence; Alembic migrations and versioned Redis caching.

> [!IMPORTANT]
> **HISTORICAL REFERENCE DOCUMENT**  
> *Note: This document is a secondary/historical reference and must not override the Master Plan. The sole canonical and authoritative specification for MetaRadar is [METARADAR_MASTER_PLAN_v5.0.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/METARADAR_MASTER_PLAN_v5.0.md).*

---

## **1. ARCHITECTURE OVERVIEW**

### 1.0 Conceptual Architecture (Non-Technical / B.Pharm Presentation View)

```
META RADAR
│
├── UNDERSTAND
│   ├── Entity extraction
│   └── Haemophilia ontology
│
├── CONNECT
│   ├── Confluence
│   └── Lifecycle
│
├── CHALLENGE
│   └── Red-Team contradiction analysis
│
├── DETECT
│   └── Missing signals
│
├── LEARN
│   └── Stakeholder calibration
│
└── FOUR QUESTIONS
    └── Role-specific intelligence
```

### 1.1 Technical System Architecture (Implementation & Engineering View)

```
┌──────────────────────────────────────────────────────────────────┐
│                         END USERS                                 │
│  Medical Affairs | Regulatory | Safety/PV | Market Access |       │
│  Medical Communications | Leadership                              │
│  (+ extended: Commercial · R&D · Simulated Personas)             │
└────────────────────────┬─────────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
   ┌────▼────────────────┐      ┌────────▼──────────────┐
   │   FRONTEND LAYER    │      │   API GATEWAY/PROXY   │
   │  (Next.js 15)       │      │   (Vercel Edge)       │
   │  ├─ Four-Question   │      └────────┬──────────────┘
   │  │  Dashboard (Q1-Q4)│              │
   │  ├─ Confluence view │       ┌───────▼───────────┐
   │  ├─ Ask Athena      │       │  BACKEND LAYER    │
   │  ├─ Calibration UI  │       │  (FastAPI)        │
   │  └─ Admin UI        │       │  ├─ /signals      │
   └────┬────────────────┘       │  ├─ /trends      │
        │                        │  ├─ /confluence  │
        │      ┌─────────────────┤  ├─ /query       │
        │      │                 │  ├─ /briefs      │
        │      │                 │  ├─ /feedback    │ ← NEW HITL
        │      │                 │  ├─ /feedback/summary │ ← NEW
        │      │                 │  ├─ /calibrate   │ ← NEW HITL
        │      │                 │  └─ /health      │
        │      │                 └────┬──┬──────────┘
        │      │                      │  │
   ┌────▼──────▼────┐      ┌──────────┘  └───────────────┐
   │   CACHE LAYER  │      │  INTELLIGENCE LAYER         │
   │  (Redis)       │      │  (LangGraph orchestration)  │
   │ ├─ Hot signals │      │  ├─ Ingestion agent         │
   │ ├─ Session     │      │  ├─ Validation agent        │
   │ └─ Rate limits │      │  ├─ NLP agent (spaCy+BART)  │
   └────┬───────────┘      │  ├─ Confluence agent        │
        │                  │  ├─ Lifecycle agent  ← NEW  │
        │      ┌───────────┤  ├─ Red-Team agent  ← NEW   │
        │      │           │  ├─ Missing-Signal agent ←NEW│
        │      │           │  ├─ Synthesis agent         │
        │      │           │  ├─ Brief agent             │
        │      │           │  └─ Stakeholder Calibration │
        │      │           │     agent (HITL)            │
        │      │           └────────────┬───────────────┘
   ┌────▼──────▼────────────────────────────────────┐
   │         DATA LAYER                              │
   │  ┌──────────────────────────────────────────┐  │
   │  │ PostgreSQL 16 + pgvector (ONE database)  │  │
   │  │ ├─ signals table                         │  │
   │  │ ├─ entities table                        │  │
   │  │ ├─ trending_scores table                 │  │
   │  │ ├─ role_relevance table                  │  │
   │  │ ├─ signal_embeddings (pgvector 384-dim)  │  │
   │  │ ├─ confluence_events table               │  │
   │  │ ├─ lifecycle_chains table        ← NEW   │  │
   │  │ ├─ lifecycle_events table        ← NEW   │  │
   │  │ ├─ contradictions table          ← NEW   │  │
   │  │ ├─ missing_signal_rules table    ← NEW   │  │
   │  │ ├─ missing_signal_alerts table   ← NEW   │  │
   │  │ ├─ briefs table                          │  │
   │  │ ├─ stakeholder_feedback table            │  │
   │  │ ├─ scoring_weights table                 │  │
   │  │ ├─ calibration_history table             │  │
   │  │ └─ [Indexes + Materialized Views]        │  │
   │  └──────────────────────────────────────────┘  │
   │  └─ Hybrid search: pgvector (semantic) +       │
   │     pg_trgm/FTS (keyword) in the SAME DB       │
   └─────────────────────────────────────────────────┘
        │
   ┌────▼──────────────────┐
   │  DATA INGESTION       │
   │  (APScheduler, single)│
   │  ├─ fetch_newsapi()         │
   │  ├─ fetch_pubmed()          │
   │  ├─ fetch_clinicaltrials()  │
   │  ├─ fetch_reddit()          │ (adapter)
   │  ├─ fetch_fda()             │ (adapter)
   │  └─ process_signals()       │
   └────┬──────────────────┘
        │
   ┌────▼──────────────────┐
   │  EXTERNAL APIs        │
   │  ├─ NewsAPI            (LIVE)
   │  ├─ NCBI PubMed (E-utilities) (LIVE)
   │  ├─ ClinicalTrials.gov (LIVE)
   │  ├─ Reddit PRAW        (ADAPTER-READY)
   │  ├─ FDA                (ADAPTER-READY)
   │  └─ Congress archives  (ADAPTER-READY)
   └───────────────────────┘
```

### 1.2 Technology Stack Summary

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | Next.js 15 + TypeScript | Server components, streaming, code splitting |
| **State Mgmt** | TanStack Query v5 | Server-state mgmt, auto caching/sync |
| **Styling** | TailwindCSS 4 + shadcn/ui | Fast development, pre-built components |
| **Backend API** | FastAPI + Python 3.11 | Async-first, auto OpenAPI docs, ML-friendly |
| **Agent Orchestration** | LangGraph | Stateful multi-agent pipeline (ingest → validate → NLP → confluence → lifecycle → red-team → missing-signal → synthesize → brief → **stakeholder calibration**) |
| **Scheduler (single)** | APScheduler (in-process, inside FastAPI) + Redis | 2-hour fetch · nightly digest · on-demand recalibration — Celery NOT used (Master Plan §14.9); heavy LangGraph runs offloaded via asyncio/thread-pool |
| **Primary DB** | PostgreSQL 16 + pgvector | ACID, JSONB, vector search in one DB (replaces Weaviate) |
| **Cache** | Redis 7 | Sub-millisecond access, rate limiting |
| **NLP/NER** | spaCy 3.7 (`en_core_sci_md`) + medspacy | Entity extraction, pharma-grade NER; medspacy extends coverage |
| **Reasoning Layer (provider-agnostic, Master Plan §13)** | `google/gemma-3-4b-it` (default local) via `LOCAL_LLM_MODEL`; optional hosted Grok via `XAI_API_KEY`/`XAI_MODEL` (`LLM_PROVIDER=local|xai|auto`) | Gemma 3 4B Instruct — narrative synthesis, Four-Question reasoning, suggested actions, Ask Athena; `text-generation` task; **Q4/int4 on the local GPU (NVIDIA RTX 3050, 4 GB VRAM)** via `LLM_DEVICE`/`LLM_DTYPE`/`MAX_CONTEXT_TOKENS`/`MAX_OUTPUT_TOKENS` (VRAM not guaranteed — provider chain falls back on init/inference failure, §14.1). Optional xAI Grok (JSON-Schema structured outputs, privacy-gated). Provider chain: Gemma → Grok → BART degraded factual mode |
| **Batch Summarizer** | `facebook/bart-large-cnn` via `SUMMARIZER_MODEL` env var | Fast CPU seq2seq 1-sentence summaries (< 60s/100 signals) + demo-safety fallback |
| **Classification** | `facebook/bart-large-mnli` (zero-shot) | Signal type classification AND Red-Team contradiction entailment (one local model, two jobs) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim local embeddings, 80MB |
| **HTTP Resilience** | `tenacity` + `httpx.AsyncClient` | Exponential backoff retry + async HTTP (research report recommendation) |
| **Containerization** | Docker + Docker Compose | Reproducible environments |
| **Deployment** | Vercel (frontend) + Render (backend) | Serverless, auto-scaling, free tier |
| **Logging** | Loguru + /metrics endpoint | Structured logging, performance telemetry |
| **Compliance** | `audit_log` (WORM) + dedicated PII/PHI detection & redaction pipeline | Append-only audit trail inspired by electronic-record traceability principles (design analogy — no 21 CFR Part 11 / GxP compliance claim) |
| **Calibration** | `StakeholderCalibrationService` (HITL) | Recalibrates function-scoring weights from persona feedback (`stakeholder_feedback` → `scoring_weights`) |

**Canonical Model Roles (Master Plan §13.8):**

| Role | Default | Alternative |
|---|---|---|
| Reasoning / Four Questions / Athena | Gemma 3 4B local (**GPU** — RTX 3050 4 GB VRAM, Q4/int4) | Grok API |
| Degraded factual summary | BART-large-CNN | — |
| Batch summarization | BART-large-CNN | — |
| NLI | BART-MNLI | — |
| NER | spaCy | — |
| Embeddings | MiniLM | — |

BART is NEVER listed as a reasoning model.


---

## **2. DETAILED COMPONENT DESIGN**

### 2.1 Frontend Architecture (Next.js)

**Project Structure:**
```
frontend/
├── app/                          # Next.js app directory
│   ├── layout.tsx               # Root layout
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── logout/page.tsx
│   ├── (dashboard)/
│   │   ├── layout.tsx           # Dashboard layout with sidebar
│   │   ├── page.tsx             # Home/overview
│   │   └── [role]/              # Dynamic role pages
│   │       └── page.tsx
│   ├── api/
│   │   └── auth/[...nextauth]/route.ts  # Auth API routes
│   └── sitemap.ts
├── components/
│   ├── Dashboard/
│   │   ├── SignalFeed.tsx       # Lazy-loaded signal list
│   │   ├── TrendChart.tsx       # Recharts trend visualization
│   │   ├── SignalCard.tsx       # Individual signal display
│   │   └── FilterBar.tsx        # Search/date/entity filters
│   ├── Common/
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   └─ LoadingSkeletons.tsx
│   └── UI/                       # shadcn/ui components
│       ├── Button.tsx
│       ├── Input.tsx
│       └── Card.tsx
├── hooks/
│   ├── useSignals.ts            # TanStack Query hook
│   ├── usePrefetch.ts           # Prefetch next page
│   └── useAuth.ts               # Auth context
├── lib/
│   ├── api-client.ts            # Axios instance with interceptors
│   ├── types.ts                 # TypeScript interfaces
│   └── utils.ts                 # Helpers
├── styles/
│   └── globals.css              # TailwindCSS config
└── next.config.js               # Image optimization, compression
```

**Key Features:**
- **Server Components:** Layout/data fetching on server (faster, secure)
- **Streaming:** Incremental rendering of heavy components
- **Code Splitting:** Automatic via dynamic imports
- **Image Optimization:** Next.js image with srcset

**Performance Optimizations:**
```typescript
// Signal feed with infinite scroll + virtual rendering
import dynamic from 'next/dynamic';
import { Suspense } from 'react';

const SignalFeed = dynamic(() => import('@/components/Dashboard/SignalFeed'), {
  loading: () => <SkeletonLoader />,
  ssr: false,  // Don't render on server (heavy component)
});

// Prefetch next role's data while current role displayed
useEffect(() => {
  queryClient.prefetchInfiniteQuery({
    queryKey: ['signals', nextRole],
    queryFn: ({ pageParam = 0 }) =>
      fetch(`/api/signals?role=${nextRole}&offset=${pageParam}`),
  });
}, [currentRole]);
```

### 2.2 Backend API Architecture (FastAPI)

**Project Structure:**
```
backend/
├── main.py                       # Entry point, app setup
├── config.py                     # Environment variables
├── requirements.txt              # Dependencies
├── Dockerfile
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── signals.py       # GET /api/v1/signals
│   │   │   ├── trends.py        # GET /api/v1/trends
│   │   │   ├── confluence.py    # GET /api/v1/confluence
│   │   │   ├── lifecycles.py    # GET /api/v1/lifecycles (lifecycle tracking)
│   │   │   ├── contradictions.py# GET /api/v1/contradictions (red-team)
│   │   │   ├── missing_signals.py # GET /api/v1/missing-signals
│   │   │   ├── query.py         # POST /api/v1/query (Ask Athena)
│   │   │   ├── briefs.py        # GET /api/v1/briefs (narrative)
│   │   │   ├── search.py        # POST /api/v1/search
│   │   │   ├── entities.py      # GET /api/v1/entities
│   │   │   ├── feedback.py      # POST /api/v1/feedback + GET /api/v1/feedback/summary (HITL)
│   │   │   ├── calibrate.py     # POST /api/v1/calibrate (Stakeholder Calibration)
│   │   │   ├── digest.py        # GET /api/v1/digest (weekly digest, function filter)
│   │   │   ├── watchlist.py     # GET/POST/DELETE /api/v1/watchlist (entity focus)
│   │   │   └── health.py        # GET /api/v1/health · /health/ready · /health/models · /health/connectors
│   │   └── routers.py           # API router aggregation
│   └── auth.py                   # JWT token validation
├── agents/
│   ├── ingestion_agent.py       # LangGraph node: parallel fetch + dedup
│   ├── validation_agent.py      # LangGraph node: quality scoring
│   ├── nlp_agent.py             # LangGraph node: spaCy NER + BART
│   ├── confluence_agent.py      # LangGraph node: cross-source convergence (Analysis 1)
│   ├── lifecycle_agent.py       # LangGraph node: lifecycle state machine + event chains (Analysis 2)
│   ├── red_team_agent.py        # LangGraph node: NLI contradiction scan + devil's-advocate review (Analysis 3)
│   ├── missing_signal_agent.py  # LangGraph node: expected-event detector (Analysis 4)
│   ├── synthesis_agent.py       # LangGraph node: narrative briefs
│   ├── brief_agent.py           # LangGraph node: role formatting
│   └── calibration_agent.py     # LangGraph node: stakeholder feedback → weight recalibration (Analysis 5, HITL)
├── graph/
│   └── intelligence_graph.py    # StateGraph wiring of agents
├── services/
│   ├── signal_processor.py      # Main orchestration
│   ├── nlp_service.py           # Entity extraction, summarization
│   ├── scoring_service.py       # Relevance scoring
│   ├── confluence_engine.py     # Signal Confluence Engine (Analysis 1)
│   ├── lifecycle_tracker.py     # Lifecycle state machine + timelines (Analysis 2)
│   ├── red_team_engine.py       # NLI contradiction detection + red-team review (Analysis 3)
│   ├── missing_signal_detector.py # Expected-event state machine + confidence-by-silence (Analysis 4)
│   ├── watch_service.py         # Watch-for-Next: stakeholder watch rules → watch_items (FR-2.3C.1A)
│   ├── routing_service.py       # relevance-based routing: primary/secondary functions + routing_reason (FR-2.5.1)
│   ├── ontology_service.py      # Pharma ontology enrichment/validation
│   ├── narrative_synthesizer.py # Executive brief generation
│   ├── temporal_patterns.py     # Competitive timeline matching
│   ├── traceability.py          # Evidence chain / audit trail
│   ├── query_engine.py          # RAG "Ask Athena" over pgvector
│   ├── calibration_service.py   # StakeholderCalibrationService.recalibrate(role) (Analysis 5, HITL)
│   ├── evidence_service.py      # evidence-sufficiency gate + F-I-S labelling (FR-2.2.6/2.2.7)
│   ├── digest_service.py        # weekly digest generation (reuses brief agents)
│   ├── api_fetcher.py           # Multi-source data fetch
│   ├── cache_service.py         # Redis operations
│   └── db_service.py            # PostgreSQL operations
├── models/
│   ├── schemas.py               # Pydantic models (request/response)
│   ├── database.py              # SQLAlchemy ORM models
│   └── types.py                 # Custom types
├── workers/
│   ├── jobs.py                  # APScheduler job definitions (single scheduler, Master Plan §14.9)
│   ├── signal_ingestion.py      # APScheduler job: fetch from connectors
│   ├── signal_processing.py     # APScheduler job: run LangGraph pipeline (offloaded via asyncio/thread-pool)
│   ├── confluence_detection.py  # APScheduler job: confluence scan
│   ├── lifecycle_detection.py   # APScheduler job: lifecycle advance
│   ├── red_team_scan.py         # APScheduler job: NLI contradiction scan
│   ├── missing_signal_scan.py   # APScheduler job: expected-event scan
│   ├── trends_aggregation.py    # APScheduler job: aggregates
│   ├── calibration_job.py       # APScheduler job: async weight recalibration
│   └── digest_job.py            # APScheduler job: nightly digest generation
├── entities/
│   └── pharma_ontology.py       # B.Pharm-authored ontology (JSON)
├── utils/
│   ├── logger.py                # Structured logging (Loguru)
│   ├── rate_limiter.py          # Rate limit enforcement
│   ├── validators.py            # Input validation
│   └── helpers.py               # General utilities
└── tests/
    ├── test_signal_processor.py
    ├── test_nlp_service.py
    ├── test_confluence_engine.py
    ├── test_lifecycle_tracker.py
    ├── test_red_team_engine.py
    ├── test_missing_signal_detector.py
    ├── test_ontology_service.py
    ├── test_stakeholder_calibration.py  # HITL weight recalibration tests
    ├── test_fis_evidence.py             # F-I-S classification + evidence-sufficiency gate
    ├── test_api_endpoints.py
    └── test_integration.py
```

**Key Design Patterns:**

```python
# 1. Async-first architecture
@app.get("/api/v1/signals")
async def get_signals(
    role: str,
    limit: int = 20,
    offset: int = 0,
    date_range: str = "7d"
) -> SignalListResponse:
    """Fetch signals with parallel async operations"""
    
    # Try cache first (sub-millisecond)
    cached = await cache_service.get(f"signals:{role}:{offset}")
    if cached:
        return SignalListResponse.parse_obj(cached)
    
    # Cache miss: fetch from DB with parallel queries
    signals, total = await asyncio.gather(
        db_service.get_signals(role, limit, offset),
        db_service.count_signals(role)
    )
    
    response = SignalListResponse(
        signals=signals,
        total=total,
        offset=offset,
        limit=limit
    )
    
    # Cache result for 2 hours
    await cache_service.set(
        f"signals:{role}:{offset}",
        response.dict(),
        ttl=7200
    )
    
    return response

# 2. Service-oriented architecture
class SignalProcessor:
    """Orchestrates entire signal processing pipeline"""
    
    def __init__(self, nlp_svc, scoring_svc, db_svc, cache_svc):
        self.nlp = nlp_svc
        self.scoring = scoring_svc
        self.db = db_svc
        self.cache = cache_svc
    
    async def process_signals_batch(self, raw_signals: list[dict]):
        """1. Extract → 2. Score → 3. Store → 4. Cache"""
        
        # Step 1: Validate + deduplicate
        validated = await self._validate_batch(raw_signals)
        
        # Step 2: Extract entities (batch NLP)
        extracted = await self.nlp.extract_batch(validated)
        
        # Step 3: Score relevance
        scored = await self.scoring.score_batch(extracted)
        
        # Step 4: Persist
        stored = await self.db.insert_signals(scored)
        
        # Step 5: Update vector embeddings
        await self._embed_batch(stored)
        
        # Step 6: Invalidate cache
        await self.cache.invalidate("signals:*")
        
        return stored

# 3. Dependency injection (FastAPI built-in)
def get_signal_processor() -> SignalProcessor:
    return SignalProcessor(
        nlp_svc=NLPService(),
        scoring_svc=ScoringService(),
        db_svc=DBService(),
        cache_svc=CacheService()
    )

@app.get("/api/v1/signals")
async def get_signals(
    processor: SignalProcessor = Depends(get_signal_processor),
    role: str = "medical_affairs"
):
    signals = await processor.fetch_by_role(role)
    return signals
```

### 2.3 Intelligence Layer: LangGraph Multi-Agent Orchestration

Replaces the monolithic pipeline with specialized agents coordinated by LangGraph. Each agent is one node; state flows automatically between agents.

```python
# graph/intelligence_graph.py
from langgraph.graph import StateGraph

# LangGraph state contract (Master Plan §14.6 — canonical field names govern): explicit
# initial state is required; accumulating fields use typed append/merge reducers so parallel
# connector/analysis nodes never overwrite each other; scalar fields use replacement
# semantics; each node declares read/write fields; explicit termination node_calibrate → END.
class IntelligenceState(TypedDict):
    raw_signals: list[dict]
    validated_signals: list[dict]
    extracted_entities: list[dict]
    ontology_entities: list[dict]
    developments: list[dict]
    scored_signals: list[dict]
    confluent_stories: list[dict]
    lifecycle_events: list[dict]        # Analysis 2 (lifecycle state machine)
    redteam_flags: list[dict]           # Analysis 3 (red-team NLI)
    missing_signals: list[dict]         # Analysis 4 (expected-event detector)
    role_briefs: dict[str, list]
    calibration_feedback: list[dict]    # from stakeholder_feedback (Analysis 5, HITL)
    model_metadata: list[dict]
    errors: list[dict]

graph = StateGraph(IntelligenceState)
graph.add_node("ingest", ingestion_agent)        # 6 APIs parallel + dedup
graph.add_node("validate", validation_agent)     # quality score > 0.5
graph.add_node("nlp", nlp_agent)                 # spaCy NER + BART (batch)
graph.add_node("confluence", confluence_agent)   # cross-source convergence (Analysis 1)
                                                 # + development-link decision:
                                                 #   congress/publication → existing development
                                                 #   (new_evidence) vs new_development
graph.add_node("lifecycle", lifecycle_agent)     # lifecycle state machine (Analysis 2); records
                                                 # event_type · event_date · development_id · source_id
graph.add_node("red_team", red_team_agent)       # NLI contradiction scan (Analysis 3)
graph.add_node("missing_signal", missing_signal_agent)  # expected-event detector (Analysis 4)
                                                 # + stakeholder watch rules → watch_items
graph.add_node("synthesize", synthesis_agent)    # narrative briefs
graph.add_node("brief", brief_agent)             # role-specific formatting (routing_reason)
graph.add_node("calibrate", calibration_agent)   # HITL: feedback → weight update (Analysis 5);
                                                 # scope: priority, routing, action, watch rules, relevance

graph.add_edge("ingest", "validate")
graph.add_edge("validate", "nlp")
graph.add_edge("nlp", "confluence")
graph.add_edge("confluence", "lifecycle")
graph.add_edge("lifecycle", "red_team")
graph.add_edge("red_team", "missing_signal")
graph.add_edge("missing_signal", "synthesize")
graph.add_edge("synthesize", "brief")
graph.add_edge("brief", "calibrate")             # calibration reads briefs + feedback
graph.set_entry_point("ingest")
graph.set_finish_point("calibrate")               # explicit termination: node_calibrate → END
runner = graph.compile()

# Single scheduler (Master Plan §14.9): in-process APScheduler invokes the runner every 2h;
# CPU/GPU-bound runs are offloaded from the event loop via asyncio/thread-pool execution.
result = await asyncio.to_thread(runner.invoke, {})
```

**Why LangGraph:** Built-in state management across agents (no global variables), the synthesis agent can read NLP state directly, and the graph can later branch per role without re-architecture.

### 2.4 Confluence Engine, Ontology & Traceability Services

**Signal Confluence Engine** (`services/confluence_engine.py`) — the core differentiator. When ≥ 2 independent signal types fire on the same entity within 48h, importance multiplies into one strategic alert:

```python
class SignalConfluenceEngine:
    CONFLUENCE_MATRIX = {
        frozenset(["regulatory", "clinical", "social"]): "CRITICAL",
        frozenset(["clinical", "competitive"]):          "HIGH",
        frozenset(["regulatory", "competitive"]):        "HIGH",
        frozenset(["social", "clinical"]):               "MEDIUM",
        frozenset(["competitive"]):                      "LOW",
    }

    def detect_confluence(self, signals, entity, time_window_hours=48) -> dict:
        entity_signals = [s for s in signals
                          if entity in s.get("entities", {}).get("all", [])
                          and s["timestamp"] > cutoff]
        if len(entity_signals) < 2:
            return None
        types = {s["signal_type"] for s in entity_signals}
        for pattern, level in self.CONFLUENCE_MATRIX.items():
            if pattern.issubset(types):
                return {"entity": entity, "alert_level": level,
                        "signal_count": len(entity_signals),
                        "signal_types_present": list(types),
                        "story_summary": await self._synthesize_story(entity_signals)}
        return None
```

**Pharma Ontology Enrichment** (`services/ontology_service.py`) — B.Pharm-authored JSON that enriches extracted entities and validates drug/company accuracy (see `entities/pharma_ontology.py`). Resolves "Hemlibra" → emicizumab → bispecific antibody → Roche → Haemophilia A competitor, flags competitor drugs at zero API cost, and provides the validation layer that answers "how do you ensure pharma accuracy?".

**Stakeholder Calibration Loop** (`services/calibration_service.py` + `agents/calibration_agent.py`) — the HITL learning loop (new in v2.0). Simulated (and real) Novo Nordisk stakeholder personas rate routing accuracy per signal (`POST /api/v1/feedback`). `StakeholderCalibrationService.recalibrate(role)` recomputes the role × signal-type weights (`scoring_weights` table) and persists a `calibration_history` row:

```python
# services/calibration_service.py
class StakeholderCalibrationService:
    def __init__(self, db):
        self.db = db

    async def submit_feedback(self, signal_id, role, rating, reason, user_id) -> UUID:
        # Append-only: stored in stakeholder_feedback (WORM audit)
        return await self.db.insert_feedback(signal_id, role, rating, reason, user_id)

    async def recalibrate(self, role: str) -> dict:
        """Recompute role scoring weights from feedback (EMA-like damped update)."""
        feedback = await self.db.feedback_for_role(role)
        if len(feedback) < MIN_FEEDBACK_PER_ROLE:
            return {"status": "skipped", "reason": "insufficient_feedback"}
        new_weights = await self._weighted_update(feedback)      # per signal_type
        old = await self.db.get_weights(role)
        await self.db.update_weights(role, new_weights)
        await self.db.insert_calibration_history(role, old, new_weights)
        return {"status": "recalibrated", "role": role, "old": old, "new": new_weights}

    async def summary(self) -> dict:
        """Per-role avg rating, n feedback, last calibration timestamp."""
        return await self.db.feedback_summary()
```

Calibration affects scoring for the *next* ingestion cycle: `scoring_service` loads `scoring_weights` fresh each batch, so a recalibration is visible in the next Q3 role-routing confidence scores. Every recalibration is written to `audit_log` (WORM).

**Signal Lifecycle Tracker** (`services/lifecycle_tracker.py` + `agents/lifecycle_agent.py`) — Analysis 2 of the Five. Maintains a chronological state machine per tracked development (entity + modality + indication): `announced → in_trial → interim_result → final_result → congress_publication → regulatory_development → approved → post_market | discontinued`. Each signal is assigned to a lifecycle chain; the agent advances the current state and computes the expected next event:

```python
# services/lifecycle_tracker.py
class SignalLifecycleTracker:
    LIFECYCLE_STATES = [
        "announced", "in_trial", "interim_result", "final_result",
        "congress_publication", "regulatory_development", "approved",
        "post_market", "discontinued",
    ]

    async def advance(self, signal, entity) -> dict:
        chain = await self.get_or_create_chain(entity)
        chain.events.append(signal)
        chain.current_state = self._infer_state(signal)          # rule-based, B.Pharm-validated
        chain.expected_next = self._expected_next(chain)
        await self.db.insert_lifecycle_event(chain, signal)
        return {"chain": chain, "state": chain.current_state,
                "expected_next": chain.expected_next}

    def timeline(self, entity) -> list[dict]:
        """Chronological, temporally-linked events for the entity."""
        return sorted(self.chains[entity].events, key=lambda e: e["published_at"])
```

**Red-Team Contradiction Engine** (`services/red_team_engine.py` + `agents/red_team_agent.py`) — Analysis 3 of the Five. Runs pairwise NLI entailment over signals about the same entity in a rolling window (default 90 days) using the *same* local `facebook/bart-large-mnli` model already used for signal classification (zero extra model download). Flags `contradiction` labels above 0.6 and attaches a devil's-advocate note:

```python
# services/red_team_engine.py
_nli = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

async def detect_contradictions(signals, entity, window_days=90) -> list[dict]:
    entity_signals = [s for s in signals if entity in s.get("entities", {}).get("all", [])]
    out = []
    for a, b in combinations(entity_signals, 2):
        if (b["published_at"] - a["published_at"]).days > window_days:
            continue
        r = _nli(a["summary"], candidate_labels=["entailment", "contradiction", "neutral"])
        if r["labels"][0] == "contradiction" and r["scores"][0] > 0.6:
            out.append({
                "entity": entity,
                "claim_a": {"text": a["summary"], "source": a["source"], "url": a["url"], "date": a["published_at"]},
                "claim_b": {"text": b["summary"], "source": b["source"], "url": b["url"], "date": b["published_at"]},
                "contradiction_score": r["scores"][0],
                "red_team_note": "Devil's-advocate: newest evidence may overturn earlier claim — human review required",
            })
    return out
```

**Domain Classification Service** (`services/domain_classifier.py` + `agents/nlp_extract_agent.py` v4.0) — B.Pharm research-driven extraction layer that populates the canonical haemophilia domain fields on every normalized signal (see SRS FR-2.2.5A/5B/5C):

```python
# services/domain_classifier.py — v4.0 (B.Pharm research integration)
class DomainClassifier:
    # Ishaaq rules: disease/factor/inhibitor/modality hard classifiers
    DISEASE_TERMS = {
        "haemophilia_a": ["factor viii", "fviii", "f8", "haemophilia a", "hemophilia a"],
        "haemophilia_b": ["factor ix", "fix", "f9", "haemophilia b", "hemophilia b"],
    }
    MODALITY_RULES = [  # factor protein → FACTOR; antibody/TFPI/siRNA → NON_FACTOR; AAV/lentiviral/editing → GENE_THERAPY
        (["aav", "transgene", "gene transfer", "gene editing", "lentiviral"], "aav_gene_therapy"),
        (["sirna", "rnai", "antithrombin"], "sirna"),
        (["bispecific", "fviiia mimetic", "fviii mimetic"], "bispecific_antibody"),
        (["anti-tfpi", "tfpi"], "non_factor"),
        (["extended half-life", "ehl"], "extended_half_life_factor"),
        (["factor viii", "factor ix", "factor replacement"], "factor_replacement"),
    ]

    def classify(self, text: str, entities: dict) -> dict:
        """Return domain fields; NEVER guess — unknown when evidence insufficient."""
        disease = self._match_terms(text, self.DISEASE_TERMS) or \
                  self._resolve_via_entity(entities)            # product/trial-ID/context resolution
        inhibitor = "unknown"
        if re.search(r"(fviii|fix|factor) inhibitor|neutrali[sz]ing antibod|inhibitor-positive", text):
            inhibitor = "with_inhibitor"
        elif re.search(r"without inhibitors|no inhibitors|inhibitor-negative|inhibitor-free", text):
            inhibitor = "without_inhibitor"
        return {
            "disease": disease or "unknown",          # bare "haemophilia" → unknown
            "factor": "fviii" if disease == "haemophilia_a" else "fix" if disease == "haemophilia_b" else "unknown",
            "inhibitor_status": inhibitor,
            "population": self._population(text) or "other_or_unknown",
            "therapy_modality": self._modality(text) or "other",
            "evidence_maturity": self._maturity(source_type=entities.get("source_type")),
        }

    def _maturity(self, source_type) -> str:
        """Sanjana/Usha evidence ladder: regulatory > peer-review/registry > congress > company > media."""
        return {"regulatory": "very_high", "pubmed": "high", "clinicaltrials": "high",
                "congress": "medium_high", "newsapi_company": "medium",
                "media": "lower"}.get(source_type, "medium")
```

**Extended Red-Team Evidence Checks** (`services/red_team_engine.py` v4.0) — in addition to NLI contradiction detection, the engine SHALL run the 19 evidence checks (A–S, Master Plan §12.7) on high-impact signals. Example implementation pattern for the deterministic (non-NLI) checks:

```python
# services/red_team_engine.py — evidence-check suite (v4.0)
EVIDENCE_CHECKS = {
    "A_causality": r"(adverse event|AE).{0,120}?(caused|due to|led to)",       # correlation ≠ causation
    "E_endpoint_definition": r"treated.*ABR|ABR.*treated",                     # preserve endpoint definitions
    "H_short_followup_durability": r"gene therap.{0,80}?durab",                # short FU ≠ lifelong durability
    "M_approval_reimbursement": r"approv.{0,80}?(reimburs|covered)",           # approval ≠ reimbursement
    "N_approval_access": r"approv.{0,80}?(available|access to patients)",      # approval ≠ actual access
}

def run_evidence_checks(signal) -> list[dict]:
    """Return triggered check ids with the governing rule; surfaced on the signal card."""
    flags = []
    for check_id, pattern in EVIDENCE_CHECKS.items():
        if re.search(pattern, signal["text"], re.IGNORECASE):
            flags.append({"check": check_id, "rule": MASTER_PLAN_S12_7[check_id],
                          "requires_human_review": True})
    return flags
```

**Missing-Signal Detector** (`services/missing_signal_detector.py` + `agents/missing_signal_agent.py`) — Analysis 4 of the Five. Uses the lifecycle state + B.Pharm-authored `MISSING_SIGNAL_RULES` (expected-event sequences with `max_lag_days`) to flag expected-but-absent milestones. Confidence grows with silence; configurable windows prevent over-warning:

```python
# services/missing_signal_detector.py
async def detect_missing_signals(lifecycles: list[dict]) -> list[dict]:
    for lc in lifecycles:
        rule = MISSING_SIGNAL_RULES.get(lc["pattern"])
        expected = rule["expected_sequence"][lc["stage_index"]]
        days = (now - lc["last_event_date"]).days
        if days > expected["max_lag_days"]:
            yield {
                "entity": lc["entity"],
                "missing_event": expected["event"],
                "days_since_last_signal": days,
                "max_lag_days": expected["max_lag_days"],
                "confidence": min(0.95, 0.4 + days * 0.02),   # confidence-by-silence
                "alert": rule["alert"],
            }
```

**Traceable Reasoning** (`services/traceability.py`) — every insight carries an evidence chain (source → URL → timestamp → excerpt → entities). Confidence computed from source count + platform diversity. Regulatory-grade audit trail.

**Temporal Pattern Recognition** (`services/temporal_patterns.py`) — matches current signal sets against B.Pharm-defined timeline patterns (pre-approval surge, access crisis) and reports current stage + predicted next stage.

**Narrative Synthesis** (`services/narrative_synthesizer.py`) — reasoning layer that converts all signals about a competitor/topic into a 3-part executive brief (WHAT HAPPENED / WHY IT MATTERS / RECOMMENDED ACTION), role-specific, via the **`LLMProvider` interface** below. Default provider `LocalGemmaProvider` — `LOCAL_LLM_MODEL` default `google/gemma-3-4b-it` (Gemma 3 4B Instruct, `text-generation` task), `google/gemma-3-1b-it` light-CPU option, or any HuggingFace-compatible text-generation model (Mistral 7B, Phi-3 Mini, TinyLlama, etc.) with a single config change. Optional `XAIProvider` (hosted Grok, `LLM_PROVIDER=xai|auto`, JSON-Schema structured outputs, gated by the external-LLM privacy gate). If no reasoning provider is available, `BartDegradedProvider` produces a **degraded factual summary only** (no interpretation, no reasoning-based action recommendation), so the demo does not hang on reasoning-provider failure (degraded path exercised by failure-injection tests). Every output carries model metadata (provider/model/mode/fallback_from/fallback_reason — SRS FR-2.2.3F).

**Provider Abstraction — LLMProvider** (`services/llm_provider.py`, v2.3) — one interface behind synthesis and Ask Athena; LangGraph nodes never call a specific model directly:

```python
# services/llm_provider.py — v2.3 (Master Plan v5.0 §13, SRS FR-2.2.3C/2.2.3G)
class LLMProvider(Protocol):
    async def generate_intelligence(self, evidence, task, output_schema, metadata) -> IntelligenceResult: ...

class LocalGemmaProvider(LLMProvider): ...   # LOCAL_LLM_MODEL (default google/gemma-3-4b-it)
class XAIProvider(LLMProvider): ...          # hosted Grok; JSON-Schema structured output; privacy-gated (FR-2.2.3D/E)
class BartDegradedProvider(LLMProvider): ... # factual summary ONLY; degraded_mode=true; never reasoning-equivalent
```

- `LLM_PROVIDER=local|xai|auto` selects the chain (Gemma → BART / Grok → BART / Gemma → Grok → BART).
- **FULL INTELLIGENCE OUTPUT** (Gemma/Grok) vs **DEGRADED FACTUAL SUMMARY** (BART) — two schemas, never mixed (FR-2.2.3G).
- Every result records model metadata: `provider` · `model` · `mode` · `fallback_from` · `fallback_reason` · `prompt_template_id` · `config_hash` · `temperature` · `generated_at` (FR-2.2.3F).

**Ask Athena Query Engine** (`services/query_engine.py`) — RAG over pgvector: hybrid search (alpha=0.6 semantic / 0.4 keyword) → grounded answer with supporting signals + confidence.

**Ingestion with Resilience** (`services/api_fetcher.py`) — uses `tenacity` + `httpx.AsyncClient` for exponential backoff retries (3 attempts, 2s/4s/8s waits) on all external API calls. Every raw response is persisted to `raw_signals_bronze` before transformation, enabling full pipeline replay on failure.


### 2.5 Database Design (PostgreSQL 16 + pgvector)

**Schema:**

```sql
-- Enable pgvector extension (vector search in the same DB as relational data)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ─────────────────────────────────────────────────────────────────────
-- ENTITY LAYER (v2.4 — Master Plan §14.2): stable entities with stable IDs.
-- Signals reference these by ID; ONE development accumulates MANY signals
-- (trial → congress abstract → oral → poster → publication stays one chain).
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL,       -- 'newsapi' | 'pubmed' | 'clinicaltrials' | 'fda' | 'ema' | 'congress' | 'reddit' | 'synthetic'
    publisher VARCHAR(255),
    freshness_class VARCHAR(20) NOT NULL,   -- real_time | near_real_time | delayed | batch | adapter_ready | synthetic
    syndication_group VARCHAR(100),         -- same syndicated content cluster (source independence, §14.4)
    parent_source_id UUID,                  -- canonical origin if this is a syndicated copy
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    canonical_name VARCHAR(255) NOT NULL
);

CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL UNIQUE,
    generic_name VARCHAR(255),
    brand_name VARCHAR(255),
    company_id UUID REFERENCES companies(id),
    mechanism VARCHAR(100),
    disease VARCHAR(30),
    factor VARCHAR(10),
    inhibitor_population VARCHAR(20),
    approval_status VARCHAR(50),            -- updateable fact, not static (ontology quality gate, §14.5)
    approval_date DATE,
    jurisdiction VARCHAR(100),
    ontology_source TEXT,
    last_verified TIMESTAMP
);

CREATE TABLE trials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trial_id UUID NOT NULL UNIQUE,
    nct_id VARCHAR(30),
    title TEXT,
    phase VARCHAR(20),
    status VARCHAR(30),
    company_id UUID REFERENCES companies(id),
    asset_id UUID REFERENCES assets(id)
);

CREATE TABLE developments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    development_id UUID NOT NULL UNIQUE,
    asset_id UUID REFERENCES assets(id),
    company_id UUID REFERENCES companies(id),
    trial_id UUID REFERENCES trials(id),
    current_lifecycle_state VARCHAR(30),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL UNIQUE,
    event_type VARCHAR(40) NOT NULL,        -- incl. publication_id | congress_event_id | regulatory_event_id | access_event_id
    development_id UUID REFERENCES developments(id),
    trial_id UUID REFERENCES trials(id),
    signal_id UUID,                          -- FK to signals(id) applied in migration order after signals table
    event_date TIMESTAMP,
    source_id UUID REFERENCES sources(id)
);
CREATE INDEX idx_events_development ON events(development_id, event_date);

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id UUID NOT NULL,                 -- claim → evidence; interpretation → evidence;
    claim_type VARCHAR(20),                 -- claim | interpretation | priority | routing | action
    source_id UUID REFERENCES sources(id),
    signal_id UUID,
    source_url TEXT,
    raw_content_hash TEXT,                  -- immutable provenance: sha256 of raw source text
    content_version INT DEFAULT 1,
    extracted_quote TEXT,
    evidence_level VARCHAR(15),             -- fact | interpretation | speculation
    created_at TIMESTAMP DEFAULT NOW()
);

-- Signals table (core)
CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,      -- 'newsapi', 'pubmed', 'clinicaltrials'
    original_url TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    original_text TEXT,
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW(),
    
    -- Quality metrics
    quality_score FLOAT DEFAULT 0.5,  -- 0.0-1.0 validation score
    relevance_score FLOAT DEFAULT 0.5, -- Overall importance
    velocity_score FLOAT DEFAULT 0.0,  -- Change rate
    signal_type VARCHAR(30),           -- canonical 11: clinical_trial | publication | congress |
                                       -- regulatory | safety | access | market | patient_advocacy |
                                       -- company_news | pipeline | other
                                       -- CONGRESS + PUBLICATION are first-class types (not news):
                                       -- congress subtypes: congress_abstract | oral_presentation |
                                       --   poster | new_congress_data | updated_congress_analysis |
                                       --   presentation_of_previously_known_data |
                                       --   congress_related_safety_signal | congress_related_efficacy_signal |
                                       --   congress_related_pro | congress_related_mechanism_dosing
                                       -- publication subtypes: peer_reviewed_publication | preprint |
                                       --   real_world_evidence | post_hoc_analysis |
                                       --   long_term_follow_up | safety_publication |
                                       --   patient_reported_outcomes | mechanistic_publication
    signal_subtype VARCHAR(40),        -- domain: gene_therapy_milestone | non_factor_therapy_update |
                                       -- inhibitor_development_signal | regulatory_milestone |
                                       -- congress_publication | patient_access_signal |
                                       -- competitive_pipeline_move (or congress/publication subtype)
    disease VARCHAR(20),               -- haemophilia_a | haemophilia_b | both | unknown
    patient_type VARCHAR(20),          -- with_inhibitors | without_inhibitors | unknown
    -- ── B.Pharm domain fields (v4.0) ──────────────────────────────
    factor VARCHAR(10),                -- fviii | fix | unknown (never guessed)
    inhibitor_status VARCHAR(20),      -- with_inhibitor | without_inhibitor | mixed | unknown
    population VARCHAR(20),            -- adult | adolescent | child | other_or_unknown
    therapy_modality VARCHAR(30),      -- factor_replacement | extended_half_life_factor | non_factor |
                                       -- bispecific_antibody | sirna | gene_therapy | aav_gene_therapy |
                                       -- lentiviral | gene_editing | other
    evidence_maturity VARCHAR(15),     -- very_high | high | medium_high | medium | lower
    source_authority VARCHAR(255),     -- regulator / peer-reviewed journal / registry / company / media
    clinical_evidence JSONB,           -- nullable: trial_id, trial_phase, study_design, comparator,
                                       -- primary_endpoint, secondary_endpoints, abr, bleeding_outcome,
                                       -- joint_or_target_joint_outcome, patient_reported_outcome,
                                       -- quality_of_life_outcome, treatment_burden, follow_up_duration,
                                       -- sample_size, safety_findings, effect_size, confidence_interval,
                                       -- p_value, interim_or_final
    access_info JSONB,                 -- nullable (access signals only): country, jurisdiction,
                                       -- effective_date, expiry_or_review_date, coverage_status,
                                       -- restrictions, prior_authorisation, specialist_centre_requirements,
                                       -- intended_vs_actual_access
    company VARCHAR(255),              -- ontology-normalized
    asset VARCHAR(255),                -- ontology-normalized
    asset_type VARCHAR(30),            -- bispecific_antibody | anti_tfpi | rnai | gene_therapy |
                                       -- factor_replacement | ehl_factor | other
    priority VARCHAR(10),              -- high | medium | low
    scoring_model_version VARCHAR(10), -- scoring model version (e.g., 'v1') — versioned scoring (v2.4, §14.10)
    scoring_config_version VARCHAR(40),-- scoring config version (e.g., 'haemophilia_v1')
    score_breakdown JSONB,             -- factor-level priority breakdown (novelty/safety/regulatory/access/...)
    impacted_functions JSONB,          -- {"primary": "medical_affairs", "secondary": ["regulatory"]}
    development_id UUID,              -- lifecycle chain this signal belongs to; NULL = NEW DEVELOPMENT
    event_date TIMESTAMP,             -- underlying event date (congress presentation, publication...)
    source_id UUID,                   -- canonical source reference (FK to raw_signals_bronze,
                                       -- applied in migration order after bronze table)
    fis_label VARCHAR(20),             -- fact | interpretation | speculation
    evidence_sufficient BOOLEAN DEFAULT FALSE,  -- evidence-sufficiency gate result
    confluence_level VARCHAR(10),      -- CRITICAL | HIGH | MEDIUM | LOW (if part of confluence)
    
    -- Extracted metadata (JSONB for flexibility)
    entities JSONB,  -- {"drugs": ["emicizumab"], "companies": [...], ...}
    ontology_context JSONB,  -- {"emicizumab": {"drug_class": "Bispecific antibody", "manufacturer": "Roche"}}
    metadata JSONB,  -- {"language": "en", "word_count": 150, ...}
    
    -- Role-specific relevance (JSONB indexed)
    role_relevance JSONB DEFAULT '{}',  -- {"medical_affairs": 0.92, "regulatory": 0.65, ...}
    
    -- Embedding (pgvector, 384-dim for all-MiniLM-L6-v2)
    embedding vector(384),
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'archived', 'duplicate'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes (critical for performance)
CREATE INDEX idx_signals_role_medical 
    ON signals USING GIN (role_relevance)
    WHERE status = 'active';

CREATE INDEX idx_signals_published 
    ON signals (published_at DESC)
    WHERE status = 'active';

CREATE INDEX idx_signals_source 
    ON signals (source)
    WHERE status = 'active';

CREATE INDEX idx_signals_type
    ON signals (signal_type)
    WHERE status = 'active';

-- Vector index (semantic search). ivfflat: fast, approximate, demo-appropriate.
CREATE INDEX idx_signals_embedding
    ON signals USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Keyword/trigram index (hybrid search partner for pgvector)
CREATE INDEX idx_signals_title_trgm ON signals USING GIN (title gin_trgm_ops);

-- Confluence events table (consolidated strategic alerts)
CREATE TABLE confluence_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity VARCHAR(255) NOT NULL,
    alert_level VARCHAR(10) NOT NULL,     -- CRITICAL | HIGH | MEDIUM | LOW
    signal_count INT NOT NULL,
    signal_types JSONB NOT NULL,          -- ["regulatory", "clinical", ...]
    window_hours INT DEFAULT 48,
    story_summary TEXT,
    development_id UUID,                 -- link decision: NEW DEVELOPMENT (NULL) vs
                                         -- NEW EVIDENCE for existing development (set)
    link_decision VARCHAR(30),           -- 'linked' | 'possibly_linked' | 'unlinked'
                                       -- (ambiguous matches: 'possibly_linked' + requires_human_review TRUE)
    status VARCHAR(20) DEFAULT 'active',
    detected_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_confluence_entity ON confluence_events(entity, detected_at DESC);
CREATE INDEX idx_confluence_level ON confluence_events(alert_level);

-- ─────────────────────────────────────────────────────────────────────
-- SIGNAL LIFECYCLE TRACKING (Analysis 2 of the Five) — NEW v2.1
-- ─────────────────────────────────────────────────────────────────────
-- Per-development state machine: announced → in_trial → results_in →
-- under_review → approved → post_market | discontinued
CREATE TABLE lifecycle_chains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity VARCHAR(255) NOT NULL,           -- 'mim8', 'Hemgenix', ...
    modality VARCHAR(50),                   -- 'bispecific', 'gene_therapy', 'anti_tfpi', 'rnai'
    indication VARCHAR(50),                 -- 'haemophilia_a', 'haemophilia_b'
    current_state VARCHAR(30) NOT NULL,     -- lifecycle state
    expected_next JSONB,                    -- [{event, max_lag_days}]
    pattern VARCHAR(50),                    -- matching MISSING_SIGNAL_RULES pattern
    last_event_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity, modality, indication)
);
CREATE INDEX idx_lifecycle_entity ON lifecycle_chains(entity, current_state);

-- Individual events in each chain (temporal links)
-- Every event records event_type · event_date · development_id · source_id so a
-- trial → congress abstract → oral presentation → poster → publication chain
-- stays ONE development timeline (NEW EVIDENCE ABOUT EXISTING DEVELOPMENT).
CREATE TABLE lifecycle_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id UUID REFERENCES lifecycle_chains(id) ON DELETE CASCADE,
    development_id UUID,                   -- same as chain_id (explicit per kickoff schema)
    signal_id UUID REFERENCES signals(id) ON DELETE CASCADE,
    event_type VARCHAR(40) NOT NULL,       -- announced | in_trial | interim_result | final_result |
                                           -- congress_abstract | oral_presentation | poster |
                                           -- publication | regulatory_development | approved | ...
    event_date TIMESTAMP NOT NULL,         -- date of the underlying event (not fetch date)
    source_id UUID,                        -- source record reference
    state VARCHAR(30) NOT NULL,
    ordered_date TIMESTAMP NOT NULL,       -- published_at of the signal
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_lifecycle_events_chain ON lifecycle_events(chain_id, ordered_date);

-- ─────────────────────────────────────────────────────────────────────
-- RED-TEAM CONTRADICTION ANALYSIS (Analysis 3 of the Five) — NEW v2.1
-- ─────────────────────────────────────────────────────────────────────
-- Pairwise NLI entailment contradictions between signals on same entity
CREATE TABLE contradictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity VARCHAR(255) NOT NULL,
    claim_a JSONB NOT NULL,                 -- {text, source, url, date}
    claim_b JSONB NOT NULL,                 -- {text, source, url, date}
    contradiction_score FLOAT NOT NULL,     -- NLI score > 0.6 threshold
    red_team_note TEXT,
    status VARCHAR(20) DEFAULT 'open',      -- open | resolved | dismissed
    requires_human_review BOOLEAN DEFAULT TRUE,
    detected_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_contradictions_entity ON contradictions(entity, detected_at DESC);

-- ─────────────────────────────────────────────────────────────────────
-- MISSING-SIGNAL DETECTION (Analysis 4 of the Five) — NEW v2.1
-- ─────────────────────────────────────────────────────────────────────
-- B.Pharm-authored expected-event sequences (rules) + alerts
CREATE TABLE missing_signal_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern VARCHAR(50) NOT NULL UNIQUE,    -- 'gene_therapy_durability', 'phase3_readout_followup'
    expected_sequence JSONB NOT NULL,       -- [{event, max_lag_days}, ...]
    alert_message TEXT NOT NULL
);

CREATE TABLE missing_signal_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity VARCHAR(255) NOT NULL,
    chain_id UUID REFERENCES lifecycle_chains(id) ON DELETE CASCADE,
    missing_event TEXT NOT NULL,
    days_since_last_signal INT NOT NULL,
    max_lag_days INT NOT NULL,
    confidence FLOAT NOT NULL,              -- confidence-by-silence (0.4 + days*0.02, capped 0.95)
    status VARCHAR(20) DEFAULT 'watch',     -- watch (monitoring signal, NOT a claim) | resolved
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_missing_alerts_entity ON missing_signal_alerts(entity, status);

-- ─────────────────────────────────────────────────────────────────────
-- CONTROLLED ACTION RECOMMENDATIONS (FR-2.6.1, kickoff-aligned)
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE action_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES signals(id) ON DELETE CASCADE,
    action VARCHAR(40) NOT NULL,        -- monitor | review | prepare_internal_briefing |
                                        -- prepare_scientific_faq | escalate |
                                        -- request_stakeholder_review | no_immediate_action
    reason TEXT NOT NULL,
    relevant_function VARCHAR(50) NOT NULL,
    evidence JSONB,                     -- evidence chain backing this action
    confidence FLOAT,
    human_review_required BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ─────────────────────────────────────────────────────────────────────
-- SIGNAL ROUTING (relevance-based routing, FR-2.5.1)
-- "Not every signal goes to everyone" — explainable per-signal routing.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE signal_routing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES signals(id) ON DELETE CASCADE UNIQUE,
    primary_function VARCHAR(50) NOT NULL,      -- medical_affairs | regulatory | safety_pv |
                                                -- market_access | medical_communications | leadership
    secondary_functions JSONB NOT NULL DEFAULT '[]',  -- ["medical_communications", "regulatory"]
    function_relevance_scores JSONB NOT NULL,   -- {"medical_affairs": 0.91, ...} (calibrated)
    routing_reason TEXT NOT NULL,               -- "why this function, why now" (explainable)
    suggested_action VARCHAR(60),               -- controlled vocabulary (FR-2.6.1)
    baseline_primary_function VARCHAR(50),      -- pre-calibration AI baseline (v2.4, §14.10) — NEVER overwritten
    baseline_relevance_scores JSONB,
    baseline_suggested_action VARCHAR(60),
    calibration_version VARCHAR(10),
    feedback_id UUID,                          -- originating stakeholder feedback row
    calibrated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_signal_routing_signal ON signal_routing(signal_id);
CREATE INDEX idx_signal_routing_primary ON signal_routing(primary_function);

-- ─────────────────────────────────────────────────────────────────────
-- WATCH ITEMS (stakeholder-defined Watch-for-Next, FR-2.3C.1A)
-- Extends Missing-Signal — NO separate watch engine.
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE watch_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    watch_id VARCHAR(50) NOT NULL UNIQUE,       -- e.g. 'watch-fr4-congress'
    source_event_id UUID REFERENCES signals(id) ON DELETE CASCADE,  -- trial/development signal
    expected_event_type VARCHAR(60) NOT NULL,   -- e.g. 'congress_disclosure' | 'publication' |
                                                -- 'regulatory_submission'
    monitoring_window_days INT NOT NULL DEFAULT 180,
    responsible_function VARCHAR(50) NOT NULL,  -- function(s) to notify
    status VARCHAR(30) NOT NULL DEFAULT 'watching',  -- watching | new_evidence_detected |
                                                -- no_new_evidence | watch_expired |
                                                -- human_review_required
    created_by TEXT,                            -- stakeholder / persona id
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    last_message TEXT                          -- "Watch for upcoming congress disclosures ·
                                                -- Expected/possible next evidence · Not observed yet"
);
CREATE INDEX idx_watch_items_status ON watch_items(status);
CREATE INDEX idx_watch_items_source ON watch_items(source_event_id);

-- ─────────────────────────────────────────────────────────────────────
-- WATCHLISTS (entity focus, MR-WATCH-1)
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_watchlist_user ON watchlists(user_id, created_at DESC);

-- ─────────────────────────────────────────────────────────────────────
-- WEEKLY DIGESTS (function-filtered, reuses brief agents)
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE digests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    function VARCHAR(50) NOT NULL,      -- medical_affairs | regulatory | safety_pv | ...
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    items JSONB NOT NULL,               -- ranked developments: what_changed / why / action /
                                        -- evidence / confidence (F-I-S labeled)
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_digests_function_week ON digests(function, week_start DESC);

-- ─────────────────────────────────────────────────────────────────────
-- STAKEHOLDER CALIBRATION LOOP (HITL) — NEW in v2.0
-- ─────────────────────────────────────────────────────────────────────
-- Append-only stakeholder feedback (routing accuracy ratings per signal)
CREATE TABLE stakeholder_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id UUID REFERENCES signals(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,          -- medical_affairs | regulatory | safety_pv | market_access |
                                        -- medical_communications | leadership (primary);
                                        -- commercial | rd (extended)
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    reason TEXT,
    user_id TEXT,                       -- real user OR simulated persona id (hackathon)
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX idx_feedback_role ON stakeholder_feedback(role, created_at DESC);
CREATE INDEX idx_feedback_signal ON stakeholder_feedback(signal_id);
-- WORM: REVOKE UPDATE, DELETE ON stakeholder_feedback FROM app_user;

-- Current role × signal_type scoring weights (recalibrated by HITL)
CREATE TABLE scoring_weights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(50) NOT NULL,
    signal_type VARCHAR(30) NOT NULL,
    weight FLOAT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    updated_by TEXT,                    -- 'human:regulatory_persona' | 'system'
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,
    UNIQUE(role, signal_type, version)
);

-- Calibration history (every recalibration is audited)
CREATE TABLE calibration_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role VARCHAR(50) NOT NULL,
    old_weights JSONB NOT NULL,
    new_weights JSONB NOT NULL,
    calibration_version VARCHAR(10),    -- e.g., 'v1' (v2.4, §14.10)
    trigger_reason TEXT,                -- 'stakeholder_feedback_batch' | 'manual'
    feedback_count INT,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX idx_calib_history_role ON calibration_history(role, created_at DESC);

-- Narrative briefs (executive intelligence output)
CREATE TABLE briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,            -- medical_affairs | regulatory | commercial
    brief_type VARCHAR(30) DEFAULT 'weekly',  -- weekly | confluence_alert
    what_happened TEXT,
    why_it_matters TEXT,
    recommended_action TEXT,
    source_count INT,
    confidence FLOAT,
    evidence_chain JSONB,                 -- [{source, url, timestamp, excerpt}]
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_briefs_entity_role ON briefs(entity, role, created_at DESC);

-- Entities table (for entity-centric queries)
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,        -- "emicizumab", "Novo Nordisk"
    type VARCHAR(50) NOT NULL,         -- 'drug', 'company', 'indication'
    canonical_name VARCHAR(255),       -- Standardized name
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_entity_canonical ON entities(canonical_name, type);

-- Signal-entity relationship
CREATE TABLE signal_entities (
    signal_id UUID REFERENCES signals(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    PRIMARY KEY (signal_id, entity_id)
);

CREATE INDEX idx_signal_entities_entity ON signal_entities(entity_id);

-- Trending scores (for velocity detection + performance)
CREATE TABLE trending_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    mention_count INT DEFAULT 0,
    velocity_score FLOAT DEFAULT 0.0,  -- Rate of change
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(entity_id, date)
);

CREATE INDEX idx_trending_entity_date ON trending_scores(entity_id, date DESC);

-- Materialized view (pre-computed high-relevance signals)
CREATE MATERIALIZED VIEW signals_medical_affairs_high_priority AS
SELECT 
    s.id, s.title, s.summary, s.source, s.published_at,
    s.relevance_score,
    (s.role_relevance->>'medical_affairs')::FLOAT as ma_relevance,
    s.entities
FROM signals s
WHERE status = 'active'
    AND (s.role_relevance->>'medical_affairs')::FLOAT > 0.7
ORDER BY s.published_at DESC
LIMIT 500;

-- Refresh view daily at 2 AM
-- CRON JOB: SELECT cron.schedule('refresh-medical-affairs', '0 2 * * *',
--   'REFRESH MATERIALIZED VIEW signals_medical_affairs_high_priority');

-- ─────────────────────────────────────────────────────────────────────
-- BRONZE LAYER: raw API responses stored before any transformation
-- Purpose: full pipeline replay if NLP/scoring fails mid-run
-- (research report Section 2 recommendation)
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE raw_signals_bronze (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source      VARCHAR(50) NOT NULL,   -- 'newsapi', 'pubmed', etc.
    raw_json    JSONB NOT NULL,         -- verbatim API response
    fetched_at  TIMESTAMP DEFAULT NOW() NOT NULL,
    processed   BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_bronze_unprocessed
    ON raw_signals_bronze(source, fetched_at)
    WHERE processed = FALSE;

-- ─────────────────────────────────────────────────────────────────────
-- COMPLIANCE AUDIT LOG: WORM-enforced append-only audit trail
-- (engineering design analogy inspired by electronic-record traceability
--  principles; MetaRadar does NOT claim 21 CFR Part 11 or GxP compliance)
-- IMPORTANT: REVOKE UPDATE, DELETE ON audit_log FROM app_user;
-- ─────────────────────────────────────────────────────────────────────
CREATE TABLE audit_log (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      TEXT NOT NULL,
    action       TEXT NOT NULL,       -- taxonomy_edit | score_adjust | signal_dismiss | role_change
    entity       TEXT NOT NULL,
    before_state JSONB,               -- snapshot before change
    after_state  JSONB,               -- snapshot after change
    session_id   TEXT,
    timestamp    TIMESTAMP DEFAULT NOW() NOT NULL
);
CREATE INDEX idx_audit_user   ON audit_log(user_id, timestamp DESC);
CREATE INDEX idx_audit_entity ON audit_log(entity, timestamp DESC);
-- REVOKE UPDATE, DELETE ON audit_log FROM app_user;  -- enforce WORM at DB level
```

### 2.6 Vector Search Design (pgvector)

Weaviate was **replaced with pgvector** (see Refined Architecture) — vector search lives inside PostgreSQL 16, eliminating one Docker container. Hybrid search = pgvector (dense/semantic) + pg_trgm/FTS (sparse/keyword), both in the same database.

**Schema:**
```sql
-- Already defined in 2.5: signals.embedding vector(384)
-- + idx_signals_embedding (ivfflat) + idx_signals_title_trgm (gin_trgm_ops)
```

**Hybrid search query (semantic + keyword in one SQL call):**
```sql
-- Semantic part (pgvector): nearest 10 by cosine similarity
SELECT id, title, summary, relevance_score,
       1 - (embedding <=> :query_embedding) AS semantic_score
FROM signals
WHERE status = 'active' AND embedding IS NOT NULL
ORDER BY embedding <=> :query_embedding
LIMIT 10;

-- Keyword part (pg_trgm): fuzzy title match
SELECT id, title, summary, relevance_score,
       similarity(title, :query) AS keyword_score
FROM signals
WHERE status = 'active' AND title % :query
ORDER BY keyword_score DESC
LIMIT 10;

-- Combined hybrid (alpha = 0.6 semantic / 0.4 keyword), implemented in query_engine.py
-- Rerank via Reciprocal Rank Fusion on the two result sets.
```

**Ask Athena query flow (RAG over pgvector):**
```python
# services/query_engine.py
async def query(self, question: str, role: str) -> dict:
    q_emb = embed(question)                       # all-MiniLM-L6-v2 (local)
    sem = await pg.fetch_top_semantic(q_emb)      # pgvector  <=>
    kw  = await pg.fetch_top_keyword(question)    # pg_trgm  %
    relevant = rrf_merge(sem, kw, alpha=0.6)      # rerank, role-filtered
    answer = await llm_provider.generate_intelligence(  # LLMProvider chain: Gemma → Grok → BART degraded (FR-2.2.3C)
        evidence=relevant, task="athena_answer",
        output_schema=FULL_INTELLIGENCE, metadata={"role": role})
    # provider: LOCAL_LLM_MODEL (default google/gemma-3-4b-it) or Grok; BART degraded if no reasoning provider
    return {"answer": answer, "supporting_signals": relevant[:3],
            "confidence": retrieval_confidence(relevant)}
```

**Query Examples:**
```sql
-- Semantic similarity (vector-only)
SELECT id, title FROM signals
ORDER BY embedding <=> (SELECT embedding FROM signals WHERE id = :seed)
LIMIT 10;

-- Hybrid (semantic + keyword) for "mim8 latest data"
SELECT id, title FROM signals
WHERE status = 'active'
ORDER BY (1 - (embedding <=> :q_emb)) * 0.6 + similarity(title, 'mim8 latest data') * 0.4 DESC
LIMIT 10;
```

### 2.7 Caching Strategy (Redis)

**Cache Key Hierarchy:**

```
signals:{role}:{offset}             # Dashboard data
  TTL: 2 hours
  Size: ~200KB per role
  Hit rate target: > 80%

trends:{entity}:{days}              # Trend chart data
  TTL: 1 hour
  Size: ~50KB per entity

entities:all                        # Reference list of drugs/companies
  TTL: 24 hours
  Size: ~5MB

api_responses:{source}:{query}      # Raw API responses
  TTL: Based on API rate limit window
  Size: ~500KB per source

rate_limit:{source}:{user}          # Rate limit tracking
  TTL: Rate limit period
  Size: ~1KB per entry

sessions:{session_id}               # User sessions
  TTL: 24 hours
  Size: ~10KB per session
```

**Cache Invalidation Strategy:**

```python
class CacheInvalidator:
    """Smart cache invalidation without full cache clear"""
    
    async def on_new_signals(self, signals: list[Signal]):
        """Invalidate only affected cache keys"""
        
        # Invalidate role dashboards (signals changed)
        for role in ['medical_affairs', 'regulatory', 'commercial']:
            await redis.delete(f"signals:{role}:*")
        
        # Invalidate trends (mention count changed)
        entities = extract_entities_from(signals)
        for entity in entities:
            await redis.delete(f"trends:{entity}:*")
        
        # Keep entity list cache (doesn't change)
        # Keep session cache (unaffected)
    
    async def full_refresh(self):
        """Called nightly or on major schema changes"""
        await redis.flushdb()
        logger.info("✅ Cache fully refreshed")
```

---

### 2.9 Compliance & Security Design

**Research report alignment: Sections 2 & 6**

This section covers three compliance requirements identified in the deep research report:

#### 2.9.1 PII Detection Pipeline

```python
# services/pii_scrubber.py
# Dedicated PII/PHI detection and redaction layer — runs as the FIRST step
# after raw API fetch, BEFORE any storage. spaCy NER contributes to entity
# detection but is NOT a guaranteed scrubber: when detection confidence is
# insufficient the content is REJECTED or QUARANTINED rather than persisted.
import spacy

_nlp = spacy.load("en_core_web_sm")  # lightweight, fast

PII_LABELS = {"PERSON", "ORG", "EMAIL", "PHONE", "ID"}

def scrub_pii(text: str) -> str:
    """Detect and redact PII/PHI from scraped content before storage.
    Unexpected PII (e.g., a patient name in a clinical report) is replaced
    with [REDACTED:<LABEL>] and the event is logged for audit.
    Low-confidence detections must be rejected/quarantined by the caller."""
    doc = _nlp(text)
    scrubbed = text
    for ent in reversed(doc.ents):
        if ent.label_ in PII_LABELS:
            scrubbed = scrubbed[:ent.start_char] + \
                       f"[REDACTED:{ent.label_}]" + \
                       scrubbed[ent.end_char:]
    return scrubbed
```

#### 2.9.2 WORM Audit Logger

```python
# services/audit_logger.py
# Append-only, never updates or deletes — WORM enforcement
# (design analogy inspired by electronic-record traceability principles;
#  no 21 CFR Part 11 / GxP compliance claim)

class ComplianceAuditLogger:
    """Write-once audit trail. DB-level WORM enforced via REVOKE."""

    async def log(self, user_id: str, action: str, entity: str,
                  before: dict = None, after: dict = None,
                  session_id: str = None):
        await db.execute("""
            INSERT INTO audit_log
                (user_id, action, entity, before_state, after_state, session_id, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """, user_id, action, entity,
             json.dumps(before or {}),
             json.dumps(after or {}),
             session_id)

audit_logger = ComplianceAuditLogger()
```

Action types logged:
- `taxonomy_edit` — B.Pharm ontology changes
- `score_adjust` — Manual relevance override
- `signal_dismiss` — User hides a signal
- `role_change` — User switches view role

#### 2.9.3 Medical Accuracy Disclaimer

Every AI-generated output (summary, confluence story, narrative brief) MUST carry the disclaimer below. It is injected by `narrative_synthesizer.py` and rendered by the frontend — suppression is not permitted.

```python
MEDICAL_DISCLAIMER = (
    "Auto-generated by MetaRadar AI — verify clinically before use. "
    "Not a substitute for professional medical judgment."
)
```

Displayed as a muted label on every signal card summary, confluence alert, and narrative brief.

---

## **3. DATA FLOW**

### 3.1 Signal Ingestion Flow

```
1. FETCH (Every 2 hours, async parallel)
   ├─ fetch_newsapi()          → ≤100 articles/day    (LIVE; Developer quota)
   ├─ fetch_pubmed()           → 100 papers          (LIVE)
   ├─ fetch_clinicaltrials()   → 50 trial updates    (LIVE)
   ├─ fetch_reddit()           → 200 posts           (ADAPTER-READY)
   └─ fetch_fda()              → 10 documents        (ADAPTER-READY)
   = 860 raw signals (live) + 500 synthetic fallback

2. VALIDATE (Reject low-quality)
   ├─ Check required fields
   ├─ Check text length > 50
   ├─ Check language = English
   ├─ Check not semantic duplicate
   └─ Assign quality_score
   = 1500 valid signals (17% rejection rate)

3. DEDUPLICATE (Across sources)
   ├─ Same news from Reuters + Bloomberg = keep 1
   ├─ Same paper from PubMed + arXiv = keep 1
   └─ Semantic similarity > 80% = keep highest score
   = 800 unique signals (47% dedup rate)

4. EXTRACT ENTITIES (Batch NLP)
   ├─ Extract drugs: "emicizumab", "mim8", "concizumab", "Hemgenix"
   ├─ Extract companies: "Roche", "Novo Nordisk", "CSL Behring", "BioMarin"
   ├─ Extract indications: "Haemophilia A", "Haemophilia B", "inhibitor development"
   └─ Extract phases: "Phase 3", "FDA approval", "CHMP opinion"
   = 2400 entities extracted

5. CLASSIFY SIGNALS (zero-shot BART-MNLI, haemophilia taxonomy)
   ├─ "Hemgenix 3-year durability data at ASH" → GENE_THERAPY_MILESTONE
   ├─ "mim8 Phase 3 meets primary endpoint" → COMPETITIVE_PIPELINE_MOVE
   └─ "FDA approves fitusiran" → REGULATORY_MILESTONE

6. ENRICH WITH PHARMA ONTOLOGY (B.Pharm, local JSON)
   ├─ "Hemlibra" → emicizumab → bispecific antibody → Roche → NOVO COMPETITOR
   ├─ "Alhemo" → concizumab → anti-TFPI → Novo Nordisk (own asset)
   └─ Validation layer: catches NER false positives before storage

7. SCORE RELEVANCE
   ├─ Source credibility: PubMed=0.95, Reddit=0.40
   ├─ Entity match (portfolio relevance + ontology context)
   ├─ Pharma keyword density
   └─ Final score: 0.0-1.0
   
8. COMPUTE FUNCTION RELEVANCE (relevance-based routing — "not every signal goes to everyone")
   ├─ For Medical Affairs: weight clinical + congress + safety
   ├─ For Regulatory: weight regulatory filings + safety
   ├─ For Safety/PV: weight safety signals highest
   ├─ For Market Access: weight access + market signals
   ├─ For Medical Communications: weight congress + publication + company_news
   ├─ For Leadership: weight strategic/pipeline + escalation triggers
   └─ Result: function_relevance = {"medical_affairs": 0.92, "regulatory": 0.71, ...}
   + primary/secondary function assignment + **routing_reason** (why this function, why now)
   + role-specific suggested action (controlled vocabulary) — stored in signal_routing table
   (initial routing matrix is seed-only; calibration adjusts weights — all share one evidence chain)

9. EMBED (Create vectors for semantic search)
   ├─ title + summary → 384-dim vector (all-MiniLM-L6-v2, local)
   └─ Store in pgvector column (same PostgreSQL DB)

10. DETECT CONFLUENCE (LangGraph confluence agent — Analysis 1)
    ├─ Group signals by entity within 48h window
    ├─ ≥ 3 signal types on same entity → confluence event (per-pattern configurable)
    ├─ Apply matrix → CRITICAL / HIGH / MEDIUM / LOW alert
    ├─ **Development-link decision:** congress/publication signal matching an existing
    │   development_id → link into that chain (new_evidence_existing_development),
    │   NOT a new card; otherwise new_development
    └─ Store consolidated alert in confluence_events table (+ development_id, link_decision)

10A. TRACK LIFECYCLES (LangGraph lifecycle agent — Analysis 2)
    ├─ Assign each signal to its lifecycle chain (entity + modality + indication)
    ├─ Advance state: announced → in_trial → results_in → under_review → ...
    ├─ Every event records: event_type · event_date · development_id · source_id
    ├─ Distinguish NEW DEVELOPMENT vs NEW EVIDENCE ABOUT EXISTING DEVELOPMENT
    ├─ Compute expected next event + temporal links (trial → congress abstract → oral → poster → publication stays ONE chain)
    └─ Store in lifecycle_chains + lifecycle_events

10B. RED-TEAM CONTRADICTION SCAN (LangGraph red_team agent — Analysis 3)
    ├─ Pairwise NLI entailment on same-entity signals (rolling 90d window)
    ├─ bart-large-mnli labels contradiction > 0.6 → flag
    ├─ Attach devil's-advocate red-team note
    └─ Store in contradictions table (both evidence chains shown)

10C. MISSING-SIGNAL SCAN + WATCH-FOR-NEXT (LangGraph missing_signal agent — Analysis 4)
    ├─ For each lifecycle: expected-next-event overdue (> max_lag_days)?
    ├─ Confidence grows with silence (0.4 + days*0.02, capped 0.95)
    ├─ Configurable windows prevent over-warning
    ├─ **Stakeholder-defined WATCH RULES:** source_event → expected_event_type (e.g.,
    │   congress_disclosure) → monitoring window → responsible function → status
    │   (watching / new_evidence_detected / no_new_evidence / watch_expired /
    │   human_review_required); wording: "Watch for… / Expected/possible next evidence /
    │   Not observed yet"; absence → "No subsequent congress evidence observed during the
    │   configured monitoring window." (never proof that nothing happened)
    └─ Store in missing_signal_alerts + watch_items tables

11. EVIDENCE SUFFICIENCY + SYNTHESIZE (LangGraph synthesis agent)
    ├─ Evidence-sufficiency gate: sufficient? → grounded interpretation
    │   → insufficient? → "Insufficient evidence to support an interpretation" + human review
    ├─ F-I-S label assigned to every output: FACT / INTERPRETATION / SPECULATION
    ├─ Confluence alert → 2-sentence executive alert
    ├─ Weekly per-entity → WHAT / WHY / ACTION brief (Four-Question wiring)
    ├─ Red-team contradiction + missing-signal flags folded into Q2/Q4
    └─ Grounded in traceable evidence chain (never speculative)

12. STORE (Persist to databases)
    ├─ Insert into PostgreSQL signals table
    ├─ Insert entities into entities table
    ├─ Create signal-entity relationships
    ├─ Vector stored in signals.embedding (pgvector)
    ├─ Lifecycle chains/events, contradictions, missing-signal alerts
    └─ Everything mirrored into audit_log (WORM) as applicable

13. CACHE (Invalidate old, populate new)
    ├─ Invalidate role dashboards
    ├─ Invalidate confluence alerts cache
    ├─ Invalidate lifecycle/contradiction/missing-signal caches
    ├─ Refresh trend aggregations
    └─ Update materialized views

14. CALIBRATE (LangGraph calibration agent — Analysis 5, HITL)
    ├─ Load stakeholder_feedback for this role batch
    ├─ StakeholderCalibrationService.recalibrate(role)
    ├─ Update scoring_weights + calibration_history + audit_log (WORM)
    ├─ Scope: priority · routing · action · watch rules · relevance criteria
    ├─ Watch rules: stakeholder comment like "monitor this competitor trial for future
    │   congress disclosures" creates a watch_items row (Watch-for-Next)
    └─ Next ingestion cycle uses the recalibrated weights

15. DONE
    ✅ 800 signals + confluence alerts + lifecycle chains + contradiction flags
       + missing-signal alerts + watch items + narrative briefs + calibrated weights ready
    ✅ Every insight passed all FIVE advanced analyses before reaching the brief
    ✅ Every congress/publication signal linked to its development (or flagged new)
    ✅ Every high-priority signal has explainable routing (primary/secondary + routing_reason)
```

### 3.2 Dashboard Request Flow

```
USER BROWSER
   │
   └─> GET /dashboard?role=medical_affairs
       │
       ├─ Next.js Server Component
       │  └─ useQuery() hook
       │
       └─> GET /api/v1/signals?role=medical_affairs&limit=20&offset=0
           │
           ├─ API Gateway
           │  ├─ Validate JWT token
           │  └─ Check rate limit (100 req/min)
           │
           └─> FastAPI Endpoint
              │
              ├─ Check Redis cache
              │  ✓ Hit? Return cached data (< 1ms)
              │  ✗ Miss? Continue...
              │
              ├─ Query PostgreSQL (with indexes)
              │  SELECT * FROM signals
              │  WHERE role_relevance->>'medical_affairs' > 0.6
              │  ORDER BY relevance_score DESC
              │  LIMIT 20
              │  (Takes < 100ms)
              │
              ├─ Enrich with entity details
              │  SELECT * FROM signal_entities
              │  WHERE signal_id IN (...)
              │
              ├─ Cache in Redis (2 hour TTL)
              │
              └─> JSON Response (200ms total)
                  {
                    "signals": [...],
                    "total": 1200,
                    "offset": 0,
                    "limit": 20
                  }
              
              └─> Browser receives → React renders
                  └─ Virtual scroll shows first 20
                     (rest load on scroll)
```

---

## **4. DESIGN PATTERNS & PRINCIPLES**

### 4.1 Design Patterns Used

| Pattern | Where Used | Benefit |
|---|---|---|
| **Repository Pattern** | DBService wraps all DB queries | Testable, abstracted from ORM |
| **Service Layer** | SignalProcessor, NLPService | Business logic isolated from API |
| **Dependency Injection** | FastAPI Depends() | Testable, loose coupling |
| **Builder Pattern** | APIRequest construction | Complex object creation |
| **Observer Pattern** | Cache invalidation on new signals | Decoupled components |
| **Strategy Pattern** | Multiple scoring algorithms | Swappable implementations |
| **Circuit Breaker** | API fetcher with retry logic | Graceful failure handling |
| **State Graph Pattern** | LangGraph multi-agent orchestration | Automatic state flow between agents |
| **Evidence Chain Pattern** | Traceable Insight service | Regulatory-grade audit trail |
| **Confluence Pattern** | Signal Confluence Engine | Cross-source convergence → strategic alerts |
| **Lifecycle State-Machine Pattern** | Signal Lifecycle Tracker (v2.1) | Chronological chains per development, expected-next computation |
| **Red-Team / Devil's-Advocate Pattern** | Red-Team Contradiction Engine (v2.1) | NLI entailment flags contradicting claims, human review required |
| **Expected-Event Pattern** | Missing-Signal Detector (v2.1) | Absence of a signal is itself a signal (confidence-by-silence) |
| **Human-in-the-Loop (HITL) Pattern** | Stakeholder Calibration Loop (v2.0) | Persona feedback recalibrates role-scoring weights; AI suggests, humans review |

### 4.2 SOLID Principles

- **S**ingle Responsibility: Each service does one thing (fetch, process, score, store)
- **O**pen/Closed: Open for extension (new data sources), closed for modification
- **L**iskov Substitution: Scorers have consistent interface
- **I**nterface Segregation: Small, focused interfaces (not "God objects")
- **D**ependency Inversion: Depend on abstractions, not implementations

### 4.3 Clean Architecture Layers

```
Presentation Layer (Next.js)
        ↓
Application Layer (FastAPI routes)
        ↓
Domain Layer (Business logic: scoring, entity extraction)
        ↓
Infrastructure Layer (DB, cache, APIs)
```

---

## **5. ERROR HANDLING & RESILIENCE**

### 5.1 Failure Modes & Recovery

| Failure | Impact | Recovery |
|---|---|---|
| **API Down (NewsAPI)** | Can't fetch new signals | Use cached data (24h old) |
| **Database Down** | Can't persist or retrieve | Return cached data only |
| **Cache Down (Redis)** | Slower (no cache), but works | Fall back to DB queries |
| **NLP Model crash** | Can't extract entities | Skip extraction, store raw text |
| **Gemma cannot fit/init on GPU (4 GB VRAM)** | No reasoning output | Provider chain fallback: Gemma → Grok (xai/auto) → BART degraded factual → source-linked signal + human-review flag; dashboard stays alive (FR-2.2.3B, Master Plan §14.1) |
| **Embedding model fail** | No semantic search | Fall back to pg_trgm keyword search (same DB) |
| **LangGraph node fails** | Pipeline stalls | Retry node, fall back to cached partial state |
| **Confluence engine error** | No confluence alerts | Log, serve signals normally (alerts skip, not crash) |
| **Lifecycle tracker error** | No state transitions | Log, serve signals without lifecycle stage (timeline empty, not crash) |
| **Red-Team NLI error** | No contradiction flags | Log, serve signals without flags (skip, not crash); flags never block signal delivery |
| **Missing-Signal scan error** | No missing alerts | Log, serve signals normally (missing-signal is advisory only) |
| **All fail** | Complete outage | Return empty set gracefully |

### 5.2 Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),           # Max 3 retries
    wait=wait_exponential(multiplier=1, min=2, max=10),  # 2s, 4s, 8s
    reraise=True  # Raise if all retries fail
)
async def fetch_newsapi():
    """Auto-retry with exponential backoff"""
    return await fetch("https://newsapi.org/...")

# Usage: Call once, retries automatic
try:
    articles = await fetch_newsapi()
except Exception:
    logger.error("NewsAPI failed after 3 retries")
    articles = await get_cached_articles()  # Fallback
```

---

## **6. SECURITY DESIGN**

### 6.1 Authentication & Authorization

```python
# API Authentication (JWT)
@app.post("/auth/login")
async def login(email: str, password: str):
    user = await db.get_user(email)
    if not verify_password(password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    
    token = create_access_token(
        data={"sub": user.id, "role": user.role},
        expires_delta=timedelta(hours=24)
    )
    return {"access_token": token}

# Route protection
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    
    return await db.get_user(user_id)

# Role-based access control
@app.get("/api/v1/signals")
async def get_signals(current_user: User = Depends(get_current_user)):
    # User can only see data for their role
    if current_user.role == "medical_affairs":
        # Return only medical_affairs signals
        return await db.get_signals_for_role("medical_affairs")
```

### 6.2 Input Validation

```python
from pydantic import BaseModel, validator

class SignalQuery(BaseModel):
    role: str
    limit: int = 20
    offset: int = 0
    
    @validator('limit')
    def limit_range(cls, v):
        if not 1 <= v <= 100:
            raise ValueError('limit must be 1-100')
        return v
    
    @validator('role')
    def role_valid(cls, v):
        if v not in ['medical_affairs', 'regulatory', 'commercial']:
            raise ValueError('invalid role')
        return v
```

---

## **7. TESTING STRATEGY**

### 7.1 Test Pyramid

```
      ▲
     ╱ ╲          E2E Tests (5%)
    ╱   ╲         - Full flow: API → DB → Cache
   ╱─────╲
  ╱       ╲       Integration Tests (25%)
 ╱         ╲      - Service interactions
╱───────────╲     - API → Database
      │      ╲    - Cache operations
      │       \
      │        Unit Tests (70%)
      │        - Functions, methods
      │        - Entity extraction
      │        - Scoring algorithms
      │        - Validators
```

### 7.2 Test Examples

```python
# Unit test: Entity extraction (haemophilia)
@pytest.mark.asyncio
async def test_extract_drug_names():
    text = "Roche's emicizumab (Hemlibra) shows durable bleed control in Haemophilia A"
    entities = await nlp_service.extract_entities(text)
    assert "emicizumab" in entities['drugs']
    assert "Hemlibra" in entities['brands']
    assert "Roche" in entities['companies']

# Integration test: Full signal processing
@pytest.mark.asyncio
async def test_process_signal_end_to_end():
    raw_signal = {"source": "pubmed", "text": "..."}
    result = await processor.process_signals([raw_signal])
    
    assert result[0]['entities'] is not None
    assert result[0]['relevance_score'] > 0
    assert result[0]['id'] in db

# Unit test: Confluence detection (Analysis 1, core differentiator, haemophilia)
@pytest.mark.asyncio
async def test_confluence_detection():
    signals = generate_signals(entity="Hemgenix",
                               types=["regulatory", "congress_publication", "patient_access"])
    event = await confluence_engine.detect_confluence(signals, "Hemgenix")
    assert event["alert_level"] == "CRITICAL"
    assert event["signal_count"] == 3

# Unit test: Lifecycle tracking (Analysis 2)
@pytest.mark.asyncio
async def test_lifecycle_advance():
    tracker = SignalLifecycleTracker(db)
    for signal, expected in [("phase3_readout", "results_in"),
                             ("submission_press", "under_review")]:
        chain = await tracker.advance(signal, entity="mim8")
        assert chain["state"] == expected
    timeline = tracker.timeline("mim8")
    assert timeline == sorted(timeline, key=lambda e: e["published_at"])

# Unit test: Red-Team contradiction detection (Analysis 3)
@pytest.mark.asyncio
async def test_red_team_contradiction():
    a = signal("sustained 3-year Factor IX efficacy", entity="Hemgenix", date="2026-01-10")
    b = signal("declining Factor IX expression in subset", entity="Hemgenix", date="2026-01-25")
    found = await red_team_engine.detect_contradictions([a, b], "Hemgenix")
    assert any(c["contradiction_score"] > 0.6 for c in found)
    assert all(c["claim_a"]["url"] and c["claim_b"]["url"] for c in found)

# Unit test: Missing-signal detection (Analysis 4)
@pytest.mark.asyncio
async def test_missing_signal_detector():
    lc = lifecycle(entity="mim8", last_event_date=now - timedelta(days=200))
    alerts = list(await missing_signal_detector.detect_missing_signals([lc]))
    assert alerts and alerts[0]["days_since_last_signal"] == 200
    assert alerts[0]["confidence"] > 0.4     # confidence grows with silence

# Unit test: Ontology enrichment resolves brand → molecule → company (haemophilia)
def test_ontology_enrichment():
    signal = extract_entities({"text": "Hemlibra shows inhibitor-agnostic efficacy"})
    enriched = ontology_service.enrich_signal(signal)
    assert enriched["context"]["drug_class"] == "Bispecific antibody"
    assert enriched["context"]["manufacturer"] == "Roche/Genentech"
    assert enriched["context"]["novo_competitor"] is True

# Unit test: Stakeholder Calibration recalibrates weights (HITL, NEW v2.0)
@pytest.mark.asyncio
async def test_stakeholder_calibration():
    svc = StakeholderCalibrationService(db)
    for _ in range(MIN_FEEDBACK_PER_ROLE + 5):
        await svc.submit_feedback(signal_id=u, role="regulatory",
                                  rating=2, reason="wrongly routed", user_id="reg_persona")
    result = await svc.recalibrate("regulatory")
    assert result["status"] == "recalibrated"
    assert result["new"]["regulatory_milestone"] > result["old"]["regulatory_milestone"]
    # WORM: feedback rows are immutable
    with pytest.raises(Exception):
        await db.execute("DELETE FROM stakeholder_feedback WHERE role='regulatory'")

# Unit test: Calibration summary reflects persona feedback
@pytest.mark.asyncio
async def test_calibration_summary():
    summary = await svc.summary()
    assert "regulatory" in summary
    assert summary["regulatory"]["feedback_count"] >= MIN_FEEDBACK_PER_ROLE
    assert summary["regulatory"]["avg_rating"] > 0

# Unit test: Traceable insight includes full evidence chain
def test_traceable_insight():
    insight = TraceableInsight()
    insight.add_source(signal_a); insight.add_source(signal_b)
    result = insight.generate()
    assert result["source_count"] == 2
    assert all(s["url"] for s in result["sources"])

# Unit test: F-I-S classification + evidence-sufficiency gate (kickoff-aligned)
def test_fis_and_evidence_sufficiency():
    fact_signal = signal("Company X announced a Phase III trial", evidence=[source_a])
    assert classify_fis(fact_signal) == "fact"
    weak_signal = signal("Public discussion may indicate increasing interest", evidence=[])
    assert classify_fis(weak_signal) == "speculation"
    assert evidence_sufficiency_check(weak_signal) is False
    assert generate_grounded_interpretation(weak_signal) == \
        "Insufficient evidence to support an interpretation."

# E2E test: Dashboard API call
def test_dashboard_api_response():
    response = client.get("/api/v1/signals?role=medical_affairs")
    assert response.status_code == 200
    assert len(response.json()['signals']) <= 20
```

---

## **8. DEPLOYMENT ARCHITECTURE**

### 8.1 Container Structure

```dockerfile
# Dockerfile (single image, all-in-one)
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Model weights live in the mounted /models volume (HF_HOME=/models, set at build AND runtime)
ENV HF_HOME=/models
# Download ML models at build time (cached in volume)
RUN python -m spacy download en_core_sci_md
RUN python -c "from transformers import pipeline; \
    pipeline('summarization', model='facebook/bart-large-cnn'); \
    pipeline('zero-shot-classification', model='facebook/bart-large-mnli')"
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
# Optional (larger image): pre-download the local reasoning LLM so the demo never hits
# a first-run download — if omitted, the model downloads on first run or the
# pipeline falls back through the provider chain (Gemma → Grok in xai/auto → BART degraded factual mode; Master Plan §13.6):
# RUN python -c "from transformers import pipeline; pipeline('text-generation', model='google/gemma-3-4b-it')"
# Model weights are mounted from the /models volume (HF_HOME=/models) — the application image
# stays small and the demo does not re-download multiple GB on every start (Master Plan §14.14).

# Copy source
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
```

### 8.2 Docker Compose (Local/Demo) — 4 services, Weaviate removed, Celery removed

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/metaradar
      - REDIS_URL=redis://redis:6379
      - NEWSAPI_KEY=xxx
      - HF_HOME=/models          # model weights persist in a mounted volume (Master Plan §14.14)
    volumes:
      - models_data:/models      # app starts without re-downloading multiple GB of weights
    depends_on: [postgres, redis]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/ready')"]
      interval: 30s
      timeout: 10s
      retries: 5

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on: [backend]

  postgres:
    image: pgvector/pgvector:pg16        # PostgreSQL 16 + pgvector in ONE image
    environment:
      - POSTGRES_USER=metauser
      - POSTGRES_PASSWORD=metapass
      - POSTGRES_DB=metaradar
    command: ["postgres", "-c", "shared_preload_libraries=vector"]
    ports: ["5432:5432"]
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U metauser -d metaradar"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  models_data:                    # model weights volume (separate from the application image)
```

**Note:** Weaviate removed entirely (Refined Architecture simplification); **Celery removed** (single in-process APScheduler, Master Plan §14.9). Vector search = pgvector extension inside PostgreSQL. `depends_on` is complemented by healthchecks — a dependency is only considered ready when its healthcheck passes.

**Note:** Weaviate removed entirely (Refined Architecture simplification). Vector search = pgvector extension inside PostgreSQL. One fewer container = faster, more reliable demo setup.

---

## **9. MONITORING & OBSERVABILITY**

### 9.1 Metrics to Track

```python
# Performance metrics
- API response time (p50, p95, p99)
- Database query time
- Cache hit/miss rate
- Signal processing throughput (signals/min)
- Confluence detection latency (per scan)
- RAG query latency (Ask Athena)

# Business metrics
- Signals ingested/day
- Entity extraction accuracy (B.Pharm QA-validated)
- F-I-S label accuracy (B.Pharm-validated ground truth)
- Evidence-sufficiency gate triggers/day (insufficient → facts-only + human review)
- Digest items/week + per-function coverage (six primary functions)
- Confluence events/day + alert-level distribution
- Lifecycle chains tracked + state transition accuracy (B.Pharm-validated)
- Contradiction flags/day + precision (human-confirmed false positive rate)
- Missing-signal alerts/day + timeliness vs false-positive rate (confidence thresholds)
- Relevance score distribution
- Data freshness (age of oldest signal)

# Calibration metrics (HITL, NEW v2.0)
- Feedback submissions/day + per-role distribution
- Routing accuracy trend per role (avg rating over time)
- Weight drift per role × signal_type after recalibration
- Confidence-score uplift (pre- vs post-calibration) in Q3 role badges
- Recalibration frequency + trigger reasons (audited in calibration_history)

# Health metrics
- Uptime percentage
- Error rate (5xx responses)
- Rate limit violations
- API source availability
- LangGraph node failure rate
```

### 9.2 Structured Logging

```python
# Loguru structured logging (Refined Architecture choice)
from loguru import logger
logger.info(
    "signal_processed",
    signal_id="uuid-xxx",
    source="pubmed",
    entities_count=5,
    relevance_score=0.92,
    processing_time_ms=145,
)

# Confluence event logging
logger.info(
    "confluence_event_detected",
    entity="Hemgenix",
    alert_level="CRITICAL",
    signal_count=3,
    signal_types=["regulatory", "congress_publication", "patient_access"],
)

# Calibration event logging (HITL, NEW v2.0)
logger.info(
    "calibration_recalibrated",
    role="regulatory",
    old_weight=0.62,
    new_weight=0.84,
    feedback_count=12,
    trigger="stakeholder_feedback_batch",
)
```

---

## **10. SCALABILITY ROADMAP**

**Phase 1 (Hackathon):**
- Single backend instance
- Single PostgreSQL instance
- 3000 signals/day

**Phase 2 (Production):**
- API behind load balancer (3-5 instances)
- PostgreSQL read replicas
- 10,000 signals/day
- Multi-tenant support

**Phase 3 (Enterprise):**
- Horizontal scaling (Kubernetes)
- Database sharding by role/source
- 100,000 signals/day
- Real-time streaming (Kafka)

---

## **11. DESIGN VS. JUDGING CRITERIA MAPPING**

This design is explicitly engineered against the Novo Nordisk judging criteria (see Novo Nordisk Analysis doc):

| Criterion (Weight) | Design Element |
|---|---|
| **Innovation (25%)** | The **Five Advanced Analyses** — Confluence Engine (2.4), Signal Lifecycle Tracker (2.4), Red-Team Contradiction Engine (2.4), Missing-Signal Detector (2.4), Stakeholder Calibration Loop / HITL (2.4) — plus Pharma Ontology enrichment (2.4) and Traceable Reasoning (2.4). No open-source tool combines these |
| **Technical (25%)** | LangGraph 10-agent orchestration incl. lifecycle/red-team/missing-signal/calibration agents (2.3), pgvector hybrid search (2.6), Docker Compose 1-command deploy (8.2), graceful failure modes (5.1) |
| **Business Impact (20%)** | Detects haemophilia paradigm shift (IV factor → subcutaneous non-factor → single-dose gene therapy); confluence alerts give Medical Affairs/Commercial a head start on mim8 positioning vs emicizumab and on Hemgenix/Roctavian gene-therapy disruption; missing-signal detection catches silent readouts and stalled submissions (see SRS 6.4) |
| **Feasibility (15%)** | Free APIs + local models (Gemma 3 4B Q4 on the RTX 3050 4 GB GPU; BART/spaCy/MiniLM on CPU — NLI reuses BART-MNLI, zero extra download), pgvector (one less container), public data sources (CDA-compliant), MVP → production path (10) |
| **Presentation (15%)** | B.Pharm owns haemophilia ontology + confluence/lifecycle clinical validation; CSE owns architecture; demo = `docker-compose up` + live Four-Question dashboard + live calibration / contradiction / missing-signal demos |

**Key differentiators over existing open-source tools (Refined Architecture doc):**
1. Confluence detection (not aggregation)
2. Pharma ontology (B.Pharm-built, knows Hemlibra = emicizumab = Roche competitor; Alhemo = concizumab = Novo Nordisk asset)
3. Traceable intelligence (regulatory-grade audit trail)
4. Temporal pattern recognition (gene therapy milestone parade / regulatory filing surge)
5. Role-specific narratives (not one report for everyone)
6. Free stack, zero vendor lock-in
7. **Stakeholder Calibration Loop (HITL)** — routing weights improve with persona feedback
8. **Signal Lifecycle Tracking** — every development has a chronological state machine with an expected next event
9. **Red-Team Contradiction Analysis** — contradicting claims on the same entity are flagged with both evidence chains
10. **Missing-Signal Detection** — absence of an expected signal becomes an early-warning alert

