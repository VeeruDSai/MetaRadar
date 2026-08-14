# Phase 3: Vector Search & LLM Provider Execution — PLAN

---

## Tracer Slice (Plan A) — End-to-End Retrieval Wire-Through

**Objective:** Replace all simulated provider behavior with real execution across four deliverable tracks, wired in production-quality code.

**Scope (locked):** `Ingestion -> Embedding -> Hybrid Retrieval -> Local LLM (Ollama/Gemma) -> Optional Grok Validation -> Structured Signal`. No fine-tuning, no complex agent loops, no multimodal, no distributed vector infra.

**Terminology invariant (user-locked):** pgvector/PostgreSQL = storage layer; HNSW = index/search method. Never describe the stack as "HNSW the vector database."

---

## Plan A — Tracer: Embedding Service -> Vector Search -> Provider Wiring

> **Verification gate:** After this plan, `pytest -v` must pass all existing 51 tests PLUS new retrieval/embedding tests, the `/api/v1/search` endpoint must return valid JSON, and `GET /api/v1/health/models` must accurately report Ollama status.

---

### Task A-1: Install fastembed and add OLLAMA_HOST to Settings

**Type:** implementation
**Files:** `backend/requirements.txt`, `backend/app/core/config.py`

**Prompt:**

Read:
- backend/requirements.txt
- backend/app/core/config.py

Add `fastembed>=0.4.0` to backend/requirements.txt (after the existing langgraph line).

In backend/app/core/config.py, add the following settings to the Settings class (after the existing XAI_API_KEY field and before the EMBEDDING_MODEL block):

    # Ollama Sidecar
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3:4b"   # matches LOCAL_LLM_MODEL name in Ollama registry

No other changes. Preserve all existing fields, docstrings, and structure.

**Verification:**

```bash
grep "fastembed" backend/requirements.txt
grep "OLLAMA_HOST" backend/app/core/config.py
```

---

### Task A-2: Implement EmbeddingService (fastembed, CPU, all-MiniLM-L6-v2)

**Type:** implementation
**Files:** `backend/app/services/embeddings.py` [NEW]

**Prompt:**

Read:
- backend/app/core/config.py (for Settings.EMBEDDING_MODEL, EMBEDDING_DIMENSION, EMBEDDING_MAX_SEQ_LENGTH, EMBEDDING_MODEL_REVISION)
- backend/app/services/deduplication.py (for chunk_text_for_embedding)
- backend/app/models/__init__.py (for Signal.embedding field shape: Vector(384))

Create backend/app/services/embeddings.py implementing EmbeddingService:

Requirements:
1. Runtime: fastembed TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
   - Loaded lazily on first call (singleton pattern, module-level _model = None)
   - Cache in-process; never reload between calls in the same process
   - Model identity matches settings.EMBEDDING_MODEL exactly

2. Public API:

   async def embed_text(text: str) -> list[float]:
       """Embed a single text chunk. Returns list of 384 floats."""

   async def embed_batch(texts: list[str]) -> list[list[float]]:
       """Embed a batch of text chunks. Returns list of 384-float vectors."""

   async def embed_signal(signal: dict) -> list[float]:
       """
       Compose embedding text from signal dict per D-02:
       text = f"{signal.get('title', '')} {signal.get('content', '')} {signal.get('signal_type', '')}"
       Chunked via chunk_text_for_embedding (256 tokens / EMBEDDING_MAX_SEQ_LENGTH).
       Returns 384-float vector.
       """

3. Error handling: any fastembed failure raises EmbeddingError (custom exception defined in same file)
   with message "Embedding failed: {cause}". Never return a zero-vector silently.

4. Module-level singleton: embedding_service = EmbeddingService()

5. Async wrapper: fastembed embed() is synchronous CPU. Wrap in asyncio.get_event_loop().run_in_executor(None, ...)
   so callers stay async without blocking the event loop.

6. Add type hints throughout. No # type: ignore without explicit justification comment.

