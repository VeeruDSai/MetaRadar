# Phase 08: Provenance Traceability + Canonical Overview/Lifecycle Design System Hardening — Research

**Researched:** 2026-08-20
**Domain:** Full-stack provenance traceability (connector → raw record → signal → API → UI) + frontend design-system/theme unification
**Confidence:** HIGH (all findings verified by reading the actual source files this session; low-confidence items explicitly tagged)

## Summary

Phase 08 fixes two systemic problems: (1) **provenance does not survive the pipeline** — real source identifiers and canonical URLs are dropped at the bronze→signal hop, and multiple layers (backend serializer, frontend mapper, health endpoints, confluence inspector) fabricate values to mask the gaps; (2) **the design system is not unified** — `/dashboard` and `/lifecycles` are token-clean, but every other workspace is riddled with hardcoded `slate`/hex Tailwind classes that break light mode and violate the UI-SPEC banned list.

The single highest-leverage backend defect is in `backend/app/workflows/nodes/ingest.py:69-71`: the signal dict is rebuilt with `payload.get("signal_type", "CLINICAL_TRIAL")` and `payload.get("url", "")`, but **no connector ever writes `url` or `signal_type` into the `raw_payload` JSONB** — so every live signal is persisted as `signal_type=CLINICAL_TRIAL` with `canonical_url=""`, and confluence never fires on live data. The second is `backend/app/workflows/runner.py:240-241`: `data_mode="live"` is hardcoded and synthetic fallback records (which lack `is_synthetic`) are persisted as live, non-synthetic data. On the frontend, `frontend/lib/mappers.ts` invents signal IDs, scores, confidence, source names, and stakeholders; `frontend/components/common/DataModeBadge.tsx:13` renders `test_fixture` and synthetic records as "Recorded Demo Data".

**Primary recommendation:** Fix provenance at the source (connectors write `url`/`signal_type`/`external_id`/`evidence_text` into `raw_payload`; runner stops hardcoding `data_mode`; synthetic fallback labeled before persistence), then delete every fabrication (serializer, mapper, health endpoints, confluence fallbacks), then sweep the frontend to semantic tokens using the canonical `panel`/`eyebrow`/`muted`/`Badge`/`SectionTitle` patterns from `frontend/components/metaradar.tsx`. Backend is authoritative; frontend never reconstructs provenance.

<user_constraints>
## User Constraints (from CONTEXT.md)

> 08-CONTEXT.md contains no separate "the agent's Discretion" or "Deferred Ideas" sections. Every directive below is a locked decision. Copied verbatim.

### User Constraints & Directives (verbatim, 08-CONTEXT.md lines 9-55)

1. **End-to-End Source Provenance Is the Highest-Priority Issue**: For every signal shown anywhere in MetaRadar, the user must be able to answer: what source produced it, what exact record/document/study/article, the canonical public URL, the source's own identifier, publication time, MetaRadar ingest time, which connector fetched it, whether content is live/cached/seeded/synthetic/test, the exact evidence text, and what transformation happened between source and signal.
   - Audit the entire chain: source connector → raw response → normalized record → database record → Signal → serializer → frontend mapper → SignalCard → EvidenceDrawer/inspector → source link.
   - Do NOT create fake provenance to make the UI look complete.
   - If a real canonical source URL cannot be derived, display an explicit `SOURCE URL UNAVAILABLE` state and explain why. Never show a fabricated URL.

2. **Every Signal Needs a Real Provenance Object**: Create/normalize a single provenance contract (conceptually `source_id`, `source_name`, `source_type`, `connector_id`, `external_id`, `canonical_url`, `published_at`, `ingested_at`, `retrieved_at`, `evidence_text`, `raw_record_reference`, `fingerprint`, `is_synthetic`, `is_test_fixture`) adapted to the actual project architecture. Provenance must survive the complete backend → API → frontend path. The backend is authoritative — the frontend must NOT reconstruct provenance from title/source-name heuristics.

