# MetaRadar: Software Requirements Specification (SRS)

**Project:** MetaRadar - Real-Time Metabolic Disease Competitive Intelligence Platform  
**Version:** 1.0  
**Date:** July 26, 2026  
**Organization:** MS Ramaiah Institute of Technology (MSRIT)  
**Hackathon:** Novo Nordisk GBS Hackathon 2026  
**Problem Statement:** #3 - From Inbox Noise to Strategic Signal: AI-Powered Competitive Intelligence & Market Evolution Radar for Metabolic Disease

---

## **1. INTRODUCTION**

### 1.1 Purpose
MetaRadar detects early market signals in obesity, diabetes, and GLP-1 therapies by converting fragmented external information (news, clinical literature, social media, regulatory filings) into role-specific, actionable intelligence for Novo Nordisk teams.

### 1.2 Scope
**MVP Scope (Weeks 1-3):**
- Primary role: Medical Affairs
- Two data sources: NewsAPI, PubMed
- Core features: Signal fetch, entity extraction, pharma ontology enrichment, signal confluence detection, role-relevance scoring, traceable reasoning, dashboarding
- Agent orchestration: LangGraph multi-agent pipeline (ingest → validate → NLP → confluence → synthesize → brief)

**Extended Scope (Week 4):**
- One additional business role (Regulatory OR Commercial)
- OR one additional data source (Reddit sentiment analysis OR ClinicalTrials.gov)
- OR conversational search ("Ask Athena" RAG)
- OR narrative synthesis intelligence briefs

### 1.3 Definitions & Acronyms
- **Signal:** Any piece of information (article, social post, clinical trial result) relevant to competitive intelligence
- **Entity:** Named item (drug name, company name, clinical condition)
- **Role:** Functional team (Medical Affairs, Regulatory, Commercial, Market Access)
- **Velocity:** Rate of change (e.g., signal mentions increasing over time)
- **Relevance Score:** ML-generated importance metric (0.0 to 1.0)
- **Confluence:** Detection that multiple independent signal types converge on the same entity within a time window → elevated alert
- **Pharma Ontology:** Domain knowledge graph (drug → brand → mechanism → manufacturer → competitor) maintained by B.Pharm team
- **Traceable Insight:** Intelligence output with a complete evidence chain (which source → which signal → why it matters)
- **Narrative Synthesis:** LLM-generated executive brief that summarizes what happened, why it matters, and a recommended action
- **Temporal Pattern:** Recognition of which stage of a competitive timeline (e.g., pre-approval surge) current signals match
- **RAG:** Retrieval-Augmented Generation (LLM + vector database)
- **NLP:** Natural Language Processing (entity extraction, sentiment)

### 1.4 References
- Novo Nordisk GBS Hackathon 2026 Problem Statements
- Confidentiality Agreement between MS Ramaiah and Novo Nordisk
- Refined Architecture & GitHub Landscape Analysis (doc 5)
- Novo Nordisk Company Analysis & Hackathon Intelligence (doc 6)
- Architecture documents (Docker, Next.js 15, FastAPI, LangGraph, PostgreSQL + pgvector)

---

## **2. FUNCTIONAL REQUIREMENTS**

### 2.1 Signal Ingestion & Aggregation

**FR-2.1.1: Multi-Source Data Fetch**
- System SHALL fetch signals from at least 2 data sources (NewsAPI, PubMed)
- System SHALL support async parallel fetching (not sequential)
- System SHALL implement rate limiting per source (500/day for NewsAPI)
- System SHALL cache fetched data for 2 hours minimum

**FR-2.1.2: Error Handling & Fallback**
- If any source fails, system SHALL NOT crash
- System SHALL fall back to cached data (up to 24 hours old)
- System SHALL return empty set gracefully if no cache available
- System SHALL log all failures with timestamp and error details

**FR-2.1.3: Data Deduplication**
- System SHALL identify and remove duplicate signals across sources
- Duplicates identified by > 80% semantic similarity in titles
- When duplicate found, keep signal with highest relevance score

**FR-2.1.4: Data Validation**
- System SHALL reject signals with:
  - Missing required fields (source, text, timestamp)
  - Text < 50 characters (likely clickbait)
  - Detected language ≠ English
  - Semantic duplicate of recent signal
- System SHALL assign quality score (0.0-1.0) to each signal

### 2.2 NLP & Entity Extraction

