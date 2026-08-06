# Architecture Research — MetaRadar

## System Components & Boundaries

### 1. Ingestion Layer
- **Components**: pi_fetcher.py, Celery tasks, APScheduler (2h cycle).
- **Resilience**: 	enacity retry logic + raw JSON persistence to aw_signals_bronze table before processing.

### 2. LangGraph Intelligence Graph
Stateful 6-node state graph orchestrating execution:
1. ingest: Fetch parallel API streams + deduplicate.
2. alidate: Score quality (>0.5 threshold) + strip PII.
3. 
lp: spaCy NER extraction + model-agnostic summarization.
4. confluence: Detect cross-source entity convergence within 48h window.
5. synthesize: Generate narrative executive briefs per role.
6. rief: Format role-specific output payloads.

### 3. Data & Storage Layer
- **PostgreSQL 16 + pgvector**: Stores aw_signals_bronze, signals, entities, confluence_events, riefs, udit_log.
- **Hybrid Search**: Semantic vector cosine distance + pg_trgm lexical trigram matching.
- **Redis 7**: Hot signal cache (2h TTL), API response cache, rate limiting.

### 4. API & Application Layer
- **FastAPI**: REST endpoints /api/v1/signals, /api/v1/confluence, /api/v1/query, /api/v1/briefs, /api/v1/health.
- **Audit Logger**: WORM logger intercepting administrative/user state edits.

### 5. Presentation Layer
- **Next.js 15 App Router**: Server-rendered dashboard, signal cards with <DisclaimerBadge />, confluence alerts view, and Ask Athena chat drawer.