Implementation constraints:
- Use only fastembed and stdlib (no torch, no sentence-transformers full stack per D-03)
- Validate output dimensionality: assert len(vector) == settings.EMBEDDING_DIMENSION before returning

**Verification:**

```bash
py -3.13 -c "from app.services.embeddings import embedding_service; import asyncio; v = asyncio.run(embedding_service.embed_text('haemophilia trial')); print(len(v))"
```
Expected: `384`

---

### Task A-3: Implement node_embed — LangGraph pipeline embedding step (D-04)

**Type:** implementation
**Files:** `backend/app/workflows/nodes/embed.py` [NEW]

**Prompt:**

Read:
- backend/app/workflows/nodes/validate.py (output shape: returns {validated_signals: [...], node_statuses: {...}})
- backend/app/workflows/nodes/ingest.py (pattern: node function, error boundary, node_statuses dict)
- backend/app/workflows/state.py (MetaRadarState contract)
- backend/app/services/embeddings.py (EmbeddingService.embed_signal)

Create backend/app/workflows/nodes/embed.py implementing:

```python
async def node_embed(state: MetaRadarState) -> Dict[str, Any]:
    """
    Node 2.5: node_embed (D-04)
    Embeds every validated_signal synchronously (fastembed CPU).
    Runs after node_validate, before node_nlp_extract.
    Adds 'embedding' key (list[float], 384 dims) and 'embedding_model_version'
    (settings.EMBEDDING_MODEL_REVISION) to each validated signal dict.
    Signals that fail embedding are kept with embedding=None and an error logged
    (never silently dropped -- pass through to nlp_extract).
    Returns validated_signals with embeddings, node_statuses.
    """
```

Requirements:
1. Read state["validated_signals"]. If empty, return early with SUCCESS status.
2. For each signal: call await embedding_service.embed_signal(sig).
   - On success: sig["embedding"] = vector, sig["embedding_model_version"] = settings.EMBEDDING_MODEL_REVISION
   - On EmbeddingError: log warning, sig["embedding"] = None, sig["embedding_model_version"] = None, accumulate to errors list
3. Return {"validated_signals": enriched_signals, "node_statuses": {node_name: status}, "errors": errors}
   where status = "SUCCESS" if no embedding errors, "DEGRADED" if some failed, "FAILED" if all failed.
4. Outer try/except: catch unexpected exceptions, log, return FAILED status with the error.
5. Follow exact LangGraph node pattern of sibling nodes.

**Verification:**

```bash
py -3.13 -c "
from app.workflows.nodes.embed import node_embed
from app.workflows.state import create_initial_state
import asyncio
state = create_initial_state()
state['validated_signals'] = [{'title': 'mim8 trial', 'content': 'haemophilia treatment ' * 20, 'signal_type': 'CLINICAL_TRIAL'}]
result = asyncio.run(node_embed(state))
sig = result['validated_signals'][0]
print('embedding dim:', len(sig['embedding']) if sig['embedding'] else 'NONE')
print('status:', result['node_statuses'])
"
```
Expected: `embedding dim: 384`, `status: {'node_embed': 'SUCCESS'}`

---

### Task A-4: Wire node_embed into LangGraph graph

**Type:** implementation
**Files:** `backend/app/workflows/graph.py`, `backend/app/workflows/nodes/__init__.py`

**Prompt:**

Read:
- backend/app/workflows/graph.py (current 10-node pipeline)
- backend/app/workflows/nodes/__init__.py (current node imports)

Objective: Insert node_embed between node_validate and node_nlp_extract (D-04).

Changes required:
1. backend/app/workflows/nodes/__init__.py:
   Add import: from app.workflows.nodes.embed import node_embed
   Add node_embed to __all__ (or wherever the existing nodes are exported from).

