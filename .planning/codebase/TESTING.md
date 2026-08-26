# Testing Strategy & Verification Gates (TESTING.md)

**Project:** MetaRadar — Autonomous Decision Intelligence Platform  
**Milestone:** v5.2  
**Last Updated:** 2026-08-27  

---

## 1. Test Suite Matrix

The automated backend test suite comprises **139 executable unit and integration tests** across 15 dedicated modules:

| Test File | Focus & Coverage | Test Count |
|---|---|:---:|
| `test_signal_routing_workflow.py` | Complete review state machine (`UNREVIEWED` → `IN_REVIEW` → `REVIEWED` → `ACTIONED`) & AuditLog | 3 |
| `test_provenance.py` | Provenance truthfulness, PubMed/NCT/EMA/FDA URL resolution, NewsAPI pass-through | 10 |
| `test_connector_health.py` | Connector health precedence, Fierce Pharma/ET Pharma registration, BioPharma Dive config | 5 |
| `test_ingestion.py` | PubMed, ClinicalTrials, NewsAPI, FDA, EMA connectors, deduplication, bronze persistence | 15 |
| `test_signals_endpoints.py` | Signal list, overview, filtering, Athena endpoint validation | 3 |
| `test_signal_decision_refinement.py` | Authority hierarchy, deterministic routing, leadership escalation, decision objects | 8 |
| `test_truthfulness_and_invariants.py` | Priority scoring determinism, time decay, secret scrubbing, correlation IDs | 7 |
| `test_retrieval.py` | pgvector 384-dim embeddings, hybrid search, exact ID match, provider fallback | 12 |
| `test_intelligence_nodes.py` | 11-node LangGraph pipeline steps, confluence, red team contradictions, missing signals | 13 |
| `test_redteam_behavior.py` | Contradiction evaluation, priority gating, rule matching | 3 |
| `test_privacy_boundary.py` | PII/PHI scrubber regex rules, privacy gate external bypass prevention | 3 |
| `test_provider_matrix.py` | Local Gemma vs. Grok availability, fallback to degraded factual mode | 6 |
| `test_observability.py` | Ingestion status rules, structured logging attributes | 3 |
| `test_parity_matrix.py` | OpenAPI endpoint synchronization and parity verification | 3 |
| `test_launchers.py` | Setup & Start CLI launcher scripts | 5 |
| **Total Automated Tests** | | **139 PASSED** |

---

## 2. Standard Verification Commands

### Backend Verification
```bash
# Run quick test pass
pytest tests/ -x -q -m "not live"

# Run full comprehensive test suite
pytest tests/ -v -m "not live"
```

### Frontend Verification
```bash
# Check CSS custom token compliance (0 banned classes)
node scripts/check-banned-classes.mjs

# Next.js 16 production build & TypeScript check
npm --prefix frontend run build
```

### Contract Synchronization
```bash
# Export OpenAPI schema and regenerate TypeScript types
python scripts/export_openapi.py
git diff --exit-code frontend/types/api.ts
```
