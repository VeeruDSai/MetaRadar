# Pitfalls Research — MetaRadar

## Domain Pitfalls & Mitigations

### 1. Hardcoding AI Models
- **Risk**: Lock-in to a specific model that fails on production hardware or incurs unexpected costs.
- **Mitigation**: Strictly wrap LLM invocation via HuggingFace pipeline configured through LOCAL_LLM_MODEL environment variable. Zero model names hardcoded in application logic.

### 2. API Down-Time During Live Demo
- **Risk**: External source failure (e.g., NewsAPI 429/500) breaking the live hackathon presentation.
- **Mitigation**: Implement 3-tier fallback (Live API with 	enacity retry → Redis 2h cache → Graceful degraded empty response).

### 3. LLM Hallucination in Regulatory Context
- **Risk**: Presenting fabricated competitive moves or clinical trial outcomes to Medical Affairs judges.
- **Mitigation**: Enforce 100% traceable evidence chain (Source URL + exact excerpt) and display mandatory <DisclaimerBadge /> on all AI summaries.

### 4. Regulatory Audit Failure
- **Risk**: Lack of audit logging for pharma GxP compliance.
- **Mitigation**: Database-enforced WORM udit_log table storing before/after state JSON for all user mutations.