2. backend/app/workflows/graph.py:
   a. Import node_embed from app.workflows.nodes
   b. Add graph.add_node("node_embed", node_embed) after the node_validate add_node line
   c. Change graph.add_edge("node_validate", "node_nlp_extract") to:
      graph.add_edge("node_validate", "node_embed")
      graph.add_edge("node_embed", "node_nlp_extract")
   d. Update the docstring to reflect 11-node pipeline (add node_embed after node_validate in the order comment)

No other changes to graph.py. Preserve all other edges, compile call, and logger lines exactly.

**Verification:**

```bash
py -3.13 -c "from app.workflows.graph import build_graph; g = build_graph(); print('graph compiled OK')"
```
Expected: `graph compiled OK`

---

### Task A-5: Implement VectorQueryService — hybrid retrieval (D-06, D-07, D-08)

**Type:** implementation
**Files:** `backend/app/services/vector_query.py` [NEW]

**Prompt:**

Read:
- backend/app/models/__init__.py (Signal model, Signal.embedding field = Vector(384), Signal.signal_type, Signal.disease, etc.)
- backend/app/db/session.py (async session patterns)
- backend/app/services/embeddings.py (EmbeddingService.embed_text)
- backend/app/core/config.py (settings.EMBEDDING_DIMENSION)

Create backend/app/services/vector_query.py implementing VectorQueryService:

Design (D-06, D-07, D-08):
- Hybrid retrieval = metadata/keyword filtering + pgvector cosine similarity
- Flow: query_text -> embed_text -> SELECT signals WITH cosine distance ORDER BY embedding <=> query_vec WHERE filters applied -> Top-K results with similarity scores
- Top-K = 10 (default), cosine similarity (pgvector <=> operator), HNSW index signals_embedding_hnsw
- ef_search configurable (default=40)

```python
class SearchFilters(BaseModel):
    signal_type: Optional[str] = None    # e.g. "CLINICAL_TRIAL"
    disease: Optional[str] = None        # e.g. "haemophilia_a"
    priority: Optional[str] = None       # e.g. "HIGH"
    limit: int = Field(default=10, ge=1, le=100)

class SignalSearchResult(BaseModel):
    signal_id: str
    title: str
    content: str
    signal_type: str
    disease: str
    priority: str
    similarity_score: float              # 1 - cosine_distance (range 0-1)
    embedding_model_version: Optional[str]
    created_at: Optional[str]

class VectorQueryService:
    async def search(
        self,
        db: AsyncSession,
        query_text: str,
        top_k: int = 10,
        ef_search: int = 40,
        filters: Optional[SearchFilters] = None,
    ) -> list[SignalSearchResult]:
        """Hybrid search: embed query, apply metadata filters, cosine similarity rank."""
```

Implementation details:
1. Embed query_text via embedding_service.embed_text(query_text).
2. Set pgvector ef_search via: await db.execute(text(f"SET LOCAL hnsw.ef_search = {ef_search}"))
3. Build SQLAlchemy select with:
   - WHERE signal.embedding IS NOT NULL (skip NULL-embedding rows)
   - WHERE signal.signal_type = filters.signal_type (if provided)
   - WHERE signal.disease = filters.disease (if provided)
   - WHERE signal.priority = filters.priority (if provided)
   - ORDER BY Signal.embedding.cosine_distance(query_vector)
   - LIMIT top_k
4. Compute similarity_score = 1.0 - cosine_distance_value (clamp to [0, 1]).
5. Return list of SignalSearchResult Pydantic models.
6. Error: if embedding_service fails, raise SearchError("Embedding failed for query").
7. Module-level singleton: vector_query_service = VectorQueryService()

**Verification:**

```bash
py -3.13 -c "from app.services.vector_query import VectorQueryService, SearchFilters, SignalSearchResult; print('VectorQueryService imports OK')"
```

---

### Task A-6: Implement POST /api/v1/search endpoint (D-07)

**Type:** implementation
**Files:** `backend/app/api/v1/endpoints/search.py` [NEW], `backend/app/api/v1/router.py` [MODIFY]

**Prompt:**