**FR-2.2.1: Named Entity Recognition (NER)**
- System SHALL extract:
  - Drug names (e.g., "semaglutide", "GLP-1")
  - Company names (e.g., "Novo Nordisk", "Eli Lilly")
  - Indications (e.g., "obesity", "type 2 diabetes")
  - Clinical phases (e.g., "Phase 2b", "FDA approval")
- Extraction SHALL use local spaCy model (no API calls)
- Extraction accuracy target: > 90%

**FR-2.2.2: Signal Classification**
- System SHALL classify each signal as one of:
  - Clinical success (new trial results, efficacy data)
  - Safety concern (adverse events, post-market surveillance)
  - Competitive move (product launches, pricing changes)
  - Regulatory change (FDA approval, guideline update)
  - Access issue (reimbursement decision, supply constraint)

**FR-2.2.3: Text Summarization**
- System SHALL generate 1-line (< 50 character) summary of each signal
- Summarization SHALL use local BART model (no API calls)
- Summary SHALL preserve key entities and metrics

**FR-2.2.4: Pharma Ontology Enrichment**
- System SHALL maintain a local pharma ontology (JSON) mapping: drug → brand names → mechanism → manufacturer → indications → competitor drugs
- Ontology SHALL be authored and validated by the B.Pharm team
- Every extracted entity SHALL be cross-referenced against the ontology (e.g., "Wegovy" → semaglutide → GLP-1 agonist → Novo Nordisk)
- When an extracted drug belongs to a competitor of Novo Nordisk, the signal SHALL be flagged as a competitive signal at zero extra API cost
- Signals with extracted entities that fail ontology validation SHALL be flagged for B.Pharm QA review

### 2.3 Signal Scoring & Ranking

**FR-2.3.1: Relevance Scoring**
- System SHALL compute relevance score (0.0-1.0) based on:
  - Source credibility (PubMed=0.95, Reddit=0.40, etc.)
  - Entity match (drug/company relevance to portfolio)
  - Pharma keyword density
  - Indication match (obesity/diabetes focus)
- Score SHALL be transparent (show scoring factors to user)

**FR-2.3.2: Micro-Trend Velocity Detection**
- System SHALL detect signals with accelerating mention frequency
- If mention count grows > 50% daily for 3+ days = HIGH velocity flag
- HIGH velocity signals promoted to top of dashboard

**FR-2.3.3: Role-Specific Relevance**
- System SHALL compute per-role relevance (Medical Affairs, Regulatory, Commercial, etc.)
- Medical Affairs cares about: clinical efficacy, safety, HCP sentiment
- Regulatory cares about: FDA decisions, post-market studies, guidelines
- Each signal shows per-role score (0.0-1.0)

**FR-2.3.4: Signal Confluence Detection**
- System SHALL detect when ≥ 2 independent signal types converge on the same entity within a 48-hour window
- Confluence alert levels SHALL follow the matrix: {regulatory+clinical+social} → CRITICAL; {clinical+competitive} / {regulatory+competitive} → HIGH; {social+clinical} → MEDIUM; single type → LOW
- Each confluence event SHALL produce ONE consolidated alert with constituent signals and a synthesized story summary
- Confluence alerts SHALL be promoted to the top of the dashboard regardless of individual signal scores
- Confluence rules SHALL be validated by the B.Pharm team for clinical sense

**FR-2.3.5: Temporal Pattern Recognition**
- System SHALL match current signal patterns against known competitive timelines (pre-approval surge, access crisis)
- For a matched pattern, system SHALL report: pattern name, current stage, predicted next stage, confidence
- Timeline stage definitions (e.g., Phase 3 results → FDA advisory → PDUFA) SHALL be authored by the B.Pharm team
- Matched patterns SHALL surface as predictive alerts (e.g., "Competitor drug following pre-approval signal trajectory")

**FR-2.3.6: Traceable Reasoning (Explainable Intelligence)**
- Every insight/alert SHALL include a complete evidence chain: source name → original URL → publication timestamp → text excerpt → extracted entities
- System SHALL expose the reasoning behind each score and alert (which signals, how many, which platforms)
- Regulatory-grade audit trail SHALL be exportable per insight
- System SHALL NOT present an insight without a traceable source chain

### 2.4 Dashboard & Visualization

**FR-2.4.1: Role-Specific Dashboard**
- System SHALL display signals filtered by user's assigned role
- Medical Affairs dashboard shows:
  - High-relevance clinical signals (score > 0.7)
  - Competitor clinical trial announcements
  - HCP sentiment on new therapies (if social data available)
  - Sorted by recency and relevance