3. **Source-Specific Identifiers** (inspect each connector's actual payload and determine the strongest stable identifier and canonical URL):
   - **PubMed**: preserve PMID; canonical URL → PubMed record; NCBI E-utilities are the official interface; show PMID + source URL in the evidence inspector.
   - **ClinicalTrials.gov**: preserve NCT ID; canonical URL → the specific study; use API v2 (do not silently rely on legacy endpoints); preserve the study identifier independently of the generated signal ID.
   - **FDA/openFDA**: preserve the FDA record identifier; build canonical URLs only when the record type actually has a stable public URL; do not confuse an API endpoint with the human-readable source record.
   - **EMA**: preserve the specific document/feed/item URL whenever available; do not merely label something "EMA"; retain originating RSS feed/item info (news, new medicines, EPARs, regulatory material).
   - **NewsAPI**: preserve the article URL returned by NewsAPI, publisher/source name, and publication date; do not treat newsapi.org itself as the article source.

4. **Raw Source / Evidence Inspector**: Improve EvidenceDrawer with clear sections: `SOURCE PROVENANCE` (Provider, Source ID, External ID, Published, Ingested, Retrieved, Canonical Source, [Open Original Source]), then `VERBATIM EVIDENCE` (exact source-derived text that generated the signal), then `TRACE` (Connector → Raw record → Normalized record → Signal → Score; each missing stage says `NOT AVAILABLE` — do not invent intermediate records). Clicking "Open Original Source" must leave MetaRadar and open the exact NCT study / PMID / real source.

5. **Synthetic Data Must Be Impossible to Confuse With Live Data**: Audit all seed/demo/test records. Every synthetic record must visibly say `TEST FIXTURE` or `SYNTHETIC`, never look like live intelligence. Explicitly mark fake-looking UUIDs/fingerprints/timestamps/source IDs. Do not manufacture public URLs for synthetic records; if a fixture intentionally tests provenance, use a clearly labeled fixture URL/reference.

6. **Source Page Must Be Operationally Honest**: `HEALTHY`/`DEGRADED`/`UNHEALTHY`/`NEVER_CONNECTED` must correspond to actual connector telemetry. HTTP 200 with 0 records fetched ≠ healthy. Display: HTTP status, records fetched, records accepted, last successful sync, last attempted sync, latency, error, auth/config state. Distinguish "HTTP reachable" from "successfully ingesting usable records".

7. **API Key / Environment Configuration**: Inspect `.env` and `.env.example`. If required keys are missing: report exactly (missing var, required-or-optional, official location, short steps to obtain). Do NOT invent values, do NOT put placeholder-like fake secrets into source control. Provider facts: PubMed/NCBI E-utilities public (API key for higher rates), ClinicalTrials.gov API v2 public (no invented key), openFDA public (API key for higher limits — verify actual connector behavior before declaring mandatory), EMA RSS public (no credentials), NewsAPI requires a key (official account flow), xAI requires `XAI_API_KEY` when fallback enabled (official xAI Console/API Keys page). Missing credential → `CONFIGURATION_ERROR: <VAR> missing` (never just `UNHEALTHY`).

8. **Canonical Design System**: `/dashboard` and `/lifecycles` are the canonical visual reference pages. Do NOT redesign them. Extract their actual design tokens (typography, spacing, hierarchy, cards, borders, muted text, headings, labels, badges, density) and make every other workspace consume those same tokens. Audit: `/signals`, `/confluence`, `/missing-signals`, `/developments`, `/intelligence`, `/functions`, `/calibrate`, `/sources`, `/observability`, `/settings`, `/red-team`, `/contradictions`, all drawers/modals/inspectors.

9. **Font Consistency**: Identify the actual font stack used by Overview/Lifecycles and enforce it globally. Audit font family, weight, size, line height, letter spacing, uppercase labels, heading hierarchy, numeric typography, monospace usage. No arbitrary fonts per workspace. Monospace only where semantically appropriate (IDs, fingerprints, API/source IDs, logs, technical values). Normal UI text must use the same primary font as Overview/Lifecycles.

10. **Typography Hierarchy**: Standardize levels: page eyebrow, page title, page description, section eyebrow, section title, card title, body, muted metadata, numeric metric, badge, technical identifier. Overview and Lifecycles are the reference implementation. No per-page different heading sizes.

11. **Light/Dark Theme Must Be a Single System**: The previous ThemeProvider fix is not sufficient if components still contain hardcoded dark colors. Search the entire frontend for `bg-slate-`, `text-slate-`, `border-slate-`, `bg-[#...]`, `text-[#...]`, `border-[#...]`, dark-only values, inline color styles. Replace with shared semantic design tokens. Theme state must survive page navigation, client-side navigation, browser refresh, opening/closing drawers, changing workspaces/tabs, and direct URL navigation. Theme stored once and read by the root application theme provider — do NOT duplicate theme state inside individual pages. The observed bug (switch to light → navigate to another tab → returns to dark) must be impossible.

12. **Light Mode Must Be a Real Theme**: Do not merely invert the dark UI. Define semantic tokens for: background, surface, surface elevated, border, primary text, secondary text, muted text, accent, success, warning, danger, info, input, hover, selected, overlay, drawer, code/log surface. Both themes use the same component structure/spacing; only semantic colors change.

13. **Drawers / Modals**: Audit EvidenceDrawer and Confluence inspector specifically. They must use the same typography, surface hierarchy, border treatment, spacing, button style, badges, form controls, and theme tokens as Overview/Lifecycles. Drawer must remain readable in both themes.

14. **Priority Score**: Keep the previous 4-factor model `P = 0.25×Novelty + 0.30×Clinical + 0.25×Regulatory + 0.20×Recency`. Verify database values, backend serializer, API response, frontend mapper, SignalCard, and EvidenceDrawer all use the exact same value. One authoritative calculation. No frontend recalculation unless explicitly required. No silent fallback to 0. If a score genuinely cannot be calculated, expose the reason.

15. **Confluence Semantics**: The UI says "Multi-source convergence" and "≥3 distinct source types required" while some displayed confluences have only 1 independent source — contradictory. Fix the logic or the UI; backend rule and frontend wording must agree. Do not hide the inconsistency. Every contributing evidence item must be independently traceable to its original source.

16. **Source Traceability in Confluence**: For each contributing evidence signal show: signal title, source provider, external ID, publication date, canonical URL, evidence excerpt. Inspector must allow walking backward: Confluence → contributing signal → source record → original public source.

17. **Observability**: Logs must make source ingestion debuggable. Per ingestion attempt record: connector, request, status, latency, records fetched, records accepted, records rejected, reason for rejection, created signals, updated signals, errors. Do not log API secrets. Missing key → `CONFIGURATION_ERROR: NEWSAPI_KEY missing` rather than just `UNHEALTHY`.

18. **Validation**: After implementation run `pytest tests/`, `npm run lint`, `npm run build`. Then manually verify: dark↔light switch; navigate every workspace; refresh; open a signal; open evidence drawer; open source; return; open Confluence; inspect evidence; open source; go to Sources; trigger ingestion; inspect connector telemetry; go to Settings; verify credential status; repeat in dark mode. Also test direct URL navigation.

19. **Do NOT Accept "Build Passes" as Completion**: Completion requires every live signal traceable, canonical URLs where they exist, synthetic clearly labeled, source identifiers survive the full pipeline, evidence verbatim/source-derived, priority scores consistent end-to-end, Confluence source-count semantics truthful, connector health reflects actual ingestion, missing credentials explicitly reported, no fabricated credentials, Overview/Lifecycles typography canonical, all workspaces share font hierarchy + spacing/card/border system, light/dark globally persistent, client navigation never resets theme, drawers/modals use the same design system, no hardcoded theme colors, and all tests/lint/build pass.

### Key Architecture & Implementation Decisions (verbatim, 08-CONTEXT.md lines 61-72)

- **D-08-01 (Provenance Object Is Authoritative in Backend)**: A single normalized provenance structure flows from DB → serializer → API → frontend mapper → UI. Frontend never derives provenance from titles or heuristics.
- **D-08-02 (Truthful URL States)**: `canonical_url` is either a real, provider-canonical URL or an explicit `SOURCE URL UNAVAILABLE` state with a reason — never fabricated.
- **D-08-03 (Source-Specific Identifier Preservation)**: PMID / NCT ID / FDA ID / EMA item URL / NewsAPI article URL are preserved end-to-end independent of generated signal IDs.
- **D-08-04 (Evidence Is Verbatim)**: The evidence excerpt is the exact source-derived text; intermediate trace stages display `NOT AVAILABLE` when absent.
- **D-08-05 (Synthetic Visibility)**: Synthetic/test-fixture records are unmistakably badged `TEST FIXTURE` / `SYNTHETIC`; no manufactured public URLs for fixtures.
- **D-08-06 (Honest Connector Health)**: Source status reflects actual ingestion telemetry (HTTP + records fetched/accepted + last syncs + latency + errors + auth state), not HTTP 200 alone.
- **D-08-07 (Explicit Credential Reporting)**: Missing credentials reported as `CONFIGURATION_ERROR: <VAR> missing` with exact env var, required/optional, official location, and steps; no fabricated values.
- **D-08-08 (Canonical Design System)**: Design tokens extracted from `/dashboard` and `/lifecycles` become the single source of truth for all workspaces and drawers.
- **D-08-09 (Single Theme Store)**: Theme persisted once at the root provider and read globally; no per-page theme state; both light and dark are real semantic token themes.
- **D-08-10 (Single Priority Calculation)**: The 4-factor formula is calculated once (backend) and flows end-to-end; no silent zero fallback; reasons exposed when incalculable.
- **D-08-11 (Truthful Confluence Semantics)**: Confluence rule (≥3 distinct source categories) and UI wording agree; contributing evidence individually traceable.
- **D-08-12 (Debuggable Ingestion)**: Per-attempt ingestion logs capture connector/request/status/latency/records/errors without secrets.
</user_constraints>

<phase_requirements>
## Phase Requirements

> `.planning/REQUIREMENTS.md` does not assign numeric REQ-IDs to phase 08; the requirements ARE the 19 user directives and 12 D-08 decisions above, plus the UI-SPEC acceptance checklist (08-UI-SPEC.md, sections §2-§5 and the per-connector rules at lines 540-544). The planner should treat each row below as a requirement.

| ID | Description | Research Support |
|----|-------------|------------------|
| DIR-1 / D-08-01..04 | End-to-end provenance object survives connector → DB → API → UI; backend authoritative | §Per-Connector Provenance Mapping, §API Contract Changes, §Data Model & Migration Requirements |
| DIR-3 / D-08-03 | PMID/NCT/FDA/EMA-item/NewsAPI-article identifiers preserved | §Per-Connector Provenance Mapping (verified payload keys per connector) |
| DIR-4 | EvidenceDrawer: SOURCE PROVENANCE / VERBATIM EVIDENCE / TRACE sections + Open Original Source + SOURCE URL UNAVAILABLE | §Frontend Design System & Theme Changes; verified current drawer lacks all three sections |
| DIR-5 / D-08-05 | Synthetic/test-fixture unmistakably labeled; no manufactured URLs | runner.py:240-241, DataModeBadge.tsx:13, synthetic_signals.json URL analysis (§Data Model & Migration Requirements) |
| DIR-6 / D-08-06 | Connector health = real ingestion telemetry | §Observability Changes; verified /sources + /sources/health fabrications |
| DIR-7 / D-08-07 | Missing credential → `CONFIGURATION_ERROR: <VAR> missing` | §Credential/Config Audit Findings; verified newsapi.py DEGRADED path |
| DIR-8..13 / D-08-08..09 | Canonical design system from dashboard/lifecycles; single theme store; no banned classes | §Frontend Design System & Theme Changes; verified canonical components in metaradar.tsx |
| DIR-14 / D-08-10 | Single 4-factor priority calc end-to-end; no frontend recalculation; no silent zero | §Priority Score Consistency; verified mappers.ts split + serializer re-scoring |
| DIR-15..16 / D-08-11 | Confluence semantics truthful (≥3 distinct source types) and traceable | §Confluence Semantics; verified signal_type vs source_type mismatch |
| DIR-17 / D-08-12 | Per-attempt ingestion observability without secrets | §Observability Changes; verified structlog scrubber + ingestion logging gaps |
| DIR-18..19 | Validation: pytest, lint, build + manual UI matrix; completion = behavior, not build-pass | §Validation Architecture |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Provenance object construction (source_id, external_id, canonical_url, timestamps, evidence) | API / Backend (DB + connectors) | — | D-08-01: backend is authoritative; connectors own the raw facts (PMID, NCT, article URL) |
| canonical_url truthfulness (real URL vs SOURCE URL UNAVAILABLE) | API / Backend | — | Only the backend knows whether a stable public URL exists; frontend must render state, never guess |
| Synthetic/test-fixture labeling | API / Backend (persistence) | Browser / Client (rendering) | `data_mode`/`is_synthetic` written at insert (runner.py); UI only renders the badge |
| Connector health / telemetry | API / Backend | — | Sources + SourceHealthLog tables hold the truth; health endpoints must read them, not ConnectorState-only |
| Credential/config state (`CONFIGURATION_ERROR`) | API / Backend | — | env vars are read in config.py; endpoint must translate absence into status |
| Priority score computation | API / Backend | — | D-08-10: one authoritative calculation in services/scoring.py; frontend renders only |
| Design tokens (semantic colors, typography) | Browser / Client (CSS) | — | globals.css `:root`/`.dark` variables + Tailwind `@theme inline` mapping |
| Theme persistence | Browser / Client (ThemeProvider) | — | D-08-09: single root provider, localStorage + FOUC script (already correct) |
| Page/workspace layout, cards, drawers | Browser / Client | — | All workspaces consume canonical `SectionTitle`/`Card`/`Badge`/token classes |
| Confluence detection rule (≥3 distinct source types) | API / Backend | — | ConfluenceEngine + node_confluence must count source types, and UI copy must match |
| Ingestion observability logs | API / Backend (structlog) | — | Per-attempt records in source_health_logs + structlog events |

## Standard Stack / Libraries

This phase is a **code-and-config refactor**: it adds **no new runtime dependencies**. All needed capabilities exist in the verified stack below.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| structlog | >=24.1.0 `[VERIFIED: backend/requirements.txt:18]` | Structured JSON logging with secret scrubbing | Already configured (`core/logging.py`); per-attempt ingestion events extend it |
| SQLAlchemy 2.0 (async) | >=2.0.28 `[VERIFIED: backend/requirements.txt:5]` | ORM + `pg_insert(...).on_conflict_do_update` upserts | Runner persistence already uses it; provenance columns extend Signal/Source models |
| Alembic | >=1.13.1 `[VERIFIED: backend/requirements.txt:7]` | Migrations | Migration 005 extends 004's schema; `alembic upgrade head` |
| FastAPI + Pydantic v2 | >=0.110.0 / >=2.6.0 `[VERIFIED: backend/requirements.txt:1,3]` | API + response schemas | Serializer/health endpoints rewritten against schemas; contract sync regenerates `types/api.ts` |
| Tailwind CSS v4 | ^4.3.3 `[VERIFIED: frontend/package.json:39]` | Utility CSS with `@theme inline` token mapping | globals.css already maps `--color-*` → tokens; banned-utility sweep uses tokens |
| Next.js 16 + React 19 | 16.3.0 / ^19 `[VERIFIED: frontend/package.json:21-23]` | App router, `[section]/page.tsx` routing | Component sweep must preserve routing; ThemeProvider/FOUC already correct |
| asgi-correlation-id | >=4.3.0 `[VERIFIED: backend/requirements.txt:19]` | X-Request-ID propagation | Invariant 4 test (test_truthfulness_and_invariants.py:132-146) guards it |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langgraph | >=0.2.0 `[VERIFIED: backend/requirements.txt:16]` | Pipeline orchestration | node_ingest/runner changes touch state dicts it threads |
| fastembed | >=0.4.0 `[VERIFIED: backend/requirements.txt:17]` | Signal embeddings | runner.py embedding generation (unchanged) |
| httpx | >=0.27.0 `[VERIFIED: backend/requirements.txt:11]` | Connector HTTP | Connector payload changes |
| recharts | ^3.10.1 `[VERIFIED: frontend/package.json:24]` | Dashboard charts | Canonical pages only (not in scope to change) |
| framer-motion | ^13.1.0 `[VERIFIED: frontend/package.json:19]` | Drawer animations | SignalDrawer/Confluence inspector use it |
| pytest + pytest-asyncio + pytest-httpx | >=8.0.0 / >=0.23.0 / >=0.30.0 `[VERIFIED: backend/requirements.txt:13-14,20]` | Test framework | New provenance/truthfulness tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Editing raw_payload keys in each connector | A central mapping layer in node_ingest | Central layer cannot recover data the connector never captured (e.g. NewsAPI article URL is nested) — fix at the source |
| New UI component library (shadcn/ui primitives exist already) | Writing new components | shadcn `Button` exists (`components/ui/button.tsx`) but the canonical shell uses hand-rolled `.panel`/`.badge` classes — keep the existing system, do not introduce a parallel one |
| New state library for theme | React Context (existing ThemeProvider) | D-08-09 mandates single root store — already implemented; only hardcoded classes remain |

**Installation:** none (no new packages). Backend deps already installed per `backend/requirements.txt`; frontend per `frontend/package.json` (pnpm 9.15.5 declared, but pnpm is NOT on PATH — npm 11.4.2 available as fallback; see Environment Availability).

## Package Legitimacy Audit

> No external packages are installed by this phase — it is a refactor of existing code. The seam gate is therefore N/A for new packages. The existing stack was verified against the repo manifests (`backend/requirements.txt`, `frontend/package.json`) — all long-lived, high-download, source-attributable packages. No `[SLOP]`/`[SUS]` verdicts apply.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| *(no new packages — phase is code/config refactor)* | — | — | — | — | N/A | Approved (no installs) |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram (provenance data flow)

```
Provider record (PMID/NCT/FDA-ID/EMA item/NewsAPI article)
   │  connector fetch (connectors/*.py)
   ▼
RawSignalBronze row  ── raw_payload JSONB  ★ GAP-1: connectors never store "url"/"signal_type"
   │  node_ingest (workflows/nodes/ingest.py)  ★ GAP-2: rebuilds dict, defaults CLINICAL_TRIAL + "" url
   ▼
normalized signal dict  ── (fallback: synthetic_signals.json entries injected AS-IS ★ GAP-3: no data_mode/is_synthetic keys)
   │  node_validate / node_nlp_extract / node_scoring
   ▼
Signal row (runner.py _persist_state_to_db)  ★ GAP-4: data_mode="live" hardcoded; is_synthetic=False; FDA API-URL fallback
   │  api/v1 endpoints  ★ GAP-5: _serialize_signal re-scores (novelty_distance=0.5) + fabricates confidence 0.85
   ▼
JSON API response  ── SignalSchema (★ lacks source_name, external_id, ingested_at, provenance_status)
   │  frontend/lib/mappers.ts  ★ GAP-6: fabricates id/score/confidence/source/stakeholders
   ▼
UI: SignalCard → EvidenceDrawer  ★ GAP-7: score||50, no provenance sections, banned classes
        └─ DataModeBadge  ★ GAP-8: test_fixture/synthetic rendered as "Recorded Demo Data"

Health path:  ConnectorState (health.py) ─★ only, ignores sources/source_health_logs
              /sources (registry.py:81) ─★ fabricates "LIVE" from status=="active"
              /sources/health (observability.py:135-136) ─★ fabricates http_code=200 on HEALTHY
Confluence path: signals.signal_type (all "CLINICAL_TRIAL" live) → distinct_types=={CLINICAL_TRIAL} → never fires live
              intelligence.py:183-185/277/297 ─★ fabricates score=75.0 / independent_sources_count=3
```

### Recommended Project Structure (no new folders required)

```
backend/app/
├── connectors/*.py      # ADD: write url/signal_type/external_id/evidence into raw_payload; EMA keep "link", NewsAPI flatten article
├── workflows/nodes/ingest.py  # FIX: read payload keys; synthetic fallback tagged is_synthetic=True/data_mode="test_fixture"
├── workflows/runner.py  # FIX: data_mode from signal dict; provenance fields in on_conflict set_
├── api/v1/endpoints/signals.py   # REMOVE fabrication; serialize stored score_breakdown only
├── api/v1/endpoints/{health,ingestion,registry,observability}.py  # read real telemetry; CONFIGURATION_ERROR
├── services/ingestion.py  # FIX: records_rejected semantics; http_status recording; min-records rule
├── schemas/*.py          # ADD: source_name, external_id, ingested_at, provenance_status, configuration_error_message, last_attempted
└── alembic/versions/005_*.py  # NEW migration
frontend/
├── components/metaradar.tsx        # CANONICAL reference (do not modify)
├── lib/mappers.ts                  # REMOVE fabrication; map real fields; null-safe
├── lib/api.ts                      # REMOVE fallback fabrication (momentum||70 etc.)
├── components/{signals,sources,confluence,common,functions,developments,missing-signals,intelligence,calibration,observability,settings,contradictions}/*.tsx  # token sweep + provenance sections
└── types/api.ts                    # regenerated via scripts/export_openapi.py
```

### Pattern 1: Provenance survives via raw_payload, not parallel plumbing
**What:** Each connector writes its native identifiers into the `raw_payload` JSONB dict (`external_id`, `url`, `signal_type`, `evidence_text`, `source_name`). `node_ingest` copies those keys through unchanged; `runner.py` persists them onto the Signal row; the serializer emits them; the mapper passes them through. One contract, defined by the backend.
**When to use:** Every connector; every signal path (live + synthetic).
**Example (connector-side, source-derived from verified payload keys):**
```python
# Source: derived from verified connector code (backend/app/connectors/*.py raw_payload dicts)
# PubMed (pubmed.py) must add:  raw_payload["url"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
# ClinicalTrials (clinical_trials.py) must add: raw_payload["url"] = f"https://clinicaltrials.gov/study/{nct_id}"
# NewsAPI (newsapi.py) must flatten: raw_payload["url"] = article["url"]; raw_payload["source_name"] = article["source"]["name"]
# EMA (ema.py) already stores "link"; node_ingest must read payload.get("link") as fallback for url
# openFDA (fda.py): do NOT set url for API records -> canonical_url stays None -> SOURCE URL UNAVAILABLE
```

### Pattern 2: Honest state rendering (SOURCE URL UNAVAILABLE)
**What:** UI branches on `canonical_url` truthiness plus `data_mode`:
- real URL → `<a href={canonical_url}>Open Original Source ↗</a>`
- null/empty + live → `SOURCE URL UNAVAILABLE` + reason (e.g., "openFDA API record has no stable public URL")
- test_fixture/synthetic → `SOURCE URL UNAVAILABLE (test fixture)` — no fabricated URL
**When to use:** EvidenceDrawer, SignalCard, ConfluenceWorkspace contributing-signals list (currently silently omits the link at line 179).
**Example:** UI-SPEC §3.3 (08-UI-SPEC.md lines 221-242) specifies both branches.

### Anti-Patterns to Avoid
- **Fallback-value fabrication:** `x || 75.0`, `x || 3`, `|| 'live'`, `|| 0.85`, `|| 50`, `|| '200 OK'`, `|| 'confluence_v2.0'` — every one of these hides a missing value behind a plausible-looking constant. Replace with explicit null/`NOT AVAILABLE` rendering. (Found at: intelligence.py:183-185,277,297; signals.py:111-114,134; mappers.ts:87-186; api.ts fetchOverview/fetchHealth; SourcesOperationsWorkspace.tsx:178; ConfluenceWorkspace.tsx:45-51,131-134; EvidenceDrawer.tsx:104.)
- **Re-scoring on read:** `_serialize_signal` re-invoking `score_text` with `novelty_distance=0.5` (signals.py:57-77) and the mapper splitting totals into 25/30/25/20 (mappers.ts:110-139) both violate D-08-10 — the score is computed once at pipeline time and stored; reads render stored values.
- **Hardcoded theme classes:** `bg-slate-*`/`text-slate-*`/`border-slate-*`/`bg-[#...]`/`dark:`-paired-with-hardcoded-light — UI-SPEC BANNED list (08-UI-SPEC.md:21). 100+ occurrences across workspace components.

## Data Model & Migration Requirements

### Verified current schema (evidence-based)
- **Signal** (migration 004 `backend/alembic/versions/004_phase7_truthfulness_and_provenance.py:20-35`): has `data_mode` (String(50), NOT NULL, `server_default='live'`), `is_synthetic` (Boolean, NOT NULL, default false), `confidence_type`, `confidence_rationale`. **No `confidence` column exists** — the serializer's `getattr(s, "confidence", 0.85)` (signals.py:134) always yields the fabricated 0.85. **No `external_id`, `source_name`, `source_type`, `ingested_at`, `evidence_text`, `raw_record_reference`, `provenance_status` columns exist** — provenance must live on `RawSignalBronze` (which has `external_id` + `raw_payload` JSONB + `retrieved_at`) and be copied through at persist time.
- **Source** (migration 004:89-116): `connector_status` (default `'NEVER_CONNECTED'`), `last_attempted`, `latency_ms`, `records_fetched`/`records_accepted`/`records_rejected` (default 0), `http_status`. **No `configuration_error_message` column** — required by D-08-07; add in migration 005.
- **SourceHealthLog** (migration 004:119-133): columns are `id` (UUID PK), `source_id`, `pipeline_run_id`, `checked_at`, `connector_status`, `http_status`, `latency_ms`, `records_fetched/accepted/rejected`, `last_error`, `error_code`. **There is no `log_id` and no `error_message`** — `api/v1/endpoints/ingestion.py:119-124` references `log.log_id`/`log.error_message` and raises `AttributeError` at runtime. Fix to `id`/`last_error`.

### Migration 005 (new) requirements
| Change | Table | Notes |
|--------|-------|-------|
| `configuration_error_message` String(255) nullable | `sources` | `CONFIGURATION_ERROR: NEWSAPI_KEY missing` |
| `source_name` String(100) nullable | `signals` | Denormalized provider display name (backend authoritative) |
| `external_id` String(255) nullable | `signals` | PMID/NCT/FDA-ID/EMA item/NewsAPI article id, preserved end-to-end |
| `ingested_at` timestamptz nullable | `signals` | Set at runner persist; distinct from `retrieved_at` (fetch time) and `published_at` |
| `provenance_status` String(50) nullable | `signals` | e.g. `'complete'`, `'missing_url'`, `'synthetic'` — drives SOURCE URL UNAVAILABLE rendering |
| `evidence_text` Text nullable | `signals` | Verbatim source-derived excerpt (D-08-04) |
| `raw_record_reference` String(255) nullable | `signals` | `raw_signals_bronze.id` reference for TRACE |

**Alternatively** (if migration churn is undesired): compute `source_name`/`external_id`/`ingested_at`/`evidence_text` in the serializer from `RawSignalBronze` joined data — but D-08-01 says the provenance object is authoritative in the backend; a denormalized Signal-side copy survives future raw-signal retention (`RAW_SIGNAL_RETENTION_DAYS=30` in `.env.example:24` purges bronze rows — provenance would vanish with them). **Recommendation: denormalize onto `signals` in migration 005.**

### Verified synthetic-data labeling path (must be fixed)
- `runner.py:240` `data_mode="live",` — hardcoded; **even synthetic fallback records are persisted as live**.
- `runner.py:241` `is_synthetic=bool(sig.get("is_synthetic", False)),` — synthetic fallback dicts from `synthetic_signals.json` carry **no `is_synthetic` key** → persisted `False`. Fix: `node_ingest` fallback path (ingest.py:78) must tag each entry `is_synthetic=True`, `data_mode="test_fixture"`.
- `synthetic_signals.json` records carry `"url": "https://metaradar.internal/signals/syn-0001"` (line 11) — internal fake URLs that would be persisted as canonical_url. Per D-08-05, fixtures must not manufacture public URLs — tag with `provenance_status='synthetic'` and render `SOURCE URL UNAVAILABLE (test fixture)`.
- `seed.py:247-317` starter signals are already honest (`data_mode="test_fixture"`, `is_synthetic=True`, real score_breakdowns) — do not regress them. Note seed.py:302 seeds the FDA record with the API URL as canonical_url — same openFDA issue in seed data.
- `DataModeBadge.tsx:13` — `if (isSynthetic || mode === 'recorded_demo' || mode === 'test_fixture')` renders **"Recorded Demo Data"** (amber). UI-SPEC §2.4 (08-UI-SPEC.md:155-160) requires a prominent **TEST FIXTURE** badge in danger tone; `DataMode` type (types/api.ts:4) has no `"synthetic"` value — label synthetic records via `is_synthetic` and render "SYNTHETIC".

## Per-Connector Provenance Mapping

Verified against connector source this session. `raw_payload` is the JSONB dict stored on `RawSignalBronze`; `node_ingest` (ingest.py:62-74) rebuilds signals from it, reading only `title/content/abstract/published_at/signal_type/disease/url` — **any connector field not in that allowlist is dropped at this hop.**

| Connector | Source record id | Verified payload facts | Canonical URL (current) | Gap & Fix |
|-----------|------------------|------------------------|-------------------------|-----------|
| **PubMed** (pubmed.py) | PMID (stable) | `raw_payload` dict does **not** include `url`; external_id=pmid | Constructed at runner.py:207-208: `https://pubmed.ncbi.nlm.nih.gov/{pmid}/` (also pubmed.py ~line 181) | URL is fine **when PMID survives**; add `url` key to raw_payload at connector time so it survives even if runner reconstruction is bypassed; add `evidence_text` (abstract) |
| **ClinicalTrials** (clinical_trials.py) | NCT ID (stable) | `raw_payload` lacks `url`; external_id=nct_id | runner.py:209-210: `https://clinicaltrials.gov/study/{nct_id}` | Same fix: write `url` at connector time; API v2 used (`clinicaltrials.gov/api/v2`) — keep |
| **openFDA** (fda.py) | FDA application_number | `raw_payload` lacks `url`; **fda.py:144 builds `url = f"https://api.fda.gov/drug/drugsfda.json?search=openfda.application_number:{application_number}"` — an API endpoint, not a human-readable record** | runner.py:211-212 reproduces the same API URL; seed.py:302 same | **Violates DIR-3/D-08-02**: do not set canonical_url for API-only records → `null` + reason `SOURCE URL UNAVAILABLE (openFDA API record has no stable public URL)`; UI-SPEC.md:544 agrees ("Only set canonical_url when record type has a verified stable public URL; otherwise leave null") |
| **EMA** (ema.py) | feed item `link` | raw_payload keeps `"link"` (verified ema.py ~line 162) — **not `"url"`** | Lost: node_ingest reads `payload.get("url", "")` → `""` | ingest.py:71 must fall back to `payload.get("link")`; preserve RSS item info per DIR-3 |
| **NewsAPI** (newsapi.py) | article url + `source.name` | url nested inside `article` dict, **not at top level** | Lost entirely | Flatten at connector: `raw_payload["url"] = article["url"]`, `raw_payload["source_name"] = article["source"]["name"]`; UI-SPEC.md:542 mandates this |
| **Synthetic fallback** (synthetic_signals.json) | `SYN_*` external ids | Entries have `url` = `metaradar.internal` fake URLs; varied `signal_type`; no `data_mode`/`is_synthetic` | Would persist fake URLs as canonical | Tag `is_synthetic=True`/`data_mode="test_fixture"` at ingest.py:78; render `SOURCE URL UNAVAILABLE (test fixture)`; never treat as live |

**Cross-cutting:** `signal_type` — **no connector sets it**; ingest.py:69 defaults `"CLINICAL_TRIAL"`. Result: every live signal is CLINICAL_TRIAL; node_confluence's `distinct_types` set is always `{CLINICAL_TRIAL}`; confluence never fires on live data (synthetic data fires because the JSON has varied types). Fix at connectors (map record type → domain `signal_types` list; verified list in `config/haemophilia.yaml:108-121`: `CLINICAL_TRIAL, PUBLICATIONS, CONGRESS, REGULATORY, COMMERCIAL_PATENT, SAFETY, ACCESS`).

## API Contract Changes

Verified gaps in `frontend/types/api.ts` (auto-generated from OpenAPI via `scripts/export_openapi.py` — line 2) and backend schemas:

| Type / Endpoint | Verified current state | Required change |
|-----------------|------------------------|-----------------|
| `Signal` (types/api.ts:53-100) | No `source_name`, `external_id`, `ingested_at`, `provenance_status`, `evidence_text`, `raw_record_reference`, `is_test_fixture`, `source_type`, `connector_id`; UI section (90-100) forces fabricated `id`, `summary`, `severity`, `status`, `score`, `sources: SignalSource[]`, `stakeholders` | Extend with real provenance fields; keep UI fields optional and stop mapping them from heuristics; `SignalSchema` (backend schemas/__init__.py) lacks `source_name` — add |
| `DataMode` (types/api.ts:4) | `"live" \| "recorded_demo" \| "test_fixture" \| "benchmark"` | Fine as-is; synthetic handled via `is_synthetic` (per D-08-05) |
| `ConnectorHealthStatus` (types/api.ts:172-186) | No `configuration_error_message`, no `last_attempted` | Add both; backend `ConnectorHealthStatus` schema too |
| `SourceRegistryItem` (types/api.ts:496-511) | No `configuration_error_message` | Add |
| `GET /api/v1/health/connectors` (health.py) | Reads **ConnectorState only** → telemetry columns stay at defaults (`NEVER_CONNECTED`, 0 records) | Read `sources` + latest `source_health_logs`; surface `configuration_error_message` |
| `GET /api/v1/sources` (registry.py:81) | `connector_status="LIVE"` fabricated when `s.status=="active"` — `"LIVE"` is not even in the canonical enum | Remove; map from `connector_status` telemetry |
| `GET /api/v1/sources/health` (observability.py:97-158) | Reads Source+SourceHealthLog correctly but **fabricates `http_code=200` when HEALTHY** (135-136); omits `configuration_error_message` (no such field) | Emit real http_status (null when not probed); include configuration_error_message |
| `POST /api/v1/ingestion/run` (ingestion.py:119-124) | **Runtime `AttributeError`**: references `log.log_id`, `log.error_message` — model has `id`, `last_error` | Fix attribute names; add regression test |
| `GET /api/v1/signals` serializer (signals.py `_serialize_signal`) | Re-scores with `novelty_distance=0.5` (57-77); splits totals 25/30/25/20 (71-76); on-the-fly scoring (82-102); `data_mode or "live"` (111-114); `confidence = getattr(s, "confidence", 0.85) or 0.85` (134) | Emit stored `score_breakdown` verbatim; drop confidence fabrication (render `confidence_type`/`confidence_rationale` when present, else omit); no default data_mode |
| `GET /api/v1/overview` (endpoints/intelligence.py) | `score=75.0`/`independent_sources_count=3` fabricated when no signals (183-185); `or 3` (277, 297) | Remove; emit null/0 honestly |

**Contract sync note:** after schema changes run the generator so `frontend/types/api.ts` regenerates (quality gate `contract_sync: true` in .planning/config.json).

## Frontend Design System & Theme Changes

### Verified canonical reference (do NOT modify)
- `frontend/components/metaradar.tsx` — `Shell`, `Badge` (`.badge badge-{tone}`), `Card` (`.panel`), `SectionTitle` (`.section-title`/`.eyebrow`/h1/`.muted`), `KPI`, `SignalRow`, `SignalDrawer` (`.drawer-backdrop`, `.signal-drawer`, `.drawer-score`, `.calibration-widget-card`, `.role-pill`) — **pure semantic classes, zero hardcoded Tailwind color utilities** (lines 110-148, 427-558, 760-938, 1663+).
- `DashboardPage` (760-938) and `LifecyclePage` (1089-1149) are the visual reference: `SectionTitle` + `kpi-grid` + `bento-grid` + `Card` + `empty-state`/`muted`/`eyebrow`/`text-link`/`icon-link`; LifecyclePage uses token var() references (`text-[var(--muted-foreground)]`, `bg-[var(--surface-secondary)]`, `border-[var(--border)]` — lines 1113-1133). These var() references are compliant (token-based; only `#...`/`slate` literals are banned).
- `frontend/app/globals.css` — complete semantic token set in BOTH themes: light `:root` (lines 31-59: `--background:#f1f5f9`, `--surface:#fbfdff`, `--surface-secondary:#eef4f8`, `--surface-elevated:#ffffff`, `--foreground:#16263a`, `--muted-foreground:#607286`, `--primary:#2563c7`, `--accent:#159a9c`, `--success/warning/danger`, priority colors, `--panel`) and `.dark` (62-88) mirrored; `@theme inline` mapping (7-27) exposes `bg-surface`, `text-muted-foreground`, `border-border`, etc. Body font: `Arial, Helvetica, sans-serif` (line 92) — the canonical font stack to enforce globally (DIR-9).
- Theme architecture (ThemeProvider + FOUC inline script in layout.tsx) is **already correct** (D-08-09): single root provider, localStorage `metaradar_theme`, `.dark` class toggling. The remaining theme bug source is **hardcoded classes inside components** — the observed "returns to dark" bug disappears once components stop pinning light/dark pairs.

### Verified violations to fix (banned classes + fabricated data)
| File | Verified violation |
|------|--------------------|
| `sources/SourcesOperationsWorkspace.tsx` | h1 `text-xl font-bold text-slate-900 dark:text-slate-100` (74); `getStatusBadge` hardcoded emerald/amber/red/slate classes (49-68, no CONFIGURATION_ERROR case → falls into NEVER_CONNECTED branch); `{s.http_status \|\| '200 OK'}` fabricated 200 (178); `records_accepted \|\| 0` (174); telemetry gaps: no records_fetched/rejected, no last_attempted, no configuration_error_message display |
| `confluence/ConfluenceWorkspace.tsx` | h1 slate (64); fabricated fallbacks `score \|\| 75.0` (45), `independent_sources_count \|\| 3` (46,49,51), `reasoning` (51), `calculation_version \|\| 'confluence_v2.0'` (134); copy claims "≥3 distinct source types required" (66,99) — backend counts signal_types; contributing-signal URL silently omitted when absent (179); modal overlay/drawer banned classes (202-204); inspect fallback fabricates a full response when endpoint unavailable (41-54) |
| `common/EvidenceDrawer.tsx` | Banned classes throughout (61-63,70,74-85,93,110-124); `Total: ... \|\| `${signal.score \|\| 50} pts`` (104) fabricated score; **missing** SOURCE PROVENANCE / VERBATIM EVIDENCE / TRACE sections (DIR-4); no External ID, no Retrieved/Ingested, no "Open Original Source" button, no SOURCE URL UNAVAILABLE state |
| `signals/SignalCard.tsx` | Banned classes; consumes mapper-fabricated score/confidence; no provenance row |
| `common/DataModeBadge.tsx` | Line 13-22: test_fixture + synthetic → "Recorded Demo Data" amber badge; never "TEST FIXTURE"/"SYNTHETIC"; violates UI-SPEC §2.4 (danger tone) |
| `lib/mappers.ts` | Fabrications: random id `SIG-${Math.random()...}` (87); score default 50 / priority→fixed 85/70/50/30 (93-108); frontend 25/30/25/20 score split (110-139, D-08-10 violation); confidence default 85 (141); source name uppercased from source_id + credibility 90 (147-155); fabricated stakeholders (158-163); `data_mode \|\| 'live'`, `scoring_status \|\| 'computed'` (182-186) |
| `lib/api.ts` | fetchOverview fabricates `momentum \|\| 70`, `confidence \|\| 85`, `latencyMs \|\| 120`; fetchHealth hardcodes `latencyMs: 85, sourceCount: 6` |
| `metaradar.tsx` DashboardPage fallback (778-789) | Fallback overview object with `health: { latencyMs: 12, sourceCount: 5 }` — only used while loading/error; acceptable as empty-state skeleton if labeled, but numbers must not masquerade as telemetry |
| `components/ui/button.tsx`, `shadcn` primitives | Existing shadcn Button exists; canonical pages use `.icon-button`/`.retry-button` classes — keep existing pattern |

**Sweep procedure:** replace banned utilities with tokens (UI-SPEC §4 table, 08-UI-SPEC.md:171-182): `bg-white dark:bg-slate-900` → `var(--surface-elevated)`; `bg-slate-50 dark:bg-slate-950/60` → `var(--surface-secondary)`; `border-slate-200 dark:border-slate-800` → `var(--border)`; `text-slate-900 dark:text-slate-100` → `var(--foreground)`; `text-slate-600 dark:text-slate-400` → `var(--muted-foreground)`; `bg-slate-100 ... text chip` → `.badge .badge-neutral`. Headers use `<SectionTitle eyebrow=... title=... detail=... />` (UI-SPEC:408). Scope per UI-SPEC §5: all workspaces except `/dashboard` and `/lifecycles`; drawers/modals included.

## Credential/Config Audit Findings

Verified this session:

| Env var | Required? | Verified status | Reporting gap |
|---------|-----------|-----------------|---------------|
| `NEWSAPI_KEY` | Yes (NewsAPI has no anonymous tier) | `.env.example:25` `NEWSAPI_KEY=` (empty placeholder); no `.env` in repo (gitignored — only `.env.example` present) | `newsapi.py:77-86` returns **DEGRADED** with "NEWSAPI_KEY not set" → must be `CONFIGURATION_ERROR: NEWSAPI_KEY missing` (D-08-07) |
| `XAI_API_KEY` | Only when `ENABLE_GROK_FALLBACK=true` | `.env.example:15` empty; `ENABLE_GROK_FALLBACK=false` (14) — verified in config.py | No live reporting surface; when enabled and key missing → same CONFIGURATION_ERROR pattern |
| PubMed / ClinicalTrials / openFDA / EMA | Public (key optional for higher limits) | No keys configured — correct, no invented keys | None |
| `DATABASE_URL`, `REDIS_URL` | Yes | `.env.example:2-3` defaults for local Docker | None |

**Plumbing:** `backend/app/core/config.py` exposes `NEWSAPI_KEY: Optional[str]`, `XAI_API_KEY: Optional[str]`, `ENABLE_GROK_FALLBACK: bool=False`. The health/registry endpoints must surface `configuration_error_message` (new column, migration 005) populated at connector init when a required key is absent — never just UNHEALTHY/DEGRADED. No fake secrets anywhere: `.env.example` placeholders are empty strings (verified lines 15, 25) — keep it that way.

## Observability Changes

Verified baseline: `backend/app/core/logging.py` — structlog JSON, `_scrub_secrets` (SENSITIVE_KEYS lines 7-11, REDACTED_SECRET/REDACTED_PII), `configure_structlog(json_logs=True)` on import; `X-Request-ID` via asgi-correlation-id (tested in test_truthfulness_and_invariants.py:132-146). SourceHealthLog table (migration 004:119-133) already models per-attempt records: connector_status, http_status, latency_ms, records_fetched/accepted/rejected, last_error, error_code, checked_at, pipeline_run_id.

Gaps to close (D-08-12 / DIR-17):
1. `services/ingestion.py` marks **HEALTHY on SUCCESS even when 0 records fetched** — add a minimum-records rule (0 fetched → DEGRADED with reason), and set `records_rejected` from actual rejection counts, not `conn_dups` (duplicates ≠ rejected).
2. `http_status` is **never recorded** into Source/SourceHealthLog — record the real connector HTTP status per attempt.
3. Per-attempt structlog events must include: connector, request/url, status, latency, records fetched/accepted/rejected, rejection reason, signals created/updated, errors — without secrets (scrubber already guards).
4. Fix `ingestion.py:119-124` `log.log_id`/`log.error_message` → `id`/`last_error` (AttributeError).
5. NewsAPI missing key path must emit `CONFIGURATION_ERROR: NEWSAPI_KEY missing` into status + log (observability.py/health surfaces).

## Confluence Semantics

Verified mismatch (D-08-11 / DIR-15):
- **Backend counts distinct `signal_type` values**: `ConfluenceEngine` (services/confluence.py) and `node_confluence` (workflows/nodes/confluence.py) group by `signal_type`; the regression test `test_truthfulness_and_invariants.py:88-104` asserts "2 signals from different signal types -> should not meet threshold" and "3 signals from 3 distinct signal types -> eligible" — **the test locks the signal_type semantics**.
- **UI copy claims source types**: ConfluenceWorkspace.tsx:66 "≥3 distinct source types required" and :99 "≥3 independent signal types converge". The domain term "source types" ≠ `signal_type` (CLINICAL_TRIAL/PUBLICATIONS/CONGRESS/REGULATORY/... per haemophilia.yaml:108-121).
- **Confluence never fires on live data** because all live signals are `signal_type=CLINICAL_TRIAL` (ingest.py:69 default) → `distinct_types == {"CLINICAL_TRIAL"}` — so live confluences are impossible today; synthetic data fires (varied types in JSON).
- **Fabricated values**: intelligence.py:183-185 (`score=75.0`, `independent_sources_count=3` with no signals), :277/:297 (`or 3`); ConfluenceWorkspace fallback inspect (41-54).

**Decision for the planner:** align semantics on **source types** (source_id-based) per the user's directive (DIR-15: "backend rule and frontend wording must agree"), or rename UI copy to "signal types". Research recommendation: use **distinct `source_id` values** (the actual independent sources: pubmed, clinical_trials, fda, ema, newsapi — 5 canonical sources, seed.py:29-38) and update the node + ConfluenceEngine + the invariant test. Thresholds verified: `minimum_independent_signals: int = 3`, `time_window_hours: int = 48`, `emerging_threshold: int = 2` (domain_config.py:30-33 and config/haemophilia.yaml:135-138).

## Priority Score Consistency

Verified end-to-end (D-08-10 / DIR-14):
- **Authoritative formula** lives in `backend/app/services/scoring.py`: `0.25 × novelty + 0.30 × clinical + 0.25 × regulatory + 0.20 × recency`, `SCORING_VERSION = "haemophilia_v2.0"`; `score_text` has default `novelty_distance=0.5` (12.5/25 pts) — a silent fabricated novelty when distance is not provided; must be called with a real distance or omitted.
- **DB**: `Signal.score_breakdown` JSONB stores the breakdown (seed rows verified with real values, seed.py:262-269 etc.).
- **Violations:**
  - Serializer re-runs `score_text(text, published_at, novelty_distance=0.5)` when breakdown missing (signals.py:57-77) and splits totals 25/30/25/20 (71-76), plus on-the-fly scoring (82-102) — re-computation on read.
  - Mapper splits total into 25/30/25/20 proportions (mappers.ts:110-139) — **explicitly forbidden** ("No frontend recalculation unless explicitly required").
  - EvidenceDrawer `signal.score \|\| 50` (line 104); SignalCard consumes mapper score; `confidence` fabricated 0.85 (signals.py:134) and 85 (mappers.ts:141).
- **Fix:** read path emits stored `score_breakdown` unchanged; when `score_breakdown` is null → `scoring_status: "not_computed"` + reason, never a recomputed or defaulted number. `signal.score` derived on the backend once.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured logging + secret scrubbing | Custom JSON logger | structlog with existing `_scrub_secrets` (logging.py) | Already implemented and tested (invariant 3) |
| DB schema evolution | Hand-written ALTERs | Alembic migration 005 | 004 pattern exists; `alembic upgrade head` |
| API schema generation | Hand-edited `types/api.ts` | `scripts/export_openapi.py` contract sync | File header says "DO NOT EDIT DIRECTLY"; quality gate `contract_sync` |
| DB upserts | Manual select-then-insert races | `pg_insert(Signal).on_conflict_do_update` (runner.py:220-258) | Already the pattern; extend `set_` with provenance fields |
| Theme persistence | Per-page theme state | Existing ThemeProvider (single root, localStorage + FOUC) | D-08-09; architecture verified correct |
| Tailwind token wiring | New build plugin | Existing `@theme inline` mapping in globals.css | Tokens already mapped (globals.css:7-27) |

**Key insight:** every "hand-rolled" fabrication in this codebase (re-scoring, splitting scores, fake IDs, fake 200s) exists because a value was missing at read time. The durable fix is to make the value exist at write time (connectors + runner), not to add more cleverness at read time.

## Runtime State Inventory

> Phase 08 is a refactor of persistence + API + UI behavior. Inventory of runtime state that holds provenance/telemetry values.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | PostgreSQL: `signals` rows with `data_mode='live'`/`is_synthetic=false` persisted from synthetic fallback (runner.py:240-241); `canonical_url=''` for live rows (URL dropped); FDA rows with API-URL as canonical (runner.py:211-212, seed.py:302); `sources.connector_status` default `NEVER_CONNECTED` untouched by health.py; `source_health_logs` rows with no `configuration_error_message` | **Data migration** (migration 005 backfill): re-label synthetic-origin signals (`fingerprint LIKE 'sig:%'` + source synthetic dataset ids) to `is_synthetic=true`/`data_mode='test_fixture'`; null out API-endpoint canonical_urls where no stable public URL exists; add provenance_status |
| Live service config | Docker Compose Postgres/Redis; no exported workflow/UI config beyond repo | None |
| OS-registered state | None — no Task Scheduler/pm2/launchd registrations found for this project | None |
| Secrets/env vars | `.env` not in repo (gitignored); `.env.example` has empty `NEWSAPI_KEY`/`XAI_API_KEY`; `config.py` reads them as Optional | Code-only: report `CONFIGURATION_ERROR: NEWSAPI_KEY missing` in health surfaces; no key changes |
| Build artifacts | `frontend/types/api.ts` is generated (stale after schema changes); no egg-info/global installs | Regenerate via contract sync; `pnpm install`/`npm install` if node_modules stale |

**Nothing found in category:** OS-registered state — explicitly verified none.

## Common Pitfalls

### Pitfall 1: Fixing the UI instead of the data
**What goes wrong:** Planner touches mappers/drawers only; canonical_url still `""`, data_mode still `"live"`, so the UI has nothing real to show and the fix is cosmetic.
**Why it happens:** Frontend violations are the most visible; backend root causes (ingest.py:69-71, runner.py:240) are easy to miss.
**How to avoid:** Order tasks backend-first: connectors → ingest → runner → serializer → mapper → UI. Verify a live row end-to-end before UI work.
**Warning signs:** UI shows real URLs but DB still has `canonical_url=''`.

### Pitfall 2: "Fixing" the serializer/mapper by recomputing differently
**What goes wrong:** D-08-10 violated again — a new split or re-score in a different layer.
**Why it happens:** Score looks "wrong" in a demo because stored breakdown is absent.
**How to avoid:** Read path is pass-through; missing → `not_computed` + reason.
**Warning signs:** Any `* 0.25` / `/ 100` arithmetic outside scoring.py.

### Pitfall 3: Keeping the signal_type-based confluence while changing UI copy
**What goes wrong:** Copy says "source types" but backend counts signal_types → still contradictory, just reworded.
**Why it happens:** The invariant test (test_truthfulness_and_invariants.py:88-104) locks signal_type semantics.
**How to avoid:** Change backend + test together (distinct source_ids) and update UI copy to match; run pytest to prove agreement.
**Warning signs:** Confluence list shows one source with `independent_sources_count=3`.

### Pitfall 4: Regressing the honest seed data
**What goes wrong:** Seed signals (seed.py:247-317) are correctly tagged test_fixture; a sweep that "normalizes" all rows to live breaks DIR-5.
**Why it happens:** Bulk UPDATE scripts are tempting during backfill.
**How to avoid:** Backfill by fingerprint/`SYN_` origin only; never blanket-update data_mode.
**Warning signs:** Demo shows seed records as "Live Intelligence".

### Pitfall 5: Breaking the theme with var() removal
**What goes wrong:** A sweep replaces `bg-[var(--surface-secondary)]` (compliant) along with banned classes, or introduces a third token set.
**Why it happens:** Grep targets "var(" indiscriminately.
**How to avoid:** Only replace the BANNED list (slate, `#hex`, `dark:`-paired-hardcoded); keep token var() references and `.panel`/`.badge` classes.
**Warning signs:** LifecyclePage visual diff after sweep.

## Code Examples

### Common Operation 1: Persist a live signal with real provenance (runner.py pattern, extended)
```python
# Source: backend/app/workflows/runner.py:220-258 (verified), extended per D-08-01/03
stmt = pg_insert(Signal).values(
    signal_id=sig_uuid,
    fingerprint=fp,
    source_id=source,
    source_name=sig.get("source_name"),          # NEW: from connector raw_payload
    external_id=ext_id,                          # NEW: PMID/NCT/FDA-id/article url-id
    pmid=pmid, nct_id=nct_id, regulatory_id=reg_id,
    title=sig.get("title", ""),
    content=sig.get("content", ""),
    canonical_url=url or None,                   # None -> SOURCE URL UNAVAILABLE
    evidence_text=sig.get("evidence_text"),      # NEW: verbatim excerpt (D-08-04)
    ingested_at=now,                             # NEW: distinct from retrieved_at
    provenance_status=sig.get("provenance_status", "complete" if url else "missing_url"),
    published_at=pub_at, retrieved_at=ret_at,
    signal_type=sig.get("signal_type"),          # REMOVED default "CLINICAL_TRIAL" -> None if unknown
    data_mode=sig.get("data_mode", "live"),
    is_synthetic=bool(sig.get("is_synthetic", False)),
    score_breakdown=sig.get("score_breakdown") or {},
    pipeline_run_id=run_uuid,
).on_conflict_do_update(
    index_elements=["fingerprint"],
    set_={
        "canonical_url": url or None,
        "provenance_status": sig.get("provenance_status", "complete" if url else "missing_url"),
        "data_mode": sig.get("data_mode", "live"),
        "is_synthetic": bool(sig.get("is_synthetic", False)),
        "external_id": ext_id, "source_name": sig.get("source_name"),
        "pmid": pmid, "nct_id": nct_id, "regulatory_id": reg_id,
        "evidence_text": sig.get("evidence_text"),
        "score_breakdown": sig.get("score_breakdown") or {},
        "pipeline_run_id": run_uuid,
    }
)
```

### Common Operation 2: Honest URL rendering in EvidenceDrawer (UI-SPEC §3.3)
```tsx
// Source: 08-UI-SPEC.md lines 221-242 (required behavior)
{signal.canonical_url ? (
  <a href={signal.canonical_url} target="_blank" rel="noreferrer" className="text-link">
    <span>Open Original Source</span>
    <small>{signal.canonical_url}</small>
  </a>
) : (
  <span className="badge badge-danger">
    SOURCE URL UNAVAILABLE{signal.provenance_status === 'synthetic' ? ' (test fixture)' : ''}
  </span>
)}
```

### Common Operation 3: Connector writes url/signal_type at fetch time (NewsAPI flatten)
```python
# Source: derived from backend/app/connectors/newsapi.py raw_payload construction (verified nested article dict)
raw_payload = {
    "title": article.get("title", ""),
    "content": article.get("description", ""),
    "published_at": article.get("publishedAt"),
    "url": article.get("url"),                    # NEW: flattened from article dict
    "source_name": (article.get("source") or {}).get("name"),  # NEW: publisher, not newsapi.org
    "signal_type": "CONGRESS" if "congress" in (article.get("title") or "").lower() else None,
    "disease": "haemophilia_a",
}
```

### Common Operation 4: SourceHealthLog honest read (observability endpoint)
```python
# Source: derived from backend/app/api/v1/endpoints/observability.py:97-158 (verified fabrication at 135-136)
item = {
    "source_id": source.source_id,
    "name": source.name,
    "connector_status": latest.connector_status if latest else source.connector_status,
    "http_status": latest.http_status if latest else None,   # NOT 200-on-HEALTHY fabrication
    "latency_ms": latest.latency_ms if latest else None,
    "records_fetched": latest.records_fetched if latest else 0,
    "records_accepted": latest.records_accepted if latest else 0,
    "records_rejected": latest.records_rejected if latest else 0,
    "last_attempted": latest.checked_at if latest else source.last_attempted,
    "last_error": latest.last_error if latest else None,
    "configuration_error_message": source.configuration_error_message,  # NEW column
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Signals stored with no external_id / source_name / ingested_at | Denormalized provenance columns on `signals` | Phase 08 (migration 005) | Provenance survives raw-signal retention; TRACE works after bronze purge |
| Health = ConnectorState-only or fabricated "LIVE"/200 | Telemetry read from sources + source_health_logs | Phase 08 | DIR-6 honest ops |
| Missing key → DEGRADED/UNHEALTHY | `CONFIGURATION_ERROR: <VAR> missing` | Phase 08 | D-08-07 explicit credential reporting |
| Workspaces with hardcoded slate/hex classes | Semantic tokens via globals.css vars | Phase 08 | Light/dark real in every workspace |
| Mapper/serializer fabricate ids/scores/confidence | Pass-through of stored values + explicit unavailable states | Phase 08 | No fake provenance (DIR-1) |
| Confluence counts distinct signal_types (always 1 on live) | Counts distinct source_ids; UI copy matches | Phase 08 | Truthful confluence semantics (D-08-11) |

**Deprecated/outdated:**
- `"LIVE"` connector_status (registry.py:81) — not a canonical enum value; replace with real `connector_status`.
- `log.log_id` / `log.error_message` references (ingestion.py) — model uses `id`/`last_error` since migration 004.
- `data_mode="live"` hardcoded at insert (runner.py:240) — must come from the signal dict.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `config/haemophilia.yaml` `signal_types` list (7 values) is the authoritative enum the connectors should map into | Per-Connector Provenance Mapping | If another enum exists in code, mapping target differs — verify at plan time against connectors' actual type strings |
| A2 | RawSignalBronze has an `external_id` column that survives into the pipeline (ingest.py:65 reads `row.external_id`) — used as the source of truth for provenance during ingest | Data Model & Migration Requirements | Verified at ingest.py:65; if some connector rows leave it null, fallback to payload-derived ids is needed |
| A3 | No runtime package changes needed; all fixes use the verified stack | Standard Stack | If a new dep is later desired (e.g., a URL validator), the package-legitimacy gate must be re-run |
| A4 | The confluence semantics fix should move to distinct `source_id` counts (research recommendation) | Confluence Semantics | User directive says backend rule and UI wording must agree but does not dictate which side moves; planner should confirm the direction in discuss/plan |
| A5 | Backend `Signal` model columns from migration 004 (`confidence_type`, `confidence_rationale`) are unused by the serializer today | Priority Score Consistency | If they are populated by scoring, the "no confidence column" claim narrows; serializer line 134's `getattr(s, "confidence", 0.85)` proves `confidence` itself doesn't exist |
| A6 | `provenance_status` values proposed (`complete`/`missing_url`/`synthetic`) are a new contract not present anywhere | API Contract Changes | UI-SPEC uses prose states (`SOURCE URL UNAVAILABLE (test fixture)`); exact enum spelling must be locked in plan |

## Open Questions

1. **Confluence semantics direction** — switch backend to distinct `source_id` counts (recommended) or keep `signal_type` and reword UI copy?
   - What we know: backend + invariant test lock signal_type; UI copy says source types; live data can never fire confluence today.
   - What's unclear: user directive (DIR-15) permits either fix.
   - Recommendation: distinct source_ids; update node_confluence, ConfluenceEngine, and the invariant test together; surface counts verbatim in UI.
2. **`external_id` uniqueness contract** — NewsAPI articles have no stable numeric id; what identifies a NewsAPI record across runs (url as id? title+publishedAt hash)?
   - What we know: NewsAPI article dict has `url`; runner fingerprints `sig:{source}:{ext_id}`.
   - What's unclear: dedup behavior for the same article re-fetched.
   - Recommendation: use article URL as external_id for NewsAPI; document in connector.
3. **`confidence` field** — Signal has no confidence column; should phase 08 add one, or drop confidence from the UI?
   - What we know: serializer fabricates 0.85; UI renders `{confidence}%`.
   - What's unclear: whether confidence has a real definition (confidence_type exists but is not populated on signals).
   - Recommendation: drop fabricated confidence; render `confidence_type`/`confidence_rationale` when present, else omit the metric.

## Environment Availability

> Phase 08 has no NEW external dependencies. Verified on this machine (2026-08-20):

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Next.js build/lint | ✓ | v22.19.0 (>=20.9.0 required) | — |
| pnpm | frontend install (`packageManager: pnpm@9.15.5`) | ✗ (not on PATH) | — | npm 11.4.2 (verified) — `npm install` works; or `corepack enable` |
| Python | pytest, backend | ✓ | 3.13.5 | — |
| pytest | Validation gate | ✓ | 9.0.3 | — |
| Docker | PostgreSQL/Redis (compose) | ✓ | 29.5.3 | — |
| psql / redis-cli | manual DB inspection | ✗ (not on PATH) | — | docker exec into compose containers |
| PostgreSQL / Redis | backend runtime | ✓ (via Docker, assumed running) | — | docker compose up |

**Missing dependencies with no fallback:** none — all phase-critical tools available.
**Missing dependencies with fallback:** pnpm (use npm or corepack); psql/redis-cli (use `docker exec`).

## Validation Architecture

> `workflow.nyquist_validation: true` in `.planning/config.json` — Validation Architecture required. Quality gates enabled: pytest, tsc, eslint, next_build, contract_sync.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 (asyncio_mode=auto) + pytest-asyncio + pytest-httpx `[VERIFIED: pytest.ini:1-9, backend/requirements.txt:13-14,20]` |
| Config file | `pytest.ini` (testpaths=tests, pythonpath="backend .", marker `live`) |
| Quick run command | `pytest tests/test_truthfulness_and_invariants.py -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DIR-1/3 | Live signal row carries source_id + external_id + canonical_url after a pipeline run | integration | `pytest tests/test_ingestion.py -x` (+ new provenance assertion) | ✅ (extend) |
| DIR-4 | /signals response contains no fabricated confidence/score | unit/API | new `tests/test_provenance_endpoints.py` | ❌ Wave 0 |
| DIR-5 | Synthetic fallback rows persisted with is_synthetic=true, data_mode=test_fixture | integration | new test in `tests/test_ingestion.py` | ❌ Wave 0 |
| DIR-6 | /sources/health emits real http_status (no 200 fabrication) | API | extend `tests/test_signals_endpoints.py` or `test_truthfulness_and_invariants.py` read-only list | ❌ Wave 0 |
| DIR-7 | NewsAPI missing key → CONFIGURATION_ERROR in /sources/health | unit | new `tests/test_config_errors.py` | ❌ Wave 0 |
| D-08-11 | Confluence counts distinct source_ids; invariant test updated to source_ids | unit | `pytest tests/test_truthfulness_and_invariants.py::test_confluence_engine_threshold -x` (must be edited) | ✅ (edit) |
| D-08-10 | Serializer/mapper never recompute or split scores | API | new assertion: response score_breakdown == stored score_breakdown | ❌ Wave 0 |
| Invariant | `ingestion.py` no longer references log.log_id/log.error_message | API | `pytest tests/test_api_endpoints.py -x` (or new) | ✅ (extend) |
| UI | Banned classes absent (grep gate) | static | `npm run lint` + grep gate script | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_truthfulness_and_invariants.py -x` + `npm run lint`
- **Per wave merge:** `pytest tests/` + `npx tsc --noEmit` + `npm run lint` + `npm run build`
- **Phase gate:** Full suite green + `npm run build` + contract sync regenerated before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_provenance_endpoints.py` — provenance pass-through + no-fabrication assertions (DIR-1..5, D-08-10)
- [ ] `tests/test_config_errors.py` — CONFIGURATION_ERROR paths (DIR-7, D-08-07)
- [ ] `tests/conftest.py` — shared app/client fixture (currently each test file re-imports `app` + ASGITransport inline)
- [ ] Edit `tests/test_truthfulness_and_invariants.py::test_confluence_engine_threshold` — switch to distinct source_ids (D-08-11)
- [ ] Frontend static gate — grep for banned class list (`bg-slate-`, `text-slate-`, `border-slate-`, `bg-[#`, `text-[#`, `border-[#`) in `frontend/components/` as a CI-able script (no frontend test runner installed; do not add one)

## Security Domain

> `security_enforcement` is absent from `.planning/config.json` → treated as enabled.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Internal tool; no auth surface in scope for this phase |
| V3 Session Management | no | None (no sessions; API is internal) |
| V4 Access Control | no | None |
| V5 Input Validation | yes | Pydantic v2 schemas on all API responses/requests; URL rendering uses React escaping — do not introduce `dangerouslySetInnerHTML` for verbatim excerpts |
| V6 Cryptography | no | No new crypto; secrets handled via env vars (never in source control) |

### Known Threat Patterns for {stack}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secret leakage in logs | Information Disclosure | Existing `_scrub_secrets` (logging.py:14-21) — extend SENSITIVE_KEYS if new event fields are added; invariant 3 test guards it |
| XSS via verbatim evidence excerpts (source-derived text rendered in drawer) | Tampering | React text nodes (auto-escaped); never `dangerouslySetInnerHTML`; sanitize any HTML from NewsAPI content |
| SSRF via user-controlled URLs | Spoofing | Canonical URLs are constructed by connectors from provider data (pmid/nct_id), never from user input; "Open Original Source" opens in new tab with `rel="noreferrer"` |
| Fabricated/false data masquerading as live | Spoofing (data integrity) | The core of this phase: provenance columns + honest data_mode/is_synthetic + no-fabrication read path |
| Open redirect via canonical_url | Spoofing | Connectors only set known provider URL patterns; validate scheme (`https://`) before rendering |

## Sources

### Primary (HIGH confidence — files read this session, line-cited in sections above)
- `backend/app/workflows/nodes/ingest.py` — URL/signal_type drop, synthetic fallback injection (lines 15-29, 62-78)
- `backend/app/workflows/runner.py` — Signal persistence, data_mode hardcode, FDA URL reconstruction, on_conflict set_ (130-261)
- `backend/app/connectors/{pubmed,clinical_trials,newsapi,fda,ema}.py` — raw_payload key audits; fda.py:144 API-URL; newsapi.py:77-86 DEGRADED path
- `backend/app/api/v1/endpoints/{signals,health,ingestion,registry,intelligence,observability}.py` — serializer fabrications, ConnectorState-only health, log_id bug, LIVE fabrication, 75.0/3 fabrications, http_code=200 fabrication
- `backend/app/services/{scoring,confluence,ingestion}.py` — formula/version, signal_type counting, HEALTHY-on-empty
- `backend/app/schemas/{__init__,registry,intelligence}.py` — missing fields
- `backend/alembic/versions/004_phase7_truthfulness_and_provenance.py` — full schema (146 lines)
- `backend/app/db/seed.py` — honest seed signals (247-317)
- `backend/app/data/synthetic_signals.json` — metaradar.internal URLs, varied signal_types
- `backend/app/core/{config,logging,domain_config}.py` — env vars, structlog, confluence thresholds
- `frontend/lib/{mappers,api}.ts`, `frontend/types/api.ts` — fabrications + missing fields
- `frontend/components/metaradar.tsx` — canonical reference pages (760-938, 1089-1149, 1663+)
- `frontend/components/{sources/SourcesOperationsWorkspace,confluence/ConfluenceWorkspace,common/EvidenceDrawer,common/DataModeBadge,signals/SignalCard}.tsx` — violations
- `frontend/app/globals.css`, `frontend/app/layout.tsx`, `frontend/components/theme/ThemeProvider.tsx` — token system (7-88), theme architecture
- `frontend/package.json`, `backend/requirements.txt`, `pytest.ini`, `.env.example`, `config/haemophilia.yaml` — stack/env/config
- `tests/test_truthfulness_and_invariants.py` — invariant coverage (183 lines)
- `.planning/phases/08-*/08-CONTEXT.md`, `08-UI-SPEC.md` — locked decisions + UI contract

### Secondary (MEDIUM confidence)
- None required — all claims grounded in repo files read this session.

### Tertiary (LOW confidence)
- Provider credential flows (NewsAPI account flow, xAI console location, openFDA key limits) — stated in CONTEXT.md (user-provided facts), marked `[ASSUMED]` in Assumptions Log where they influence reporting copy, not implementation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every version verified against repo manifests this session
- Architecture: HIGH — provenance chain and fabrication points verified line-by-line in source
- Pitfalls: HIGH — each pitfall grounded in a verified code defect with file+line

**Research date:** 2026-08-20
**Valid until:** 2026-09-19 (stable stack; no fast-moving external deps introduced)