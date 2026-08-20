# Phase 07 Research: Trustworthy Intelligence Reconciliation & Platform Hardening

> **Status:** RESEARCH COMPLETE  
> **Phase:** 07 — Trustworthy Intelligence Reconciliation & Platform Hardening  
> **Stack:** FastAPI 0.110+, Python 3.11, SQLAlchemy 2.0 async/asyncpg, PostgreSQL 16 + pgvector, LangGraph, Next.js 16.3 (App Router), React 19, TypeScript 5.7, Tailwind v4, pnpm  
> **Grounded in:** Direct file inspection of the real MetaRadar v5.1 codebase  

---

## Standard Stack

### Python / Backend Libraries
| Purpose | Library | Version | Notes |
|:---|:---|:---|:---|
| Structured JSON logging | `structlog` | `>=24.1.0` | Use with `structlog.contextvars` — already asyncio-safe |
| Correlation ID propagation | `asgi-correlation-id` | `>=4.3.0` | Reads/generates `X-Request-ID`, propagates to structlog automatically |
| HTTP testing + mocking | `pytest-httpx` | `>=0.30.0` | Patches `httpx.AsyncClient` for failure injection without network calls |
| Async test support | `pytest-asyncio` | `>=0.23.0` | Already in use; pin `asyncio_mode = "auto"` in pytest.ini |
| Database test isolation | `pytest-postgresql` or `sqlalchemy-utils` | — | Use existing PostgreSQL test DSN; wrap tests in `AsyncSession` rollback |

### Frontend Libraries
| Purpose | Library | Notes |
|:---|:---|:---|
| Lightweight component tests | `@testing-library/react` + `vitest` | For React 19 + Next.js 16 App Router; does not require Playwright |
| Test runner | `vitest` | Vite-based, works without ejecting Next.js config; add `vitest.config.ts` |
| JSdom environment | `jsdom` (vitest builtin) | Provides DOM APIs for component render tests without a browser |

---

## Architecture Patterns

### A. Structured JSON Logging + Correlation IDs

**Pattern: `structlog` + `asgi-correlation-id` + `contextvars`**

```python
# backend/app/core/logging.py
import structlog
import logging
from contextvars import ContextVar

# PII/secret scrubber processor
def _scrub_secrets(_, __, event_dict: dict) -> dict:
    SENSITIVE = {"password", "token", "api_key", "secret", "authorization",
                 "cookie", "access_token", "private_key", "bearer", "grok_key"}
    for key in list(event_dict.keys()):
        if any(s in key.lower() for s in SENSITIVE):
            event_dict[key] = "[REDACTED]"
    return event_dict

def configure_structlog(json_logs: bool = True) -> None:
    shared_processors = [
        structlog.contextvars.merge_contextvars,          # pulls request_id, pipeline_run_id etc.
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        _scrub_secrets,
    ]
    if json_logs:
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        shared_processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=shared_processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

```python
# backend/app/core/middleware.py
import uuid
import time
import structlog
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.responses import JSONResponse

logger = structlog.get_logger("metaradar.api")