- Signal card displays:
  - Title (original source headline)
  - Summary (1-line AI-generated)
  - Source name + publication date
  - Relevance score (with breakdown)
  - Entity tags (drugs, companies, indications)

**FR-2.4.2: Trend Visualization**
- System SHALL show:
  - Line chart: Signal volume over last 7 days (by entity/category)
  - Heatmap: Signal volume by competitor + indication
  - Word cloud: Most mentioned terms in signals
  - Updates automatically as new signals arrive

**FR-2.4.3: Search & Filter**
- System SHALL support filtering by:
  - Date range (last 24h, 7d, 30d, custom)
  - Entity (drug name, company, indication)
  - Source type (clinical, news, regulatory)
  - Relevance score threshold
- Search SHALL use keyword + semantic similarity (hybrid search)

**FR-2.4.4: Responsive Design**
- Dashboard SHALL render correctly on:
  - Desktop (1920x1080)
  - Tablet (1024x768)
  - Mobile (375x667)
- Load time (cached): < 500ms
- Load time (cold): < 3 seconds

**FR-2.4.5: Narrative Intelligence Briefs**
- System SHALL synthesize all signals about an entity/topic into a 3-part executive brief: WHAT HAPPENED / WHY IT MATTERS / RECOMMENDED ACTION
- Briefs SHALL be role-specific (Medical Affairs sees clinical implications; Regulatory sees compliance impact)
- Each brief SHALL be grounded in traceable sources (cite signal counts, never speculate beyond evidence)
- Weekly competitive briefs SHALL cover the previous 7 days

**FR-2.4.6: Natural Language Query ("Ask Athena" Lite)**
- System SHALL accept natural-language questions (e.g., "What is Eli Lilly doing with oral GLP-1?")
- Answers SHALL be generated using RAG over the signal store (hybrid search: semantic + keyword, alpha=0.6)
- Answers SHALL cite supporting signals (top 3) and report retrieval confidence
- If insufficient signals exist, system SHALL return "Insufficient signals in last 7 days"
- Query responses SHALL be role-scoped (users only query data their role can access)

### 2.5 Data Storage & Retrieval

**FR-2.5.1: Primary Database (PostgreSQL)**
- System SHALL store:
  - signals table: raw signal data + metadata
  - entities table: extracted drug/company/indication references
  - trending_scores table: velocity metrics over time
  - role_relevance table: per-role importance scores
- Queries SHALL use indexes for performance (< 100ms)

**FR-2.5.2: Vector Search (pgvector in PostgreSQL)**
- System SHALL store signal embeddings (768-dim, sentence-transformers/all-MiniLM-L6-v2) as pgvector columns inside PostgreSQL
- Hybrid search SHALL combine:
  - Dense vector similarity (semantic meaning, pgvector)
  - Sparse keyword matching (exact matches, pg_trgm + FTS)
- Query response time: < 1 second for 10K signals
- No separate vector database container is required (eliminates one service)

**FR-2.5.3: Cache Layer (Redis)**
- System SHALL cache:
  - Dashboard data (2 hour TTL)
  - API responses (per source rate limit window)
  - User session data
- Redis hit rate target: > 80%

### 2.6 User Authentication & Authorization

**FR-2.6.1: Role-Based Access Control (RBAC)**
- System SHALL enforce role-based data access:
  - Medical Affairs: See clinical/safety data only
  - Regulatory: See regulatory/compliance data only
  - Admin: See all data
- Access enforcement on API layer (not UI only)

**FR-2.6.2: Session Management**
- System SHALL issue JWT tokens on login (24 hour expiry)
- System SHALL validate token on every API call
- System SHALL handle token expiration gracefully

### 2.7 Monitoring & Logging

**FR-2.7.1: Structured Logging**
- System SHALL log all operations with:
  - Timestamp (ISO 8601)
  - Operation name
  - Status (success/failure)
  - Duration (if performance-critical)
  - Error details (if failed)
- Logs retained for 30 days minimum
- Log format: JSON (for easy parsing)

**FR-2.7.2: Performance Monitoring**
- System SHALL track:
  - API response times (per endpoint)
  - Database query times
  - Cache hit/miss rates
  - Data freshness (age of oldest signal)
- Alerts triggered if:
  - API response > 3 seconds
  - Error rate > 5%
  - Cache hit rate < 60%