Read:
- backend/app/api/v1/endpoints/signals.py (FastAPI endpoint patterns, DB dependency, error handling)
- backend/app/api/v1/router.py (how routers are registered)
- backend/app/services/vector_query.py (VectorQueryService, SearchFilters, SignalSearchResult)

Create backend/app/api/v1/endpoints/search.py:

```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[SearchFilters] = None
    top_k: int = Field(default=10, ge=1, le=100)
    ef_search: int = Field(default=40, ge=1, le=1000)

class SearchResponse(BaseModel):
    results: list[SignalSearchResult]
    total: int
    query: str
    ef_search_used: int

@router.post("/", response_model=SearchResponse)
async def search_signals(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    """
    Hybrid vector search: embed query, apply filters, return Top-K signals by cosine similarity.
    Requires signals to have embeddings (NULL-embedding rows excluded).
    """
```

Error handling:
- If vector_query_service raises SearchError: return HTTP 503 with {"detail": "Search service unavailable: {cause}"}
- 422 from Pydantic validation is automatic

In backend/app/api/v1/router.py:
- Register: api_router.include_router(search_router, prefix="/search", tags=["search"])
- Preserve all existing router registrations exactly.

**Verification:**

```bash
py -3.13 -c "from app.api.v1.endpoints.search import router; print('search router imports OK')"
```

---

### Task A-7: Wire real Gemma 3 4B via Ollama HTTP client in GemmaProvider

**Type:** implementation
**Files:** `backend/app/providers/gemma.py` [MODIFY]

**Prompt:**

Read:
- backend/app/providers/gemma.py (current simulated implementation)
- backend/app/providers/base.py (LLMProvider, ProviderCapability, DataClassification)
- backend/app/core/config.py (settings.OLLAMA_HOST, settings.OLLAMA_MODEL, settings.MAX_CONTEXT_TOKENS, settings.MAX_OUTPUT_TOKENS)
- backend/app/schemas/__init__.py (ModelMetadataSchema)

Replace the simulated GemmaProvider with a real Ollama-backed implementation:

Requirements (D-09, D-12):
1. HTTP client: use httpx.AsyncClient with base_url = settings.OLLAMA_HOST
2. Endpoint: POST /api/generate with JSON body:
   {"model": settings.OLLAMA_MODEL, "prompt": "<prompt>", "stream": false,
    "options": {"num_predict": settings.MAX_OUTPUT_TOKENS, "num_ctx": settings.MAX_CONTEXT_TOKENS}}
3. Response: parse {"response": "<text>", "done": true}
4. Never-crash contract (D-12): any exception must raise OllamaUnavailableError (custom exception, defined in this file).
   ProviderFactory catches this and moves to Grok -> BART. Do NOT swallow silently.
5. generate_summary(text): sends text as prompt, returns response string.
6. generate_intelligence(evidence, task, classification):
   - Construct structured prompt: SYSTEM + HUMAN with evidence and task
   - Call Ollama, parse response JSON
   - Return dict with: what_changed, why_it_matters, primary_function, suggested_action, model_metadata
   - model_metadata: provider="local_gemma", model=settings.OLLAMA_MODEL, latency_ms=<actual>, fallback_used=False
7. Add async def is_available() -> bool:
   - GET /api/tags, check if settings.OLLAMA_MODEL in response["models"] names
   - Returns False on any error (never raises)
8. httpx timeout: connect=5s, read=30s (Gemma inference can be slow)
9. Preserve class-level name = "gemma_local" and capabilities list exactly.

**Verification:**

```bash
py -3.13 -c "from app.providers.gemma import GemmaProvider, OllamaUnavailableError; print('GemmaProvider imports OK')"
```

---

### Task A-8: Wire real Grok API client in GrokProvider (D-13, D-14, D-16)

**Type:** implementation
**Files:** `backend/app/providers/grok.py` [MODIFY]

**Prompt:**

