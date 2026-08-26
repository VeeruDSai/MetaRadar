# External & Internal Integrations (INTEGRATIONS.md)

**Project:** MetaRadar — Autonomous Decision Intelligence Platform  
**Milestone:** v5.2  
**Last Updated:** 2026-08-27  

---

## 1. External Ingestion Integrations

### Tier 1: Authoritative Public Registries
- **ClinicalTrials.gov API v2:**
  - Endpoint: `https://clinicaltrials.gov/api/v2/studies`
  - Auth: None (public API)
  - Method: Cursor-paginated GET requests
  - Output: Full protocol sections, intervention lists, sponsor modules
  - Canonical URL: `https://clinicaltrials.gov/study/{NCTId}`
- **NCBI PubMed E-Utilities:**
  - Endpoint: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` & `efetch.fcgi`
  - Rate Limit: Max 3 req/sec unauthenticated (enforced via async delay)
  - Output: Peer-reviewed article abstracts, authors, mesh terms, PMIDs
  - Canonical URL: `https://pubmed.ncbi.nlm.nih.gov/{PMID}/`
- **openFDA & FDA MedWatch:**
  - Endpoints: `https://api.fda.gov/drug/drugsfda.json` & MedWatch RSS
  - Output: Regulatory approvals, BLA numbers, safety alerts
  - Canonical URL: Record-specific Drugs@FDA document link
- **EMA Medicines RSS:**
  - Endpoint: `https://www.ema.europa.eu/en/medicines/rss`
  - Output: CHMP scientific opinions, EPAR product summaries, orphan designations
  - Canonical URL: Specific product EPAR URL (e.g. `https://www.ema.europa.eu/en/medicines/human/EPAR/roctavian`)

### Tier 3: Discovery & News Feeds
- **NewsAPI:**
  - Endpoint: `https://newsapi.org/v2/everything`
  - Auth: API Key (`NEWSAPI_KEY`) with 100 req/day quota tracking
  - Canonical URL: Direct `article.url` (landing pages blocked)
- **Fierce Pharma RSS:**
  - Endpoint: `https://www.fiercepharma.com/rss/xml`
  - Parsing: Stdlib `xml.etree.ElementTree` with domain keyword filtering
  - Canonical URL: Direct article `<link>`
- **Economic Times Pharma RSS:**
  - Endpoints: `https://pharma.economictimes.indiatimes.com/rss/topstories` & `.../drug_approvals`
  - Canonical URL: Direct article `<link>`
- **BioPharma Dive:**
  - Status: `configured_no_feed` (honest registry visibility without scraping)

---

## 2. Internal Service Integrations

```mermaid
graph TD
    Connectors[Source Connectors (7 Active)] -->|Verbatim Raw Data| Bronze[RawSignalBronze DB Table]
    Bronze --> Ingestion[Ingestion Engine & Deduplication]
    Ingestion --> LangGraph[11-Node LangGraph Intelligence Pipeline]
    LangGraph --> SignalsDB[(Signals & Evidence PostgreSQL)]
    SignalsDB --> VectorIndex[pgvector 384-dim Index]
    SignalsDB --> Routing[Routing & Escalation Engine]
    Routing --> ReviewQueue[Functional Review Queues]
    ReviewQueue --> AuditDB[(Immutable AuditLog)]
    SignalsDB --> Athena[Athena Clinical Q&A Engine]
    SignalsDB --> REST[FastAPI REST & SSE Endpoints]
    REST --> NextUI[Next.js 16 Workspace UI]
```

---

## 3. Workflow & Review Integration

- **State Persistence:** `POST /api/v1/signals/{id}/review` mutates `review_status`, `reviewed_by`, `review_decision`, and `resulting_action`.
- **Audit Logging:** Every review mutation creates an immutable `AuditLog` entry with timestamp, actor, and before/after metadata.
- **Demo Operator Persona:** Client `sessionStorage` provides the active operator persona across 6 functions (`Medical Affairs`, `Regulatory`, `Safety`, `Market Access`, `Communications`, `Leadership`).
- **Athena Context Injection:** `POST /api/v1/athena` passes scoped signal facts, interpretation, and evidence citations directly into LLM reasoning.
