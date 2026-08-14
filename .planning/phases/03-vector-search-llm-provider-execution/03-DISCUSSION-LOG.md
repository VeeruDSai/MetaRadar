# Phase 3 Discussion Log

**Gathered:** 2026-08-15
**Areas discussed:** 7 (4 primary + 3 follow-on)

## Area 1: Grok Live Validation Scope
- **Options presented:** (a) Mocked CI + opt-in live test, (b) Gate-only tests, no live test, (c) Reuse existing provider matrix tests.
- **User selected:** Mocked CI + opt-in live test (Recommended).
- **Notes:** User additionally locked the privacy gate rule as explicit (public/synthetic only, else blocked → local fallback), the three-mode operation (Demo/Standard/Restricted), the public claim about public/mock/synthetic data only, and that live Grok is never mandatory.

## Area 2: Gemma Inference Backend & VRAM Strategy
- **Options presented:** (a) llama-cpp-python (GGUF int4), (b) transformers + bitsandbytes, (c) Ollama sidecar, (d) You decide.
- **User selected:** Ollama sidecar.
- **Notes:** User repositioned Gemma as local baseline (extraction/classification/summarization), Grok as validation/enrichment. Q4/int4 on RTX 3050, never-crash fallback chain.

## Area 3: Vector Search Interface & Integration
- **Options presented:** (a) Expose /search endpoint now, (b) Internal service only this phase, (c) Pipeline-internal only.
- **User selected:** Expose /search endpoint now (Recommended).
- **Notes:** User locked hybrid retrieval (metadata/keyword + pgvector cosine), Top-K=10, HNSW m=16/ef_construction=64, adjustable ef_search, and corrected terminology (HNSW is the index, pgvector is the store).

## Area 4: Embedding Pipeline Timing & Text Source
- **Options presented:** (a) Pipeline step + CLI backfill, (b) Inline in node_ingest, (c) Startup backfill only.
- **User selected:** Pipeline step + CLI backfill (Recommended).
- **Notes:** User locked embed-at-ingestion (not lazy), text source = title + normalized summary + entities + signal category, consuming Phase 1 stored chunks (no new chunking).

## Follow-on Area 5: Embedding Runtime & VRAM
- **Options presented:** (a) fastembed (ONNX, CPU), (b) sentence-transformers (torch), (c) Ollama embedding models.
- **User selected:** fastembed (ONNX, CPU) (Recommended).
- **Notes:** Keeps 4 GB VRAM free for Gemma; model identity stays all-MiniLM-L6-v2.

## Follow-on Area 6: Ollama Container & Deploy Story
- **Options presented:** (a) docker-compose sidecar + auto-pull, (b) Host-side Ollama, (c) Client + docs, manual pull.
- **User selected:** docker-compose sidecar + auto-pull (Recommended).
- **Notes:** Persistent volume, OLLAMA_HOST config, /health/models reports real Ollama status.

## Follow-on Area 7: BART Degraded Path
- **Options presented:** (a) Keep transformers BART as-is, (b) Move BART to Ollama, (c) Replace BART with source-grounded fallback.
- **User selected:** Keep transformers BART as-is (Recommended).

## General / Cross-Cutting
- User reviewed the Phase 3 decision screen against current official docs (Gemma 3 4B, pgvector, Grok structured outputs, xAI security) and confirmed the architecture is defensible.
- **Anti-over-engineering:** Phase 3 locked to `Ingestion → Embedding → Hybrid Retrieval → Local LLM → Optional Grok Validation → Structured Signal`; fine-tuning, agent loops, multimodal, reranking, distributed vector infra, autonomous agents all deferred.
- **Terminology correction:** HNSW is the index method; pgvector/PostgreSQL is the storage layer.
- One-month hackathon constraint explicitly considered.

## Deferred Ideas
- Fine-tuning, complex agent loops, multimodal pipelines, elaborate reranking, distributed vector infrastructure, autonomous agents — all captured in 03-CONTEXT.md `<deferred>`.