Read:
- backend/app/providers/grok.py (current simulated implementation with existing validate_privacy_gate)
- backend/app/providers/base.py (LLMProvider, DataClassification)
- backend/app/core/config.py (settings.XAI_API_KEY, settings.ENABLE_GROK_FALLBACK)
- backend/app/schemas/__init__.py (ModelMetadataSchema)

Replace the simulated generate_intelligence with a real xAI Grok API client.

CRITICAL: Do NOT change validate_privacy_gate -- it is already correct and tested. Only change generate_intelligence and generate_summary.

Requirements (D-13, D-14, D-16):
1. Privacy gate remains exactly as-is: validate_privacy_gate(classification) before any API call.
2. Real API endpoint: POST https://api.x.ai/v1/chat/completions
   Headers: {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
   Body: {"model": "grok-beta", "messages": [...], "max_tokens": 1024, "response_format": {"type": "json_object"}}
3. Parse response: choices[0]["message"]["content"] -> JSON string -> dict
4. Extract: what_changed, why_it_matters, suggested_action from parsed JSON (with safe .get() fallbacks)
5. httpx timeout: connect=5s, read=60s.
6. model_metadata: provider="xai", model="grok-beta", latency_ms=<actual>, fallback_used=True
7. Mocked CI path (D-16):
   - If self.api_key is empty string or None -> raise GrokUnavailableError("No XAI_API_KEY configured")
   - CI stays green without a key; provider factory falls through to BART
   - DO NOT add @pytest.mark or test-specific logic in production code

Preserve: name = "grok", capabilities list, validate_privacy_gate signature and logic EXACTLY.

**Verification:**

```bash
py -3.13 -c "from app.providers.grok import GrokProvider, GrokUnavailableError; print('GrokProvider imports OK')"
```

---

### Task A-9: Update /health/models to report real Ollama status (D-10)

**Type:** implementation
**Files:** `backend/app/api/v1/endpoints/health.py` [MODIFY]

**Prompt:**

Read:
- backend/app/api/v1/endpoints/health.py (current /health/models returning fabricated gemma_available=True)
- backend/app/providers/gemma.py (GemmaProvider.is_available() async method added in Task A-7)
- backend/app/schemas/__init__.py (HealthModelsResponse schema)

Update the get_health_models endpoint to remove the fabricated gemma_available=True:

```python
@router.get("/models", response_model=HealthModelsResponse)
async def get_health_models():
    """Reports real provider & model initialization availability. No fabricated telemetry."""
    from app.providers.gemma import GemmaProvider
    provider = GemmaProvider()
    gemma_available = await provider.is_available()   # actual HTTP GET to Ollama /api/tags
    return HealthModelsResponse(
        llm_provider=settings.LLM_PROVIDER,
        gemma_available=gemma_available,
        grok_configured=bool(settings.XAI_API_KEY),
        grok_fallback_enabled=settings.ENABLE_GROK_FALLBACK,
        bart_degraded_available=True,
        embedding_model=settings.EMBEDDING_MODEL,
        embedding_revision=settings.EMBEDDING_MODEL_REVISION,
        embedding_dimension=settings.EMBEDDING_DIMENSION
    )
```

Also add ollama_host: str field to HealthModelsResponse in schemas.py (value = settings.OLLAMA_HOST).

No other changes to health.py.

**Verification:**

```bash
py -3.13 -c "from app.api.v1.endpoints.health import get_health_models; print('health endpoint updated')"
```

---

### Task A-10: Implement retrieval and provider tests (D-16)

**Type:** testing
**Files:** `tests/test_retrieval.py` [NEW], `tests/test_providers_live.py` [NEW]

**Prompt:**

Read:
- tests/test_provider_matrix.py (existing pattern: mocked provider tests, Cases A-F)
- tests/test_privacy_boundary.py (existing privacy gate test pattern)
- backend/app/services/embeddings.py (EmbeddingService)
- backend/app/services/vector_query.py (VectorQueryService, SearchFilters)
- backend/app/workflows/nodes/embed.py (node_embed)
- backend/app/providers/gemma.py (GemmaProvider, OllamaUnavailableError)
- backend/app/providers/grok.py (GrokProvider, GrokUnavailableError)

Create tests/test_retrieval.py (hermetic -- no live services):

Tests to implement:
1. test_embed_text_returns_384_dims: mock fastembed TextEmbedding to return [0.1]*384; assert len == 384
2. test_embed_signal_composites_text: verify embed_signal builds text from title + content + signal_type
3. test_embed_batch_calls_model_once: verify batch is passed together, not individually
4. test_node_embed_attaches_embedding_to_signal: mock embed_signal; check sig["embedding"] is list, sig["embedding_model_version"] is not None
5. test_node_embed_degraded_on_partial_failure: mock embed_signal to raise on second call; verify status=DEGRADED
6. test_node_embed_empty_state_returns_success: node_embed with empty validated_signals -> status SUCCESS
7. test_search_filters_pydantic: SearchFilters(limit=200) raises ValidationError (limit le=100)
8. test_gemma_raises_on_connection_refused: mock httpx ConnectError; GemmaProvider.generate_intelligence raises OllamaUnavailableError
9. test_gemma_is_available_false_on_error: mock GET /api/tags to raise; is_available() returns False (never raises)
10. test_grok_blocks_without_api_key: GrokProvider(api_key="").generate_intelligence raises GrokUnavailableError

Create tests/test_providers_live.py (opt-in, marker=live):
```python
import os, pytest

@pytest.mark.live
@pytest.mark.skipif(not os.getenv("LIVE_XAI_KEY"), reason="Requires LIVE_XAI_KEY env var")
async def test_grok_live_structured_output():
    """Real Grok API call -- only runs with LIVE_XAI_KEY set. CI stays green without it."""
    from app.providers.grok import GrokProvider
    from app.providers.base import DataClassification
    provider = GrokProvider(api_key=os.environ["LIVE_XAI_KEY"])
    result = await provider.generate_intelligence(
        evidence=["Emicizumab phase 3 trial showed 96% bleed reduction."],
        task="Summarize clinical impact for haemophilia A market.",
        classification=DataClassification.SYNTHETIC
    )
    assert "what_changed" in result
    assert "model_metadata" in result
```

Add live marker to pytest.ini or conftest.py:
    markers:
        live: mark test as requiring live external services

All tests in test_retrieval.py must pass without any network calls or external services.

**Verification:**

```bash
py -3.13 -m pytest tests/test_retrieval.py -v
```
Expected: All 10 tests pass

---

### Task A-11: Add CLI backfill command for NULL-embedding signals (D-05)

**Type:** implementation
**Files:** `backend/app/services/embeddings_backfill.py` [NEW]

**Prompt:**

Read:
- backend/app/services/embeddings.py (EmbeddingService.embed_signal)
- backend/app/models/__init__.py (Signal model, embedding field)
- backend/app/db/session.py (async session patterns)
- backend/app/core/config.py (settings)

Create backend/app/services/embeddings_backfill.py:

CLI entry point: `python -m app.services.embeddings_backfill [--batch-size 50] [--dry-run]`

Implements async_main():
1. SELECT signals WHERE embedding IS NULL LIMIT batch_size
2. For each: embed_signal(row_as_dict), UPDATE signals SET embedding=vector, embedding_model_version=settings.EMBEDDING_MODEL_REVISION
3. Commit batch, log progress: "Backfilled N signals (embedding_model_version={settings.EMBEDDING_MODEL_REVISION})"
4. Repeat until no NULL-embedding rows remain
5. --dry-run: log what WOULD be embedded without writing to DB

Error handling: if embedding fails for a row, log warning and skip (backfill must not abort entire batch on partial failure).

**Verification:**

```bash
py -3.13 -c "from app.services.embeddings_backfill import async_main; print('backfill CLI imports OK')"
```

---

### Task A-12: Add Ollama service to docker-compose.yml (D-10)

**Type:** infrastructure
**Files:** `docker-compose.yml` [MODIFY]

**Prompt:**

Read:
- docker-compose.yml (current services: postgres, redis, backend, backend-gpu, frontend)

Add an `ollama` service to docker-compose.yml:

```yaml
# Ollama sidecar -- hosts Gemma 3 4B (Q4 int4) for local LLM inference (D-09, D-10)
# On first run: docker exec metaradar-ollama ollama pull gemma3:4b
# VRAM budget: ~2.8 GB weights + KV cache fits RTX 3050 4 GB (MAX_CONTEXT_TOKENS=2048)
ollama:
  image: ollama/ollama:latest
  container_name: metaradar-ollama
  restart: always
  ports:
    - "11434:11434"
  volumes:
    - ollama_models:/root/.ollama
  healthcheck:
    test: ["CMD-SHELL", "curl -sf http://localhost:11434/api/tags || exit 1"]
    interval: 15s
    timeout: 10s
    retries: 5
    start_period: 30s
```

Update backend and backend-gpu services:
1. Add environment: OLLAMA_HOST=http://ollama:11434
2. Add depends_on: ollama: condition: service_started

Add to volumes section: ollama_models:

Preserve all existing services, healthchecks, and volume mounts exactly.

**Verification:**

```bash
docker compose config --quiet
```
Expected: exits 0 (no error)

---

### Task A-13: Run full test suite and verify contract drift

**Type:** verification
**Files:** None (verification task)

**Prompt:**

Execute the complete verification sequence:

1. Install fastembed:
   `py -3.13 -m pip install fastembed`

2. Run full pytest suite:
   `py -3.13 -m pytest -v`
   REQUIRED: All 51 existing tests PASS + all new tests in test_retrieval.py PASS. ZERO failures permitted.

3. Run OpenAPI contract sync:
   `py -3.13 scripts/export_openapi.py`
   REQUIRED: exits 0, produces contracts/openapi.json and frontend/types/api.ts

4. Validate docker compose config:
   `docker compose config`
   REQUIRED: exits 0 (valid YAML, no undefined references)

5. TypeScript check (if node_modules present):
   `npx pnpm --dir frontend exec tsc --noEmit`
   REQUIRED: 0 TypeScript errors

Report exact output for each step. If any step fails:
- Do NOT suppress the error
- Do NOT add ignoreBuildErrors or @ts-ignore
- Fix the root cause and re-run

After all steps pass, report:
  - pytest: {N} passed, 0 failed
  - OpenAPI sync: 0 drift
  - docker compose: validated
  - TypeScript: 0 errors

---

## Verification Gate

The following must all be true before Phase 3 is declared complete:

| Gate | Command | Required Result |
|---|---|---|
| Full pytest suite | `py -3.13 -m pytest -v` | All tests PASS (>=51 + new retrieval tests), 0 failures |
| New retrieval tests | `py -3.13 -m pytest tests/test_retrieval.py -v` | 10/10 PASS |
| Embedding service | `py -3.13 -c "from app.services.embeddings import embedding_service; ..."` | Returns 384-dim vector |
| Search endpoint | `py -3.13 -c "from app.api.v1.endpoints.search import router; ..."` | Imports cleanly |
| OpenAPI contract | `py -3.13 scripts/export_openapi.py` | 0 drift |
| Docker compose | `docker compose config` | Validated |
| TypeScript | `npx tsc --noEmit` | 0 errors |

**Human UAT (deferred to Phase 3 VERIFICATION.md):**
- Live Ollama Gemma inference (RTX 3050, requires physical GPU) -- verified via GET /api/v1/health/models reporting gemma_available: true
- Live Grok API call -- verified via opt-in test with LIVE_XAI_KEY env var

---

*Phase: 3 -- Vector Search & LLM Provider Execution*
*Plan created: 2026-08-15*
*Strategy: Tracer-first, production-quality implementation*
*Decisions locked: D-01 through D-17 (03-CONTEXT.md)*
