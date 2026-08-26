# Codebase Concerns & Observations (CONCERNS.md)

**Project:** MetaRadar — Autonomous Decision Intelligence Platform  
**Milestone:** v5.2  
**Last Updated:** 2026-08-27  

---

## 1. Resolved Technical Debt & Hardening Accomplished

- **NewsAPI Provenance Repaired:** Replaced generic portal fallback with verified `article.url` and blocked registration landing pages.
- **Workflow State Persisted:** Evolved passive destination classification into a persistent database-backed review workflow with immutable `AuditLog` history.
- **Demo Operator Available:** Added 6-role non-auth persona selector for judges and stakeholders to test queue routing and decision actions.
- **Discovery Feeds Added:** Fierce Pharma and ET Pharma integrated as Tier 3 RSS discovery connectors. BioPharma Dive registered with honest `configured_no_feed` status.
- **Escalation Rules Improved:** Replaced single score threshold with compound strategic domain and inflection event rules.
- **Zero Banned Tailwind Classes:** 100% compliant with CSS token custom properties (`scripts/check-banned-classes.mjs`).

---

## 2. Active Areas for Future Enhancement

### A. Next Codegen Migration (Contract Sync)
- **Current State:** `scripts/export_openapi.py` re-emits a static template verbatim to `frontend/types/api.ts` to enforce CI diff gates.
- **Future Milestone:** Integrate `openapi-typescript` for automated end-to-end AST-based type generation directly from FastAPI OpenAPI JSON.

### B. Redis Cluster & Distributed Lock Scalability
- **Current State:** Ingestion scheduler uses PostgreSQL 31-bit advisory locks (`try_advisory_lock()`), which work reliably for single-instance or moderately scaled Postgres setups.
- **Future Milestone:** Transition to Redis distributed locks (`Redlock`) if running across multi-region stateless backend clusters.

### C. Rate Limiting Multi-Worker Sync
- **Current State:** NewsAPI 100 req/day quota is tracked per connector state in PostgreSQL.
- **Future Milestone:** Add centralized Redis sliding-window rate limiters across all external connector targets.
