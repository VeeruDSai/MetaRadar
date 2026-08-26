# Technology Stack (STACK.md)

**Project:** MetaRadar — Autonomous Decision Intelligence Platform  
**Milestone:** v5.2 (Real Signal Workflow, Discovery Connectors & Demo Operator)  
**Last Updated:** 2026-08-27  

---

## 1. Core Frameworks & Runtimes

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend Framework** | Next.js (App Router, Turbopack) | `16.3.0` | Server/client component rendering, streaming, responsive layout |
| **Frontend Runtime** | React / React DOM | `^19.0.0` | UI component tree, optimistic updates, hooks |
| **Frontend Styling** | Tailwind CSS v4 + Custom Tokens | `^4.3.3` | Token-based theme system (`var(--surface)`, `var(--border)`, etc.) |
| **Animation & Charts** | Framer Motion & Recharts | `^13.1.0` / `^3.10.1` | Smooth micro-animations, counters, trend analysis charts |
| **Icons & UI Primitives**| Lucide React, Base UI, Shadcn | `^1.16.0` / `^1.5.0` | Semantic iconography, accessible primitives |
| **Backend Framework** | FastAPI (Python) | `^0.115.0` | High-performance asynchronous REST API & Server-Sent Events |
| **Backend Runtime** | Python (CPython) | `3.13.5` | Pipeline execution, data transformation, async event loop |
| **Pipeline Engine** | LangGraph / LangChain | `^0.2.0` | 11-node directed acyclic graph for signal processing |
| **ORM & Database Client**| SQLAlchemy 2.0 (Async) + asyncpg | `^2.0.36` / `^0.30.0` | PostgreSQL async session management, connection pooling |
| **Data Validation** | Pydantic v2 | `^2.10.0` | Strict schema validation, DTOs, domain config models |
| **Observability** | Structlog + asgi-correlation-id | `^24.4.0` / `^4.3.0` | Structured JSON logging, request tracing, secret scrubbing |

---

## 2. Data Storage & Search Infrastructure

| Component | Technology | Purpose |
|---|---|---|
| **Primary Relational DB** | PostgreSQL 16 | Relational storage for Signals, Bronze data, Audit Logs, Sources, Feedback |
| **Vector Search** | pgvector extension | 384-dimensional cosine distance semantic indexing |
| **Cache & Distributed Locks** | Redis 7 (or asyncpg advisory locks) | Fast caching, rate-limiting, scheduler concurrency control |
| **Local Embeddings** | SentenceTransformers / ONNX | Local 384-dim semantic embeddings for fast retrieval |

---

## 3. Connector & Data Ingestion Stack

| Source ID | Source Name | Freshness Class | Tier | Transport / Protocol |
|---|---|---|:---:|---|
| `clinical_trials` | ClinicalTrials.gov | `near_real_time` | 1 | REST API v2 (JSON with cursor pagination) |
| `pubmed` | NCBI PubMed | `batch` | 1 | E-Utilities API (XML parsing with rate limiter) |
| `fda` | Drugs@FDA / MedWatch | `adapter_ready` | 1 | openFDA REST API + FDA MedWatch RSS XML |
| `ema` | European Medicines Agency | `adapter_ready` | 1 | Official EMA Medicines RSS XML Feed |
| `newsapi` | NewsAPI Commercial News | `delayed` | 3 | NewsAPI `/v2/everything` REST JSON (Quota-aware) |
| `fierce_pharma` | Fierce Pharma | `delayed` | 3 | Official RSS Feed (`fiercepharma.com/rss/xml`) |
| `et_pharma` | ET Pharma | `delayed` | 3 | Top Stories & Drug Approvals RSS XML Feeds |
| `biopharmadive` | BioPharma Dive | `manual` | 3 | Configured without feed (`status: configured_no_feed`) |

---

## 4. LLM & Reasoning Stack

| Provider | Model | Mode | Privacy & Guardrails |
|---|---|---|---|
| **Local Gemma** | Gemma 3 (Ollama / Local Inference) | `reasoning` | Default offline local reasoning engine |
| **Grok (xAI)** | Grok-Beta / Grok-2 | `reasoning` | Optional cloud reasoning behind strict PII/PHI privacy gate |
| **Deterministic Fallback**| Factual Extraction & Scored Heuristics | `degraded_factual` | Guaranteed offline operation when LLMs are unreachable |
