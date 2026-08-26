# Development Conventions & Standards (CONVENTIONS.md)

**Project:** MetaRadar — Autonomous Decision Intelligence Platform  
**Milestone:** v5.2  
**Last Updated:** 2026-08-27  

---

## 1. Design System & CSS Rules

- **CSS Token Enforcement:** All styles must use CSS custom properties defined in `globals.css` (`var(--surface)`, `var(--surface-secondary)`, `var(--border)`, `var(--foreground)`, `var(--muted-foreground)`, `var(--primary)`, `var(--warning)`, `var(--danger)`, `var(--success)`).
- **Banned Classes:** No hardcoded hex colors (e.g. `#1e293b`) or default `slate-*` Tailwind utility classes.
- **Automated Gate:** Every frontend commit must pass `node scripts/check-banned-classes.mjs` with 0 violations.
- **Responsive Layout:** Dynamic layouts must support mobile, tablet, and widescreen desktop breakpoints cleanly.

---

## 2. API Contract & Type Safety

- **Contract Synchronization:** TypeScript interfaces in `frontend/types/api.ts` must maintain strict parity with FastAPI Pydantic schemas in `backend/app/schemas/`.
- **Export Script:** Schema modifications require editing the template in `scripts/export_openapi.py`, running `python scripts/export_openapi.py`, and committing both `contracts/openapi.json` and `frontend/types/api.ts`.
- **Zero Type Suppressions:** No `@ts-ignore`, `any` type casting where strict DTOs exist, or `ignoreBuildErrors: true` in `next.config.mjs`.

---

## 3. Truthfulness & Provenance Invariants

- **No Synthetic Leaks:** In `data_mode="live"`, signals must never contain fabricated test fixtures or synthetic tags.
- **Honest Telemetry:** Connector health statuses (`HEALTHY`, `DEGRADED`, `UNHEALTHY`, `CONFIGURATION_ERROR`) must reflect real operational results.
- **Provenance Honesty:** Canonical URLs must point to specific record endpoints (PubMed, NCT study, Drugs@FDA, EPAR, Fierce/ET Pharma direct link) or report `missing_url`. Generic portal homepages are strictly blocked.

---

## 4. Backend Database & Async Standards

- **SQLAlchemy 2.0 Async:** Use `async_session_factory()` for database interactions.
- **Synchronous `.add()`:** Note that SQLAlchemy `session.add(instance)` is synchronous even on an `AsyncSession` — never await `session.add()`.
- **Immutable Audit Logging:** Every review status change or administrative action must insert an immutable `AuditLog` row before committing.