---

## **3. NON-FUNCTIONAL REQUIREMENTS**

### 3.1 Performance Requirements

| Metric | Target | Rationale |
|---|---|---|
| Dashboard load (cached) | < 500ms | Real-time feel |
| Dashboard load (cold) | < 3s | Acceptable wait |
| API single request | < 200ms | Responsive UI |
| Full data refresh (all sources) | < 5s | Reasonable background task |
| Search/filter | < 1s | User interaction feel |
| Database query (indexed) | < 100ms | 10K signals max |

### 3.2 Scalability Requirements

**Current Scale (Hackathon):**
- 3,000 signals/day ingested
- 5 concurrent users
- 2-month data retention

**Future Scale (Production):**
- 10,000+ signals/day (10 sources)
- 100+ concurrent users
- 1-year data retention
- Multi-tenant capability

**Architecture supports scaling via:**
- Horizontal scaling (multiple API instances behind load balancer)
- Database replication (PostgreSQL read replicas)
- Caching at edge (Vercel Edge Network for frontend)
- Async task workers (Celery/Redis for background jobs)

### 3.3 Availability & Reliability

- **Uptime SLA:** > 99% (graceful degradation acceptable)
- **Data Loss:** Zero tolerance (backups, transactions)
- **Backup Strategy:** Daily automated PostgreSQL dumps to cloud storage
- **Disaster Recovery:** Full system restore possible within 1 hour

### 3.4 Security Requirements

- **Data in Transit:** HTTPS/TLS 1.3 for all API calls
- **Data at Rest:** PostgreSQL encryption at rest (optional for hackathon)
- **API Authentication:** JWT tokens (RS256 signing)
- **Input Validation:** All user inputs sanitized (SQL injection, XSS protection)
- **Rate Limiting:** Per-user request rate limits (100 req/min)
- **Logging:** No sensitive data (passwords, tokens) logged

### 3.5 Usability Requirements

- **Learning Curve:** New user productive within 5 minutes
- **Onboarding:** In-app tutorial for first-time users
- **Accessibility:** WCAG 2.1 AA compliance (keyboard navigation, screen reader support)
- **Documentation:** User guide + API docs auto-generated from code

### 3.6 Maintainability & Code Quality

- **Test Coverage:** > 80% of critical paths
- **Code Style:** Black formatter + flake8 linter (Python), Prettier (JavaScript)
- **Documentation:** Docstrings for all functions, API endpoint comments
- **Version Control:** Git with conventional commits
- **CI/CD:** Automated tests on every push, deploy on merge to main

---

## **4. DATA REQUIREMENTS**

### 4.1 Data Sources

| Source | Type | Update Frequency | Cost |
|---|---|---|---|
| NewsAPI | Industry news | Real-time | Free (500/day) |
| PubMed | Clinical literature | Real-time | Free |
| Twitter API | Social signals | Real-time | Free (academic) |
| Reddit | Patient/HCP sentiment | Real-time | Free |
| FDA | Regulatory | Weekly | Free |
| ClinicalTrials.gov | Trial intelligence | Weekly | Free (Week 4) |
| Company websites | Competitor news | Weekly | Free |

### 4.2 Data Storage Requirements

```
PostgreSQL (incl. pgvector extension):
├─ signals table:           1M rows × 5KB = 5GB
├─ entities table:          500K rows × 1KB = 500MB
├─ trending_scores table:   50K rows × 2KB = 100MB
├─ role_relevance table:    100K rows × 3KB = 300MB
└─ signal embeddings:       1M × 768 dims × 4 bytes = 3GB
= ~9GB total (vector search in the same database)

Redis (cache):
├─ Hot signals:             100K × 2KB = 200MB
├─ API responses:           50MB
└─ User sessions:           10MB
= ~260MB total

Disk Archive:
└─ 2 months × 50MB/day = ~3GB

TOTAL: ~12GB (well within single server limits)
```

### 4.3 Data Quality Metrics

- **Accuracy:** > 90% (entity extraction correctly identifies drugs/companies)
- **Completeness:** > 95% (required fields present for > 95% of signals)
- **Timeliness:** < 2 hours old (difference between signal creation and ingestion)
- **Consistency:** Duplicate drug names standardized (e.g., "Ozempic" = "semaglutide")

---

## **5. INTERFACE REQUIREMENTS**

### 5.1 User Interface

