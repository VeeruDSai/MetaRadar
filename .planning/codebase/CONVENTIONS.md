# Coding Conventions

**Analysis Date:** 2026-08-28

## Naming Patterns

**Files & Folders:**
- Python backend modules: `snake_case.py` (e.g., `backend/app/services/vector_query.py`, `backend/app/connectors/clinical_trials.py`)
- Frontend React components: `PascalCase.tsx` (e.g., `frontend/components/signals/SignalCard.tsx`, `frontend/components/intelligence/AthenaWorkspace.tsx`)
- Frontend utilities, hooks, and helpers: `camelCase.ts` (e.g., `frontend/lib/api.ts`, `frontend/lib/hooks.ts`)
- TypeScript types: `frontend/types/api.ts`

**Functions & Methods:**
- Python: `snake_case` (e.g., `get_domain_config()`, `compute_priority_score()`, `extract_entities()`)
- TypeScript: `camelCase` (e.g., `fetchSignals()`, `useSignalDetail()`, `formatDate()`)
- React Components: `PascalCase` (e.g., `EvidenceDrawer()`, `PersonaSwitcher()`)

**Variables & Constants:**
- Local variables: `snake_case` (Python), `camelCase` (TypeScript)
- Global constants & Config settings: `UPPER_SNAKE_CASE` (e.g., `DATABASE_URL`, `RAW_SIGNAL_RETENTION_DAYS`, `MAX_CONTEXT_TOKENS`)

**Types & Interfaces:**
- Python Pydantic Models & SQLAlchemy Classes: `PascalCase` (e.g., `SignalCreate`, `SignalResponse`, `RawSignalBronze`, `User`)
- TypeScript Interfaces & Types: `PascalCase` (e.g., `Signal`, `PriorityScore`, `HealthStatusResponse`)

## Code Style

**Formatting:**
- Python: Formatted with standard PEP 8, 4-space indentation, clear docstrings on public services and routers.
- TypeScript / React: Formatted with 2-space indentation, semicolons enabled, clean JSX structure.

**Linting:**
- Python: Clean type hints with `typing` module (`List`, `Optional`, `Dict`, `Any`, `UUID`).
- Frontend: ESLint 10.8.1 with Next.js rules (`frontend/eslint.config.mjs`). Banned classes checked via `scripts/check-banned-classes.mjs`.

## Import Organization

**Python Backend:**
```python
# 1. Standard library imports
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

# 2. Third-party library imports
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

# 3. Application internal imports
from app.core.config import settings
from app.db.session import get_db
from app.models import Signal
from app.schemas.intelligence import SignalResponse
from app.services.scoring import compute_priority_score
```

**TypeScript / React Frontend:**
```typescript
// 1. React and Next.js core
import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";

// 2. Third-party UI & icon libraries
import { motion, AnimatePresence } from "framer-motion";
import { Shield, Sparkles, AlertTriangle, ArrowRight } from "lucide-react";

// 3. Application context & hooks
import { useAuth } from "@/context/AuthContext";
import { useSignals } from "@/lib/hooks";

// 4. Application types and utilities
import { Signal, PriorityLevel } from "@/types/api";
import { cn, formatDate } from "@/lib/utils";
```

## Error Handling

**Backend Strategy:**
- Use FastAPI `HTTPException` with explicit status codes (400, 401, 403, 404, 422, 500) and descriptive detail strings.
- Graceful degradation for external connectors: If an external API (e.g., NewsAPI or PubMed) times out or returns an error, catch the specific exception, log it via `structlog`, update the connector's health status in `source_health_logs`, and return available results without crashing the application.
- LLM Provider fallback cascade: If local Gemma inference is unavailable, fall back to Grok or BART summarizer.

**Frontend Strategy:**
- All API client methods in `frontend/lib/api.ts` wrap network calls with structured error catching (`frontend/lib/errors.ts`).
- Component-level error boundaries and `<ErrorState />` UI components provide retry buttons and clear failure messages.

## Logging

**Framework:**
- Backend: Structured JSON logging with `structlog` (`backend/app/core/logging.py`).
- Correlation IDs: Injected on every request via `asgi-correlation-id` and `backend/app/core/middleware.py`.

**Patterns:**
```python
# Use event name as first positional parameter followed by structured key-values:
logger.info("ingestion_connector_started", source="pubmed", query="haemophilia")
logger.warning("connector_rate_limited", source="newsapi", retry_after=60)
logger.error("pipeline_execution_failed", error=str(e), signal_id=str(signal_id))
```

## Security & Privacy Invariants

1. **Zero Secrets in Code:** Secrets and API keys must only be loaded via environment variables in `backend/app/core/config.py`.
2. **Audit Immutability:** Records in `audit_log` are strictly append-only. SQLAlchemy before-update and before-delete event listeners raise `PermissionError` on any modification attempts.
3. **Privacy Boundary:** Internal patient or sensitive pipeline data must never be transmitted to third-party LLMs without PII redaction (`backend/app/services/pii.py`).
4. **RBAC Verification:** Protected endpoints verify user persona permissions through dependency injection (`app/api/v1/endpoints/auth.py`).

---

*Convention analysis: 2026-08-28*
