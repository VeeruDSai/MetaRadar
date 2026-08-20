# Phase 08: Context & Decisions

> **Phase:** 08
> **Topic:** Provenance Traceability + Canonical Overview/Lifecycle Design System Hardening
> **Grounded in:** Direct user audit directive — the previous remediation pass (Phase 07) fixed priority scoring, connector health telemetry, confluence endpoint failures, basic theme persistence, synthetic labeling, some source URLs, and tests/builds, but fundamental traceability remains broken.

---

## User Constraints & Directives

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

---

## Key Architecture & Implementation Decisions

- **D-08-01 — Provenance Object Is Authoritative in Backend** A single normalized provenance structure flows from DB → serializer → API → frontend mapper → UI. Frontend never derives provenance from titles or heuristics.
- **D-08-02 — Truthful URL States** `canonical_url` is either a real, provider-canonical URL or an explicit `SOURCE URL UNAVAILABLE` state with a reason — never fabricated.
- **D-08-03 — Source-Specific Identifier Preservation** PMID / NCT ID / FDA ID / EMA item URL / NewsAPI article URL are preserved end-to-end independent of generated signal IDs.
- **D-08-04 — Evidence Is Verbatim** The evidence excerpt is the exact source-derived text; intermediate trace stages display `NOT AVAILABLE` when absent.
- **D-08-05 — Synthetic Visibility** Synthetic/test-fixture records are unmistakably badged `TEST FIXTURE` / `SYNTHETIC`; no manufactured public URLs for fixtures.
- **D-08-06 — Honest Connector Health** Source status reflects actual ingestion telemetry (HTTP + records fetched/accepted + last syncs + latency + errors + auth state), not HTTP 200 alone.
- **D-08-07 — Explicit Credential Reporting** Missing credentials reported as `CONFIGURATION_ERROR: <VAR> missing` with exact env var, required/optional, official location, and steps; no fabricated values.
- **D-08-08 — Canonical Design System** Design tokens extracted from `/dashboard` and `/lifecycles` become the single source of truth for all workspaces and drawers.
- **D-08-09 — Single Theme Store** Theme persisted once at the root provider and read globally; no per-page theme state; both light and dark are real semantic token themes.
- **D-08-10 — Single Priority Calculation** The 4-factor formula is calculated once (backend) and flows end-to-end; no silent zero fallback; reasons exposed when incalculable.
- **D-08-11 — Truthful Confluence Semantics** Confluence rule (≥3 distinct source categories) and UI wording agree; contributing evidence individually traceable.
- **D-08-12 — Debuggable Ingestion** Per-attempt ingestion logs capture connector/request/status/latency/records/errors without secrets.

---