**Dashboard Layout:**
```
┌─────────────────────────────────────┐
│     MetaRadar - Medical Affairs     │  Header
├─────────────────────────────────────┤
│ [Date Range] [Entity Filter] [Search] │  Controls
├─────────────────────────────────────┤
│ Trend Chart (7-day signal volume)    │  Visualization
├─────────────────────────────────────┤
│ Signal Feed (sorted by score)        │  Main Content
│ ┌──────────────────────────────────┐ │
│ │ [High] Clinical Trial: GLP-1 ...  │ │
│ │ Source: Reuters | Score: 0.92     │ │
│ │ Entities: semaglutide, Novo N...  │ │
│ └──────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Key UI Components:**
- Date range picker (calendar)
- Multi-select filters (entity, source, type)
- Search bar (keyword + semantic)
- Trend charts (Recharts)
- Signal cards (title, summary, metadata)
- Loading states + error messages

### 5.2 API Interface

**REST Endpoints:**

```
GET /api/v1/signals
  Params: role, limit, offset, date_range, entity_filter
  Returns: 200 with paginated signal list

GET /api/v1/signals/{id}
  Returns: 200 with full signal details (incl. evidence chain)

GET /api/v1/trends
  Params: entity, days (default: 7)
  Returns: 200 with time-series signal volume

GET /api/v1/confluence
  Params: role, entity, window_hours (default: 48)
  Returns: 200 with confluence alerts (entity, level, constituent signals)

GET /api/v1/entities
  Params: type (drug|company|indication)
  Returns: 200 with list of entities

POST /api/v1/search
  Body: { query: "oral GLP-1" }
  Returns: 200 with search results

POST /api/v1/query
  Body: { question: "What is Eli Lilly doing with oral GLP-1?", role: "medical_affairs" }
  Returns: 200 with grounded answer + supporting signals (Ask Athena)

GET /api/v1/briefs
  Params: entity, days (default: 7)
  Returns: 200 with narrative intelligence brief (WHAT/WHY/ACTION)

GET /api/v1/health
  Returns: 200 if healthy, 503 if degraded
