---
status: testing
phase: 03-vector-search-llm-provider-execution
source: [03-VERIFICATION.md]
started: "2026-08-15T03:05:00Z"
updated: "2026-08-15T03:05:00Z"
---

## Current Test

number: 1
name: Live Ollama Gemma inference
expected: |
  gemma_available: true (real /api/tags probe - no fabricated telemetry); a pipeline run produces Gemma-generated structured JSON with model_metadata.provider = local_gemma
awaiting: user response

## Tests

### 1. Live Ollama Gemma inference
expected: |
  gemma_available: true (real /api/tags probe - no fabricated telemetry); a pipeline run produces Gemma-generated structured JSON with model_metadata.provider = local_gemma
steps: |
  - docker compose up -d ollama
  - docker exec metaradar-ollama ollama pull gemma3:4b
  - GET /api/v1/health/models
  - Run a pipeline / generate_intelligence call
result: [pending]

### 2. Live Grok API call
expected: |
  test_grok_live_structured_output PASSES against the real api.x.ai endpoint; response contains what_changed + model_metadata
steps: |
  - Set LIVE_XAI_KEY env var
  - py -3.13 -m pytest tests/test_providers_live.py -v
result: [pending]

### 3. Live pgvector search
expected: |
  Backfill writes 384-dim vectors + embedding_model_version; search returns ranked results with similarity_score, metadata filters applied, NULL-embedding rows excluded
steps: |
  - Start Postgres 16 + pgvector + signals_embedding_hnsw (migration 001)
  - python -m app.services.embeddings_backfill
  - POST /api/v1/search with a query + filters
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