class CorrelationIdMiddleware:
    """Injects X-Request-ID and binds to structlog contextvars."""
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Clear previous request context
        structlog.contextvars.clear_contextvars()

        # Read or generate request ID
        headers = dict(scope.get("headers", []))
        request_id = (
            headers.get(b"x-request-id", b"").decode() or
            str(uuid.uuid4())
        )
        structlog.contextvars.bind_contextvars(request_id=request_id)

        start_ns = time.perf_counter_ns()
        status_code = 500

        async def send_with_id(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                # Propagate X-Request-ID back in response headers
                headers_list = list(message.get("headers", []))
                headers_list.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": headers_list}
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            duration_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.info(
                "http.request_completed",
                method=scope.get("method", "UNKNOWN"),
                path=scope.get("path", ""),
                status_code=status_code,
                duration_ms=round(duration_ms, 2),
            )
```

**Correlation ID propagation inside LangGraph nodes:**  
- Python 3.11 `contextvars.ContextVar` values propagate automatically across `async` boundaries within the same task tree.  
- `structlog.contextvars` is a thin wrapper over `contextvars`. Any value bound in the middleware (e.g. `request_id`, `pipeline_run_id`) is automatically available inside all LangGraph node coroutines that are awaited from the same asyncio task.  
- For background pipeline runs (started independently, not per-HTTP-request), bind a fresh `pipeline_run_id` at the start of `PipelineRunner.run()`:

```python
# backend/app/workflows/runner.py
import structlog, uuid
run_id = str(uuid.uuid4())
structlog.contextvars.bind_contextvars(pipeline_run_id=run_id)
```

---

### B. Alembic Async Migrations (Additive Schema Changes)

**Pattern: manual additive migrations — never autogenerate with `--autogenerate` for production tables with existing data**

**Rule:** All new columns for Phase 07 must be `nullable=True` or have a `server_default`. Never add non-nullable columns without backfill in the same transaction.

**Migration 004 — add provenance + is_applied + SourceHealthLog:**
```python
# backend/alembic/versions/004_phase7_truthfulness_and_provenance.py
"""phase7: add provenance fields, CalibrationFeedback.is_applied, SourceHealthLog

Revision ID: 004_p7_provenance
Revises: 003_contradictions_scoring
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = '004_p7_provenance'
down_revision = '003_contradictions_scoring'

def upgrade() -> None:
    # --- signals: add data_mode, is_synthetic, confidence_type ---
    op.add_column('signals', sa.Column('data_mode', sa.String(50), nullable=True, server_default='live'))
    op.add_column('signals', sa.Column('is_synthetic', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('signals', sa.Column('confidence_type', sa.String(50), nullable=True))
    op.add_column('signals', sa.Column('confidence_rationale', sa.Text(), nullable=True))

    # --- contradictions: add claim excerpts ---
    op.add_column('contradictions', sa.Column('claim_a_excerpt', sa.Text(), nullable=True))
    op.add_column('contradictions', sa.Column('claim_b_excerpt', sa.Text(), nullable=True))
    op.add_column('contradictions', sa.Column('claim_a_evidence_id', UUID(as_uuid=True), nullable=True))
    op.add_column('contradictions', sa.Column('claim_b_evidence_id', UUID(as_uuid=True), nullable=True))
    op.add_column('contradictions', sa.Column('confidence_type', sa.String(50), nullable=True, server_default='nli_heuristic'))

    # --- calibration_feedback: add is_applied, applied_at, calibration_run_id ---
    op.add_column('calibration_feedback', sa.Column('is_applied', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('calibration_feedback', sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('calibration_feedback', sa.Column('calibration_run_id', UUID(as_uuid=True), nullable=True))

    # --- sources: add canonical health state fields ---
    op.add_column('sources', sa.Column('connector_status', sa.String(50), nullable=True, server_default='NEVER_CONNECTED'))
    op.add_column('sources', sa.Column('last_attempted', sa.DateTime(timezone=True), nullable=True))
    op.add_column('sources', sa.Column('latency_ms', sa.Integer(), nullable=True))
    op.add_column('sources', sa.Column('records_fetched', sa.Integer(), nullable=True))
    op.add_column('sources', sa.Column('records_accepted', sa.Integer(), nullable=True))
    op.add_column('sources', sa.Column('records_rejected', sa.Integer(), nullable=True))
    op.add_column('sources', sa.Column('http_status', sa.Integer(), nullable=True))

    # --- new table: source_health_logs ---
    op.create_table(
        'source_health_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('source_id', sa.String(100), sa.ForeignKey('sources.source_id'), nullable=False),
        sa.Column('pipeline_run_id', UUID(as_uuid=True), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('connector_status', sa.String(50), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('records_fetched', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('records_accepted', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('records_rejected', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
    )

    # --- new table: calibration_runs ---
    op.create_table(
        'calibration_runs',
        sa.Column('run_id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='running'),
        sa.Column('feedback_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('previous_weights', JSONB(), nullable=True),
        sa.Column('new_weights', JSONB(), nullable=True),
        sa.Column('affected_functions', JSONB(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('scoring_version', sa.String(50), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('calibration_runs')
    op.drop_table('source_health_logs')
    for col in ['calibration_run_id', 'applied_at', 'is_applied']:
        op.drop_column('calibration_feedback', col)
    for col in ['connector_status', 'last_attempted', 'latency_ms',
                'records_fetched', 'records_accepted', 'records_rejected', 'http_status']:
        op.drop_column('sources', col)
    for col in ['claim_a_excerpt', 'claim_b_excerpt',
                'claim_a_evidence_id', 'claim_b_evidence_id', 'confidence_type']:
        op.drop_column('contradictions', col)
    for col in ['data_mode', 'is_synthetic', 'confidence_type', 'confidence_rationale']:
        op.drop_column('signals', col)
```

---

### C. Priority Scoring Service Architecture

**Pattern: Stateless versioned service class returning typed `ScoreBreakdown | None`**

The scoring service must be a pure function of its inputs (no DB side effects). It is called:
1. Inside `node_nlp_extract` or `node_synthesize` — during pipeline processing.
2. Inside `_serialize_signal()` in `signals.py` — at API serialization time (as a fallback re-score if `score_breakdown` is null).

```python
# backend/app/services/scoring.py
from dataclasses import dataclass
from typing import Optional
import math

SCORING_VERSION = "haemophilia_v2.0"

@dataclass
class ScoreInput:
    novelty_distance: Optional[float]   # cosine distance to nearest neighbour (0-1; higher = more novel)
    clinical_keywords_found: int         # count of matched clinical significance terms
    regulatory_keywords_found: int       # count of matched regulatory relevance terms
    hours_since_published: Optional[float]

@dataclass
class ScoreBreakdown:
    novelty: float
    clinical: float
    regulatory: float
    recency: float
    total: float
    version: str

    def to_dict(self) -> dict:
        return {
            "novelty": round(self.novelty, 2),
            "clinical": round(self.clinical, 2),
            "regulatory": round(self.regulatory, 2),
            "recency": round(self.recency, 2),
            "total": round(self.total, 2),
            "version": self.version,
        }


class PriorityScoringService:
    """
    Deterministic multi-factor priority scorer.
    
    Weights (stakeholder-approved defaults, overridable via ScoringWeights table):
      novelty:    0.25   — distance to nearest semantic neighbour
      clinical:   0.30   — endpoint / inhibitor / phase mention count
      regulatory: 0.25   — PDUFA / CHMP / filing / designation count
      recency:    0.20   — exponential decay (half-life = 72h)
    
    Returns None if any required input is absent (caller maps to null/not_computed).
    """
    VERSION = SCORING_VERSION
    HALF_LIFE_HOURS = 72.0

    def score(self, inp: ScoreInput) -> Optional[ScoreBreakdown]:
        if inp.hours_since_published is None or inp.novelty_distance is None:
            return None  # Not enough information to score

        # Novelty: cosine distance (0=identical, 1=orthogonal) — novel content scores high
        novelty = min(1.0, inp.novelty_distance) * 25.0  # max 25 pts

        # Clinical significance: capped at 30 pts (3 pts per keyword match)
        clinical = min(30.0, inp.clinical_keywords_found * 3.0)

        # Regulatory relevance: capped at 25 pts
        regulatory = min(25.0, inp.regulatory_keywords_found * 5.0)

        # Recency: exponential decay
        decay = math.exp(-0.693 * inp.hours_since_published / self.HALF_LIFE_HOURS)
        recency = decay * 20.0  # max 20 pts

        total = round(novelty + clinical + regulatory + recency, 2)

        return ScoreBreakdown(
            novelty=round(novelty, 2),
            clinical=round(clinical, 2),
            regulatory=round(regulatory, 2),
            recency=round(recency, 2),
            total=total,
            version=self.VERSION,
        )

# Module-level singleton
priority_scorer = PriorityScoringService()
```

**API serialization pattern** — when `score_breakdown` is null in the DB, return explicit `"scoring_status": "not_computed"`:
```python
# In _serialize_signal():
if s.score_breakdown:
    breakdown = ScoreBreakdownSchema(**s.score_breakdown)
    scoring_status = "computed"
else:
    breakdown = None
    scoring_status = "not_computed"
```

---

### D. pgvector Evidence Retrieval for Athena

**Pattern: single efficient async query with cosine distance threshold**

```python
# backend/app/services/athena.py (retrieval section)
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Signal, Evidence, RawSignalBronze

SIMILARITY_THRESHOLD = 0.28   # cosine distance threshold (1 - 0.72 similarity)
TOP_K = 5

async def retrieve_evidence(
    db: AsyncSession,
    query_embedding: list[float],
    top_k: int = TOP_K,
) -> list[dict]:
    """
    Retrieve top-K evidence chunks via pgvector cosine distance.
    Returns [] if no chunks meet the similarity threshold.
    """
    # Use <=> (cosine distance operator) — lower is more similar
    stmt = (
        select(
            Signal.signal_id,
            Signal.title,
            Signal.canonical_url,
            Signal.source_id,
            Signal.published_at,
            Signal.content,
            Signal.embedding.op("<=>")(query_embedding).label("distance"),
        )
        .where(Signal.embedding.isnot(None))
        .where(Signal.embedding.op("<=>")(query_embedding) < SIMILARITY_THRESHOLD)
        .order_by("distance")
        .limit(top_k)
    )
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return []

    return [
        {
            "signal_id": str(r.signal_id),
            "title": r.title,
            "source_id": r.source_id,
            "canonical_url": r.canonical_url,
            "published_at": r.published_at.isoformat() if r.published_at else None,
            "excerpt": r.content[:500],   # verbatim first 500 chars
            "distance": round(r.distance, 4),
        }
        for r in rows
    ]
```

**Zero-fabrication rule for Athena responses:**
```python
if not evidence_chunks:
    return AthenaQueryResponse(
        answer="No sufficiently relevant evidence was found in the indexed sources to answer this question.",
        evidence=[],
        reasoning_available=False,
        provider="none",
        response_type="insufficient_evidence",
    )
```

**FACT/INFERENCE/SUGGESTION taxonomy** — implemented as a post-processing parse on the LLM response using a simple prefix convention:
- Prompt instructs the model to prefix every bullet with `[FACT]`, `[INFERENCE]`, or `[SUGGESTION]`.
- The API response exposes a structured `claims: list[{type, text, evidence_ids}]` field parsed from the model output.

---

### E. Frontend Modularization (Next.js 16 App Router)

**Pattern: extract domain components out of `metaradar.tsx` into `frontend/components/<domain>/` subfolders; pages remain in `frontend/app/`**

**Extraction approach** (avoids breaking the build):
1. Create the target directory: `frontend/components/common/`, `frontend/components/signals/`, etc.
2. Move one domain at a time (start with `common/ErrorState.tsx` and `common/EmptyState.tsx` — no circular deps).
3. Update imports in `metaradar.tsx` to point to new paths.
4. After full extraction, the shell of `metaradar.tsx` becomes a layout router component only.
5. Finally split into individual `frontend/app/<route>/page.tsx` files.

**`ErrorState` component pattern:**
```tsx
// frontend/components/common/ErrorState.tsx
import { useState } from 'react'

interface ErrorStateProps {
  title?: string
  message: string
  requestId?: string
  endpoint?: string
  statusCode?: number
  onRetry?: () => void
}

export function ErrorState({ title = "Something went wrong", message, requestId, endpoint, statusCode, onRetry }: ErrorStateProps) {
  const [detailsOpen, setDetailsOpen] = useState(false)

  return (
    <div role="alert" aria-live="assertive" className="rounded-xl border border-red-800/40 bg-red-950/20 p-6 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-red-400">{title}</p>
          <p className="text-sm text-slate-300 mt-1">{message}</p>
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="shrink-0 text-xs px-3 py-1.5 rounded-md bg-slate-700 hover:bg-slate-600 text-slate-200 transition"
          >
            Retry
          </button>
        )}
      </div>

      {requestId && (
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span>Correlation ID: <code className="text-slate-400">{requestId}</code></span>
          <button
            onClick={() => navigator.clipboard.writeText(requestId)}
            aria-label="Copy correlation ID"
            className="text-slate-500 hover:text-slate-300"
          >
            ⎘
          </button>
        </div>
      )}

      {(endpoint || statusCode) && (
        <button
          className="text-xs text-slate-600 hover:text-slate-400"
          onClick={() => setDetailsOpen(v => !v)}
          aria-expanded={detailsOpen}
        >
          {detailsOpen ? "Hide" : "Show"} technical details
        </button>
      )}

      {detailsOpen && (
        <pre className="text-xs text-slate-500 bg-slate-900 rounded p-3 overflow-auto max-h-40">
          {JSON.stringify({ endpoint, status_code: statusCode, request_id: requestId }, null, 2)}
        </pre>
      )}
    </div>
  )
}
```

**Eliminating `any` in TypeScript mappers** — use discriminated union + `unknown` + Zod or manual type guards:
```ts
// frontend/lib/mappers.ts
import type { Signal as ApiSignal } from '@/types/api'

export function mapSignal(raw: ApiSignal): MappedSignal {
  return {
    id: raw.signal_id,
    title: raw.title ?? "Untitled",
    score: raw.score_breakdown?.total ?? null,          // explicit null, not 0
    scoringStatus: raw.scoring_status ?? "not_computed",
    isSynthetic: raw.is_synthetic ?? false,
    dataMode: raw.data_mode ?? "live",
    confidence: raw.confidence ?? null,
    confidenceType: raw.confidence_type ?? null,
    publishedAt: raw.published_at ? new Date(raw.published_at) : null,
  }
}
```

---

### F. Connector Health Telemetry

**Pattern: persist `SourceHealthLog` at the END of each connector profile run — fire-and-forget in background (does not block ingestion)**

```python
# backend/app/connectors/base.py — add to SourceConnector._persist_health_log()
async def _persist_health_log(
    self,
    session: AsyncSession,
    result: ProfileRunResult,
    pipeline_run_id: Optional[Any] = None,
) -> None:
    """Persist connector run telemetry — called at end of run_profile()."""
    from app.models import SourceHealthLog, Source
    from datetime import datetime, timezone

    status = self._run_status_to_health_state(result.status)
    log = SourceHealthLog(
        source_id=self.source_id,
        pipeline_run_id=pipeline_run_id,
        checked_at=datetime.now(timezone.utc),
        connector_status=status,
        latency_ms=int(result.duration_s * 1000),
        records_fetched=result.fetched,
        records_accepted=result.new_rows,
        records_rejected=result.errors,
        last_error=result.error_detail,
    )
    session.add(log)

    # Also update the Sources table's live health state
    await session.execute(
        update(Source)
        .where(Source.source_id == self.source_id)
        .values(
            connector_status=status,
            last_attempted=log.checked_at,
            latency_ms=log.latency_ms,
            records_fetched=log.records_fetched,
        )
    )

def _run_status_to_health_state(self, run_status: RunStatus) -> str:
    mapping = {
        "SUCCESS": "HEALTHY",
        "PARTIAL": "DEGRADED",
        "DEGRADED": "DEGRADED",
        "FAILED": "ERROR",
    }
    return mapping.get(run_status, "ERROR")
```

**Canonical 8-state health enum and state-determination logic:**

| State | Condition |
|:---|:---|
| `HEALTHY` | Last run SUCCESS within freshness window, error rate 0% |
| `DEGRADED` | PARTIAL success OR latency > 3000ms OR parse errors > 0 |
| `STALE` | Last success > freshness window (e.g. batch connector >24h old) |
| `RATE_LIMITED` | HTTP 429 received in last run |
| `AUTH_FAILED` | HTTP 401 or 403 received |
| `ERROR` | Exception raised / connection refused after all retries |
| `DISABLED` | `Source.status == "disabled"` |
| `NEVER_CONNECTED` | `Source.last_success IS NULL` and `connector_status IS NULL` |

**Aggregation endpoint** — single query with `max(checked_at)` group by `source_id`:
```python
# GET /api/v1/sources/health — uses a window function to avoid N+1
latest_logs = (
    select(SourceHealthLog)
    .distinct(SourceHealthLog.source_id)
    .order_by(SourceHealthLog.source_id, SourceHealthLog.checked_at.desc())
)
```

---

### G. Calibration Lifecycle Idempotency

**Pattern: `CalibrationRun` entity + `CalibrationFeedback.is_applied` flag**

```python
# POST /api/v1/calibration/run — the only mutation endpoint
async def trigger_calibration_run(db: AsyncSession) -> CalibrationRunResponse:
    # 1. Fetch only UNAPPLIED feedback
    stmt = select(CalibrationFeedback).where(CalibrationFeedback.is_applied == False)
    result = await db.execute(stmt)
    feedback_items = result.scalars().all()

    if not feedback_items:
        return CalibrationRunResponse(status="no_pending_feedback", feedback_count=0)

    # 2. Snapshot current weights
    current_weights = await _fetch_current_weights(db)

    # 3. Compute new weights (existing StakeholderCalibrationService logic)
    new_weights = await calibration_service.recalibrate(feedback_items, current_weights)

    # 4. Create immutable CalibrationRun record
    run = CalibrationRun(
        triggered_at=utc_now(),
        feedback_count=len(feedback_items),
        previous_weights=current_weights,
        new_weights=new_weights,
        status="completed",
    )
    db.add(run)
    await db.flush()  # get run_id

    # 5. Mark feedback as applied — idempotency guard
    for fb in feedback_items:
        fb.is_applied = True
        fb.applied_at = utc_now()
        fb.calibration_run_id = run.run_id

    # 6. Persist new weights
    await _apply_weights(db, new_weights)

    await db.commit()
    return CalibrationRunResponse(run_id=run.run_id, status="completed", ...)
```

**GET /api/v1/calibration** — purely read-only, returns current weights + run history:
```python
@router.get("/calibration")
async def get_calibration_state(db: AsyncSession = Depends(get_db)):
    # Read-only: no mutations, no side effects
    weights = await _fetch_current_weights(db)
    runs = await _fetch_run_history(db, limit=10)
    pending_count = await _count_unapplied_feedback(db)
    return CalibrationWeightsResponse(weights=weights, run_history=runs, pending_feedback_count=pending_count)
```

---

### H. Testing Patterns

**Backend invariant tests:**
```python
# tests/test_truthfulness_and_invariants.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_calibration_does_not_mutate_db(async_client: AsyncClient, db_session):
    """GET /calibration must be idempotent — no DB writes."""
    before = await db_session.execute(select(func.count()).select_from(CalibrationFeedback))
    await async_client.get("/api/v1/calibration")
    after = await db_session.execute(select(func.count()).select_from(CalibrationFeedback))
    assert before.scalar() == after.scalar()

@pytest.mark.asyncio
async def test_contradiction_excerpts_are_not_placeholders(async_client, db_session):
    """Red-team excerpts must not contain the placeholder string 'Primary evidence claim'."""
    resp = await async_client.get("/api/v1/red-team")
    items = resp.json()
    for item in items:
        assert "Primary evidence claim" not in (item.get("claim_a_excerpt") or "")
        assert "Contradicting evidence claim" not in (item.get("claim_b_excerpt") or "")
```

**Failure injection with `pytest-httpx`:**
```python
# tests/test_failure_injection.py
import pytest
from pytest_httpx import HTTPXMock

@pytest.mark.asyncio
async def test_pubmed_timeout_produces_degraded_health(httpx_mock: HTTPXMock, db_session):
    httpx_mock.add_exception(httpx.ReadTimeout("Simulated timeout"))
    connector = PubMedConnector()
    result = await connector.run_profile(db_session, "haemophilia_a")
    assert result.status in ("DEGRADED", "FAILED")
    assert result.error_detail is not None

@pytest.mark.asyncio
async def test_newsapi_429_handled_gracefully(httpx_mock: HTTPXMock, db_session):
    httpx_mock.add_response(status_code=429, json={"message": "Rate limit exceeded"})
    connector = NewsAPIConnector()
    result = await connector.run_profile(db_session, "haemophilia_a")
    assert result.status == "FAILED"
    # Verify health log entry was persisted
    log = await db_session.execute(
        select(SourceHealthLog).where(SourceHealthLog.source_id == "newsapi")
        .order_by(SourceHealthLog.checked_at.desc()).limit(1)
    )
    entry = log.scalar_one_or_none()
    assert entry is not None
    assert entry.connector_status == "RATE_LIMITED"
```

**Frontend component tests with Vitest + React Testing Library:**
```ts
// frontend/__tests__/ErrorState.test.tsx
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ErrorState } from '@/components/common/ErrorState'

test('shows retry button when onRetry is provided', async () => {
  const onRetry = vi.fn()
  render(<ErrorState message="Network error" onRetry={onRetry} />)
  await userEvent.click(screen.getByRole('button', { name: /retry/i }))
  expect(onRetry).toHaveBeenCalledOnce()
})

test('copies correlation ID to clipboard', async () => {
  const writeText = vi.fn()
  Object.assign(navigator, { clipboard: { writeText } })
  render(<ErrorState message="Err" requestId="req-1234-abcd" />)
  await userEvent.click(screen.getByRole('button', { name: /copy correlation id/i }))
  expect(writeText).toHaveBeenCalledWith('req-1234-abcd')
})
```

**Vitest config (no Next.js ejection):**
```ts
// frontend/vitest.config.ts
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tsconfigPaths from 'vite-tsconfig-paths'

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
  },
})
```

---

## Don't Hand-Roll

| Domain | Don't Build | Use Instead |
|:---|:---|:---|
| JSON logging | Custom JSON formatter | `structlog` with `JSONRenderer` |
| Request ID generation/propagation | Custom ASGI middleware from scratch | `asgi-correlation-id` + `CorrelationIdMiddleware` wrapper above |
| Secret scrubbing | Per-call regex | Global `_scrub_secrets` structlog processor (defined once) |
| pgvector distance | Raw SQL strings | SQLAlchemy `column.op("<=>")(embedding)` |
| HTTP mocking for tests | `unittest.mock.patch` on httpx | `pytest-httpx` (`HTTPXMock` fixture) |
| Pydantic JSONB mapping | Custom `TypeDecorator` from scratch | Existing `score_breakdown = Column(JSONB)` pattern already in Signal model — just enforce through Pydantic validation in `ScoreBreakdownSchema(**s.score_breakdown)` |
| Frontend test runner | Playwright / full Cypress | `vitest` + `@testing-library/react` (no browser needed) |
| Drawer/Sheet component | Custom portal | Existing shadcn/Base UI `Sheet` or `Dialog` primitives in `frontend/components/ui/` |

---

## Common Pitfalls

### Python / Backend
1. **`asyncpg` + `contextvars` fork**: `asyncpg` connection pools use `asyncio.Task` under the hood — `contextvars` propagate correctly in Python 3.11+ but **only within the same task tree**. Background tasks spawned with `asyncio.create_task()` do NOT inherit the parent's contextvars unless you explicitly pass the context: `asyncio.create_task(coro(), context=contextvars.copy_context())`.

2. **Alembic `server_default` vs `default`**: `server_default` (a SQL expression) is required for columns added to tables with existing rows. `default` (a Python callable) is evaluated only on `INSERT` — it does NOT retroactively populate existing rows. Always use `server_default='false'` (string) for boolean columns and `server_default='live'` for enum string columns.

3. **pgvector `<=>` operator requires `pgvector.sqlalchemy.Vector`**: The `op("<=>")(embedding)` pattern works only if the column is defined with `Vector(384)` from `pgvector.sqlalchemy`. Do not pass a plain Python list as the right-hand side — it must be cast to a compatible type. Use `func.cast(embedding_list, Vector(384))` if needed.

4. **SQLAlchemy async + `selectinload` in endpoints**: The existing `intelligence.py` uses nested queries (N+1 pattern for signals-per-confluence). Replace with `selectinload` or batch the signal IDs and use `WHERE signal_id IN (...)`.

5. **`calibration_feedback` double-application**: Without `is_applied` guard, every call to `recalibrate()` re-processes ALL historical feedback, causing weight drift unboundedly. The `is_applied` column + the `WHERE is_applied = false` filter is mandatory.

6. **`utc_now()` without `timezone=True`**: All `DateTime` columns must use `DateTime(timezone=True)`. Columns defined without `timezone=True` store naive datetimes — comparison with `datetime.now(timezone.utc)` produces a `TypeError` in Python 3.11+. The existing models are correct; new migrations must follow the same pattern.

### Frontend
7. **Next.js 16 App Router + `use client` boundaries**: Server components cannot import client components that use hooks or browser APIs. When extracting from `metaradar.tsx`, carefully check each component for `useState`, `useEffect`, `useRef` — these require `"use client"` directive at the top of the file.

8. **Vitest with Next.js `@` path alias**: Without `vite-tsconfig-paths` plugin, `@/components/...` imports fail in Vitest. Install `vite-tsconfig-paths` and add it to `vitest.config.ts`.

9. **`any` in generated `api.ts`**: The OpenAPI generator may produce `any` for `JSONB` / untyped fields. Add manual type overrides in `frontend/types/overrides.ts` and re-export with explicit types.

---

## Code Examples

### Confirmed Bug Fix #1 — Red-Team Placeholder Excerpts (intelligence.py:158-159)
```python
# BEFORE (placeholder — FORBIDDEN):
claim_a_excerpt=f"Primary evidence claim for {c.claim_a_id}",
claim_b_excerpt=f"Contradicting evidence claim for {c.claim_b_id}",

# AFTER (real evidence lookup):
# In GET /red-team endpoint — join Evidence records
async def _fetch_claim_excerpt(db: AsyncSession, claim_id: str) -> Optional[str]:
    """Fetch verbatim evidence excerpt by signal_id or evidence_id."""
    try:
        signal_uuid = uuid.UUID(claim_id)
    except ValueError:
        return None
    stmt = (
        select(Signal.content)
        .where(Signal.signal_id == signal_uuid)
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    return row[:400] if row else None  # first 400 chars verbatim

# In get_red_team_contradictions():
for c in contradictions:
    excerpt_a = await _fetch_claim_excerpt(db, c.claim_a_id)
    excerpt_b = await _fetch_claim_excerpt(db, c.claim_b_id)
    items.append(ContradictionItem(
        ...
        claim_a_excerpt=excerpt_a,        # None if not found — not a placeholder string
        claim_b_excerpt=excerpt_b,
    ))
```

### Confirmed Bug Fix #2 — Fake Confidence Heuristic (intelligence.py:193)
```python
# BEFORE (mislabeled as confidence — FORBIDDEN):
confidence = min(0.95, 0.5 + (0.05 * (overdue // 10))) if overdue > 0 else 0.5

# AFTER (honest naming + separate field):
# Remove `confidence` from MissingSignalWatchItem entirely
# Add explicit fields:
#   overdue_heuristic_score: Optional[float]   # = 0.5 + 0.05*(overdue//10) — honest label
#   days_overdue: int
#   watch_status: str  # WITHIN_WINDOW | DUE | OVERDUE | SATISFIED | SUPPRESSED | INSUFFICIENT_DATA

def _compute_watch_status(age_days: int, window: int) -> str:
    overdue_days = age_days - window
    if overdue_days > 30:
        return "OVERDUE"
    elif overdue_days > 0:
        return "DUE"
    elif age_days >= 0:
        return "WITHIN_WINDOW"
    return "INSUFFICIENT_DATA"
```

### Confirmed Bug Fix #3 — Mock Data Removal (frontend/lib/mock-data.ts)
```ts
// DELETE: frontend/lib/mock-data.ts (entire file, after verifying no imports remain)
// All data must come from real API calls via frontend/lib/api.ts

// Verify no imports before deletion:
// grep -r "mock-data" frontend/src/ frontend/app/ frontend/components/
// If found: replace the import with a real useLiveData hook call
```

---

## Migration Strategy

1. **Create migration `004_p7_provenance.py`** (see Architecture Patterns B above) with additive nullable columns.
2. Run `alembic upgrade head` against local PostgreSQL — verify no errors.
3. Run `pytest tests/test_contract_drift.py` to ensure schema drift tests still pass.
4. Never use `--autogenerate` for this migration — write it manually to avoid dropping/recreating existing indexes.
5. After migration: update `backend/app/models/__init__.py` to add `SourceHealthLog`, `CalibrationRun` classes and add new columns to existing models.
6. Export updated OpenAPI schema: `python scripts/export_openapi.py`.

---

## Test Patterns

### Test matrix additions for Phase 07
```
tests/
├── test_truthfulness_and_invariants.py    # NEW: invariant tests
│   ├── test_get_calibration_is_readonly
│   ├── test_contradiction_excerpts_not_placeholder
│   ├── test_missing_signal_confidence_not_used
│   ├── test_priority_score_has_breakdown_or_null
│   ├── test_confluence_score_from_db_not_hardcoded
│   └── test_source_health_reflects_connector_state
│
├── test_failure_injection.py              # NEW: failure injection
│   ├── test_pubmed_timeout_degraded_health
│   ├── test_newsapi_429_rate_limited_state
│   ├── test_database_disconnect_500_with_request_id
│   ├── test_redis_unavailable_graceful_fallback
│   └── test_correlation_id_present_on_error_response
│
└── test_contract_drift.py                 # EXISTING: extend for new schemas
    └── test_004_migration_schemas_in_contract
```

### Frontend test matrix (new)
```
frontend/__tests__/
├── ErrorState.test.tsx       # retry, clipboard copy, details toggle
├── EmptyState.test.tsx       # distinguishes empty vs error vs loading
├── EvidenceDrawer.test.tsx   # renders source, URL, excerpt
├── SignalCard.test.tsx        # score null → "Not computed" label
└── DataModeBadge.test.tsx    # live vs recorded_demo badge rendering
```

**Key vitest commands to add to `package.json`:**
```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```