```

### 5.3 Notification Interface

- Dashboard refresh (WebSocket) when new signals arrive
- Email digest: Weekly summary for each role
- In-app alerts: High-velocity signals highlighted

---

## **6. CONSTRAINTS & ASSUMPTIONS**

### 6.1 Technical Constraints

- **Backend Language:** Python (FastAPI)
- **Agent Orchestration:** LangGraph (multi-agent state graph)
- **Frontend Framework:** Next.js 15 (React)
- **Database:** PostgreSQL 16 + pgvector (vector + relational in one DB)
- **Cache:** Redis
- **Task Queue:** Celery + Redis; APScheduler (2-hour fetch trigger)
- **Deployment:** Docker Compose (local/dev), Vercel + Render (production)
- **ML Models:** spaCy 3.7 (en_core_sci_md), facebook/bart-large-cnn (summarization), facebook/bart-large-mnli (zero-shot classification), sentence-transformers/all-MiniLM-L6-v2 (embeddings) — all free, open-source
- **No GPU required:** All models run on CPU (slower but free)

### 6.2 Business Constraints

- **Timeline:** 4 weeks (hackathon deadline)
- **Budget:** $0 (all free/open-source)
- **Team:** 2 CSE + 3 B.Pharm students
- **Scope:** MVP only (1 role, 2 sources, core features)

### 6.3 Assumptions

- **Internet connectivity:** Available during development (APIs require internet)
- **Demo environment:** Has Docker, Git, Python 3.11+
- **Data availability:** NewsAPI + PubMed remain free and stable
- **User expertise:** Medical/regulatory teams familiar with dashboards (not data scientists)
- **Confidentiality:** All signal data treated as Novo Nordisk confidential per CDA; public APIs only, no proprietary Novo Nordisk data

### 6.4 Business Context (Hackathon Alignment)

MetaRadar is designed against Novo Nordisk's current business reality (see Novo Nordisk Analysis doc) to maximize judged Business Impact:

- **Semaglutide patent expiry (India, Mar 20, 2026):** 12+ generic entrants (Sun Pharma, Torrent, Dr. Reddy's, Zydus). MetaRadar's confluence engine + market access signals give Commercial/Market Access a competitive head start.
- **Eli Lilly tirzepatide momentum:** Beat semaglutide in a 2024 head-to-head trial; gained share in Q1 2026. MetaRadar flags Lilly's oral GLP-1 (orforglipron) trajectory via temporal pattern recognition.
- **GBS AI mandate:** Novo Nordisk GBS Bangalore targets a two-thirds reduction in drug launch timelines using AI. MetaRadar demonstrates that intelligence infrastructure.
- **Judging alignment:** Innovation 25% (confluence + ontology + traceability), Technical 25% (LangGraph + pgvector + Docker), Business Impact 20% (above), Feasibility 15% (free stack, CPU-only, CDA-compliant), Presentation 15% (B.Pharm domain narration + CSE architecture narration).

---

## **7. ACCEPTANCE CRITERIA**

### 7.1 MVP Acceptance Criteria (Week 3)

- [ ] Dashboard loads in < 500ms (cached)
- [ ] All signals from NewsAPI + PubMed appear in feed
- [ ] Entity extraction works for drugs, companies, indications
- [ ] Pharma ontology enrichment resolves brand→molecule→company (e.g., "Wegovy" → semaglutide → Novo Nordisk)
- [ ] Confluence Engine produces ONE consolidated alert for ≥ 2 signal types on the same entity in 48h
- [ ] Every insight displays a traceable source chain (source → URL → excerpt)
- [ ] Role filtering works (Medical Affairs sees only relevant signals)
- [ ] 7-day trend chart displays correctly
- [ ] At least 1 integration test passes
- [ ] Docker Compose runs without errors (pgvector, no Weaviate)
- [ ] Fallback cache works when API fails
- [ ] At least 1 B.Pharm student can explain the domain logic

### 7.2 Extended Acceptance Criteria (Week 4)

- [ ] One bonus feature fully implemented (Reddit OR Regulatory OR Ask Athena OR narrative briefs)
- [ ] Temporal pattern matching flags a pre-approval or access-crisis trajectory
- [ ] Unit test coverage > 60% for critical paths
- [ ] Performance benchmarks met (see 3.1)
- [ ] Judges can run `docker-compose up` and see live demo
- [ ] Architecture diagram + code walkthrough documented
- [ ] Demo script includes failure scenarios (API down, etc.)
- [ ] Demo ties features to Novo Nordisk pain (patent expiry, Eli Lilly competition) for Business Impact score

### 7.3 Quality Metrics

- **Bug Severity:** No critical bugs (crashes) at demo
- **Code Quality:** No warnings from linter/type checker
- **Documentation:** README + API docs complete
- **User Feedback:** At least 2 faculty review and approve domain logic

---

## **8. GLOSSARY**

| Term | Definition |
|---|---|
| **Agentic AI** | AI system that autonomously takes actions without human intervention |
| **Confluence** | Multiple independent signal types converging on the same entity in a time window → elevated alert |
| **Embedding** | Vector representation of text (semantic meaning) |
| **Evidence Chain** | Audit trail linking an insight to its source signals, URLs, and excerpts |
| **Hybrid Search** | Combining semantic (vector) + keyword (lexical) search |
| **Knowledge Graph** | Graph database of entities and relationships |
| **LangGraph** | Framework for stateful multi-agent orchestration (state graph) |
| **LLM** | Large Language Model (GPT-4, BART, etc.) |
| **NER** | Named Entity Recognition (extract entities from text) |
| **Narrative Synthesis** | LLM generation of executive briefs (what / why / action) |
| **Ontology** | Domain hierarchy (drug → brand → mechanism → manufacturer → competitor) |
| **Payload** | Request/response body in API |
| **pgvector** | PostgreSQL extension enabling vector similarity search in the primary DB |
| **RAG** | Retrieval-Augmented Generation (fetch + generate) |
| **Relevance Score** | ML metric (0-1) indicating importance |
| **Temporal Pattern** | Recognition of competitive timeline stages (e.g., pre-approval surge) |
| **Traceability** | Ability to show which signals produced an insight |
| **Velocity** | Rate of change (e.g., mentions per day) |
| **Vector DB** | Database optimized for semantic similarity search (here: pgvector) |

---

## **9. REVISION HISTORY**

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-26 | Omprakash | Initial MVP specification |
| 1.1 | 2026-07-28 | Omprakash | Aligned with Refined Architecture: pgvector (replaces Weaviate), LangGraph orchestration, confluence engine, pharma ontology, traceable reasoning, temporal patterns, narrative briefs, Ask Athena; added Novo Nordisk business context + judging criteria |

