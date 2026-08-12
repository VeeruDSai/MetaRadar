# Coding Conventions

**Analysis Date:** 2026-08-13

> **Status note:** `CLAUDE.md` states *"Conventions not yet established. Will populate as patterns emerge during development."* The repository is specification-first (docs only), so the conventions below are **prescriptive** — derived from the canonical spec ([`docs/METARADAR_MASTER_PLAN_v3.0.md`](docs/METARADAR_MASTER_PLAN_v3.0.md)) and SRS, to be followed when implementation begins.

## Naming Patterns

**Files (docs — current, observed):**
- Numbered spec docs: `{N}_{UPPER_TOPIC}.md` — e.g., `2_SRS_Software_Requirements_Specification.md`, `9_RISK_AND_GUARDRAILS.md`
- Research docs: `{Author}_{topic}.md` — e.g., `Ishaaq_research-1.md`
- Every doc carries a version stamp (e.g., "v2.1", "v3.0") and a pointer to the master plan as canonical

**Functions (prescribed):**
- `snake_case` — e.g., `node_ingest`, `node_nlp_extract`, `build_prompt`, `build_pipeline` (SDD code samples in `docs/3_SOFTWARE_DESIGN_DOCUMENT.md`)
- LangGraph nodes prefixed `node_` consistently

**Variables:**
- `snake_case` for Python; constants in `UPPER_SNAKE_CASE` — e.g., `LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "google/gemma-3-4b-it")` (`docs/1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md`)

**Types/Classes:**
- `CamelCase` for classes/services — e.g., `StakeholderCalibrationService`, `NarrativeSynthesizer` (SDD)
- Domain types: `Signal`, `Development`, `Entity`, `Function` (SRS §2 term definitions)

## Code Style

**Formatting:**
- No formatter/linter config exists yet (no `pyproject.toml`, `.prettierrc`, `eslint.config.*`). For Python, follow PEP 8 and `black`-compatible formatting; for TS/React, follow Next.js 15 + shadcn/ui conventions.

**Linting:**
- Not configured yet. Recommended once code lands: `ruff` (Python), ESLint (Next.js default).

## Import Organization

**Order (prescribed by sample code in `docs/3_SOFTWARE_DESIGN_DOCUMENT.md`):**
1. Standard library
2. Third-party (fastapi, httpx, langgraph, transformers, spacy)
3. Local modules
4. Env/config imports via `config.py` module (SDD line ~242: `config.py  # Environment variables`)

**Path Aliases:**
- None defined yet. Backend package root is `app` (`backend/app/...` per `README.md` "Project Structure").
- Keep `main.py` at `backend/app/main.py` as the FastAPI entry.

## Error Handling

**Patterns (prescribed):**
- **External API failures:** `tenacity` exponential backoff (3 retries: 2s, 4s, 8s); fallback cascade Redis cache → bronze DB → 500-signal synthetic dataset; 100% graceful degradation, zero dashboard crashes (`CLAUDE.md` "Resilience & Calibration", `docs/9_RISK_AND_GUARDRAILS.md` R11)
- **LLM load failure:** auto-fallback from Gemma 3 4B → BART summarizer, logged and surfaced in UI (`docs/9_RISK_AND_GUARDRAILS.md` R6)
- **Low-confidence retrieval:** evidence-sufficiency gate blocks generation — return *"Insufficient evidence to support an interpretation."* (R1)
- **API auth errors:** raise `HTTPException(401, "Invalid credentials")` (SDD line ~1543)

## Logging

**Framework:** Standard library logging (prescribed; no external logger).

**Patterns:**
- Log fallback events (Gemma → BART) so degradation is visible (`docs/9_RISK_AND_GUARDRAILS.md` R6)
- WORM `audit_log` table (append-only, 21 CFR Part 11-style) for calibration history and ontology changes — never overwrite/delete audit rows (`CLAUDE.md`, `docs/9_RISK_AND_GUARDRAILS.md` R10/R15)
- Data-freshness + source-health status surfaced in UI, not just logs (R5/R11)

## Comments

**When to Comment:**
- Document AI/domain decisions that are non-obvious (F-I-S labeling rules, WATCH wording guardrails, fallback chains)
- Spec docs already encode the rationale — implementation comments should reference them

**JSDoc/TSDoc:**
- Not prescribed. Use minimal docstrings on public Python functions/services (FastAPI endpoints, LangGraph nodes, service methods).

## Function Design

**Size:**
- Single-responsibility per LangGraph node (10 nodes, one concern each) — mirror this in plain functions (`docs/METARADAR_MASTER_PLAN_v3.0.md` §4)

**Parameters:**
- Prefer config via env vars over hard-coded values — *"Model names SHALL be configurable via environment variables (never hard-coded)"* (SRS NFR, line ~570). Example: `LOCAL_LLM_MODEL`, `SUMMARIZER_MODEL`.

**Return Values:**
- Structured/typed where possible (Pydantic models for FastAPI; dataclasses for signals/developments)
- Every lifecycle event returns `event_type · event_date · development_id · source_id` (node_lifecycle contract)

## Module Design

**Exports:**
- LangGraph node functions (`node_*`) exported from `backend/app/agents/`; services from `backend/app/services/`
- Keep the FastAPI entry (`main.py`) thin — routers in `backend/app/api/`

**Barrel Files:**
- Not used/prescribed. Prefer explicit imports.

## Guardrail Conventions (non-negotiable)

- **No secrets in code** — env vars only, `.env` gitignored (SRS NFR, `docs/9_RISK_AND_GUARDRAILS.md` R14)
- **Public + synthetic data only** — no confidential/patient data; PII/PHI scrubbed before persistence (R14)
- **F-I-S labeling on every AI output** — speculation never presented as fact (R1/R2)
- **Controlled action vocabulary only** — monitor · review · prepare_internal_briefing · prepare_scientific_faq · escalate · request_stakeholder_review · no_immediate_action (R13)
- **Human review required** — AI suggests, human decides (R13/R19)

---

*Convention analysis: 2026-08-13*
