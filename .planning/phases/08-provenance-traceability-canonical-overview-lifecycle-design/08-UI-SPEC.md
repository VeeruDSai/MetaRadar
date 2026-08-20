# UI-SPEC — Phase 08: Provenance, Traceability & Canonical Design System

**Phase:** 08  
**Topic:** Provenance Traceability + Canonical Overview/Lifecycle Design System Hardening  
**Canonical Reference:** `DashboardPage` + `LifecyclePage` in [`metaradar.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/metaradar.tsx)  
**Design token source:** [`frontend/app/globals.css`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/app/globals.css) CSS custom properties  
**Status:** CONTRACT — Binding for all implementation work in Phase 08  

---

## 0. Scope & Non-Goals

**In scope:** All workspaces except `/dashboard` and `/lifecycles` which ARE the canonical reference.  
**Not in scope:** Altering the 4-factor priority formula, ThemeProvider architecture, navigation shell (`Shell`, `topbar`, `sidebar`), or `globals.css` token definitions.

---

## 1. Design Token Reference (Canonical)

All workspaces, drawers, and modals MUST use only the tokens below.  
**BANNED:** `bg-slate-*`, `text-slate-*`, `border-slate-*`, `bg-[#...]`, `text-[#...]`, `border-[#...]`, any `dark:` variant classes that pair with hardcoded light values.

### 1.1 Color Tokens

| CSS Variable | Light | Dark | Semantic Use |
|---|---|---|---|
| `--background` | `#f1f5f9` | `#0b1220` | Page / shell background |
| `--background-secondary` | `#e6eef5` | `#0e1929` | Sidebar background |
| `--surface` | `#fbfdff` | `#111b2b` | Card / panel body |
| `--surface-secondary` | `#eef4f8` | `#152235` | Nested panels, table headers |
| `--surface-elevated` | `#ffffff` | `#1a2a40` | Drawers, modals, popovers |
| `--surface-glass` | `rgb(255 255 255/78%)` | `rgb(17 27 43/82%)` | Glassmorphism overlays |
| `--foreground` | `#16263a` | `#e8eef5` | Primary text |
| `--muted-foreground` | `#607286` | `#8493a5` | Muted / secondary text |
| `--border` | `rgb(15 45 75/10%)` | `rgb(148 163 184/13%)` | All borders |
| `--border-selected` | `rgb(14 165 185/28%)` | `rgb(45 212 191/28%)` | Highlighted / selected borders |
| `--primary` | `#2563c7` | `#4f86e8` | Links, primary accent |
| `--signal` / `--accent` | `#159a9c` | `#52d0c2` | Brand accent / live indicator |
| `--success` | `#168b73` | `#52d0c2` | HEALTHY, confirmed |
| `--warning` | `#bd7b19` | `#e5a45f` | DEGRADED, stale |
| `--danger` | `#c84d59` | `#f2787f` | ERROR, CRITICAL, AUTH_FAILED |
| `--priority-critical` | `#c84d59` | `#f2787f` | CRITICAL badge |
| `--priority-high` | `#c9771d` | `#e5a45f` | HIGH badge |
| `--priority-medium` | `#a87516` | `#ab9be8` | MEDIUM badge |
| `--priority-low` | `#607b91` | `#8ba8ba` | LOW badge |

Usage syntax:
```tsx
style={{ color: 'var(--muted-foreground)' }}
style={{ background: 'var(--surface)' }}
className="text-[var(--foreground)]"
className="bg-[var(--surface-secondary)]"
className="border-[var(--border)]"
```

### 1.2 Typography Tokens

**Font stack:** `Arial, Helvetica, sans-serif` — as defined in `globals.css` body rule.  
**Monospace** (`font-family: monospace`) — reserved **exclusively** for: IDs, fingerprints, source IDs, NCT IDs, PMIDs, log values, technical identifiers. Never for prose, headings, or UI labels.

| Level | CSS Class | Size / Style | Use |
|---|---|---|---|
| Page eyebrow | `.eyebrow` | 10px · UPPERCASE · 0.12em spacing · 700 | Above page title |
| Page title | `.section-title h1` | `clamp(25px,3vw,34px)` · -0.045em | Main workspace heading |
| Card heading | `.card-heading h2` | 16px · -0.025em | Panel section title |
| Panel subtitle | `.muted.panel-subtitle` | 11px · muted | Under card heading |
| Body | default | 14px | General prose |
| Metadata / small | `small` element | 10–11px · muted | Timestamps, counts |
| KPI metric | `.kpi-value strong` | 30px · -0.05em | Dashboard KPI numbers |
| Badge | `.badge` | 9px · 0.08em · UPPERCASE · 700 | Status labels |
| Section label (drawer) | inline style | 10px · UPPERCASE · 0.1em · `var(--primary)` | Drawer section headers |
| Monospace ID | `font-family:monospace` | 10–11px | IDs, fingerprints ONLY |

### 1.3 Spacing & Layout

| Context | Value | Where |
|---|---|---|
| Page content padding | `36px 38px 28px` | `.content` |
| Panel padding | `20px` | `.panel` |
| KPI card padding | `16px 18px` | `.kpi` |
| Grid gap | `13–14px` | `.kpi-grid`, `.bento-grid` |
| Drawer padding | `28px` | `.signal-drawer` |
| Panel border-radius | `var(--radius)` = `0.72rem` | All panels |

### 1.4 Canonical CSS Classes

These are defined in `globals.css` and exported from `metaradar.tsx` components. **Use them — do not recreate them inline.**

| Class / Component | Purpose |
|---|---|
| `<Card>` / `.panel` | Standard surface card |
| `<Badge tone="...">` / `.badge .badge-{critical\|high\|medium\|low\|neutral}` | Status labels |
| `<SectionTitle eyebrow title detail>` | Page header with eyebrow + h1 |
| `.signal-row` + `.severity-dot` + `.signal-copy` + `.signal-score` | Signal list item row |
| `.data-table-container > .data-table` | Sortable data tables |
| `.empty-state` | Zero-data state layout |
| `.error-card` | API / connection error state |
| `.timeline-track > .timeline-node` | Lifecycle event track |
| `.filter-bar button` + `.filter-active` | Filter chip bar |
| `.contradiction-pair > .claim-box` | Red team claim side-by-side |

---

## 2. Provenance Contract

### 2.1 Signal Provenance Pipeline

```
DB Record (Signal model)
  → _serialize_signal()  [backend/app/api/v1/endpoints/signals.py]
  → SignalSchema          [backend/app/schemas/]
  → /api/v1/signals       [API JSON response]
  → mapSignal()           [frontend/lib/mappers.ts or api.ts]
  → Signal type           [frontend/types/api.ts]
  → SignalCard            [frontend/components/signals/SignalCard.tsx]
  → EvidenceDrawer        [frontend/components/common/EvidenceDrawer.tsx]
```

The frontend **MUST NOT** reconstruct provenance from titles, source names, or heuristics. The backend is authoritative.

### 2.2 Required Provenance Fields (Must Flow End-to-End)

| Field | DB Column | API Field | Frontend Type | Display Label |
|---|---|---|---|---|
| Connector Source ID | `signal.source_id` | `source_id` | `Signal.source_id` | Source ID |
| PubMed ID | `signal.pmid` | `pmid` | `Signal.pmid` | PubMed ID |
| ClinicalTrials NCT ID | `signal.nct_id` | `nct_id` | `Signal.nct_id` | NCT ID |
| FDA Record ID | `signal.regulatory_id` | `regulatory_id` | `Signal.regulatory_id` | FDA Record ID |
| Canonical URL | `signal.canonical_url` | `canonical_url` | `Signal.canonical_url` | Canonical Source |
| Content Fingerprint | `signal.fingerprint` | `fingerprint` | `Signal.fingerprint` | Fingerprint |
| Source Published | `signal.published_at` | `published_at` | `Signal.published_at` | Published |
| Connector Retrieved | `signal.retrieved_at` | `retrieved_at` | `Signal.retrieved_at` | Retrieved |
| MetaRadar Ingested | `signal.created_at` | `created_at` | `Signal.created_at` | Ingested |
| Data Mode | `signal.data_mode` | `data_mode` | `Signal.data_mode` | Data Mode |
| Synthetic Flag | `signal.is_synthetic` | `is_synthetic` | `Signal.is_synthetic` | (badge trigger) |
| Signal Type | `signal.signal_type` | `signal_type` | `Signal.signal_type` | Signal Type |

### 2.3 Canonical URL Construction Rules

| Connector | External ID Field | Canonical URL |
|---|---|---|
| PubMed | `pmid` | `https://pubmed.ncbi.nlm.nih.gov/{pmid}/` |
| ClinicalTrials.gov | `nct_id` | `https://clinicaltrials.gov/study/{nct_id}` |
| openFDA | `regulatory_id` | Only when record type has stable public URL; otherwise → `null` |
| EMA RSS | item link from feed | Preserve `<link>` / `href` verbatim |
| NewsAPI | article `url` field | Preserve article URL verbatim; NOT `newsapi.org` |

**URL unavailability rule:** If `canonical_url` is `null` or empty, display:
```
SOURCE URL UNAVAILABLE
Reason: [test fixture / provider did not return a stable public URL]
```
Never fabricate a URL. Never use an API endpoint as the human-readable source URL.

### 2.4 Synthetic / Test Fixture Visibility

Any signal where `is_synthetic === true` OR `data_mode === "test_fixture"`:

- **MUST** show a prominent `TEST FIXTURE` badge in `danger` tone adjacent to the title
- **MUST NOT** show a fabricated `canonical_url` — display `SOURCE URL UNAVAILABLE (test fixture)` instead
- **MUST NOT** be labeled `LIVE INTELLIGENCE` anywhere

---

## 3. EvidenceDrawer Redesign

### 3.1 Banned → Required Color Migration

Every `dark:` Tailwind variant paired with a hardcoded value must be replaced:

| BANNED (current) | REQUIRED (replacement) |
|---|---|
| `bg-white dark:bg-slate-900` | `style={{ background: 'var(--surface-elevated)' }}` |
| `bg-slate-50 dark:bg-slate-950/60` | `style={{ background: 'var(--surface-secondary)' }}` |
| `bg-slate-950/60 backdrop-blur` | `bg-[var(--background)]/60 backdrop-blur-sm` |
| `border-slate-200 dark:border-slate-800` | `style={{ borderColor: 'var(--border)' }}` |
| `text-slate-900 dark:text-slate-100` | `style={{ color: 'var(--foreground)' }}` or `.text-[var(--foreground)]` |
| `text-slate-600 dark:text-slate-400` | `style={{ color: 'var(--muted-foreground)' }}` |
| `text-emerald-600 dark:text-emerald-400` | `style={{ color: 'var(--success)' }}` |
| `text-blue-600 dark:text-blue-400` | `style={{ color: 'var(--primary)' }}` |
| `bg-blue-600 hover:bg-blue-500 text-white` | `style={{ background: 'var(--primary)' }} hover:opacity-90` |
| `bg-slate-100 dark:bg-slate-800` text chip | Use `.badge .badge-neutral` |
| `font-mono` on non-identifier text | Remove — monospace only on IDs |

### 3.2 Content Section Layout (Top to Bottom)

```
┌─ EvidenceDrawer ──────────────────────────────────────────────────────┐
│ HEADER                                                                 │
│  [TEST FIXTURE] [SIGNAL_TYPE]  Priority: [CRITICAL|HIGH|MEDIUM|LOW]  │
│  Signal Title                                              [✕ Close] │
├────────────────────────────────────────────────────────────────────────┤
│ SOURCE PROVENANCE                                                      │
│  Provider:   <source_name or source_id>                               │
│  Source ID:  <source_id>  (monospace)                                 │
│  External ID: <pmid> | <nct_id> | <regulatory_id> | NOT AVAILABLE     │
│  Published:  <published_at>     Ingested:   <created_at>             │
│  Retrieved:  <retrieved_at>     Fingerprint: <fingerprint> (mono)    │
│  ─────────────────────────────────────────────────────────────────   │
│  [ExternalLink] Open Original Source  <url>    (or SOURCE URL UNAVAIL)│
├────────────────────────────────────────────────────────────────────────┤
│ PRIORITY SCORE  (4-Factor Model)                                      │
│  P = 0.25×Novelty + 0.30×Clinical + 0.25×Regulatory + 0.20×Recency  │
│  [Novelty XX] [Clinical XX] [Regulatory XX] [Recency XX]  Total: XX/100│
├────────────────────────────────────────────────────────────────────────┤
│ VERBATIM EVIDENCE                                                      │
│  Exact source-derived text from signal.content                        │
├────────────────────────────────────────────────────────────────────────┤
│ TRACE                                                                  │
│  Connector ──→ Raw record ──→ Normalized ──→ Signal ──→ Score         │
│  (Missing stages show: NOT AVAILABLE — never fabricated)              │
├────────────────────────────────────────────────────────────────────────┤
│ EXTRACTED FACTS  (conditional — only when signal.facts.length > 0)   │
├────────────────────────────────────────────────────────────────────────┤
│ INTERPRETATION / SPECULATION  (conditional)                           │
├────────────────────────────────────────────────────────────────────────┤
│ STAKEHOLDER CALIBRATION FEEDBACK  (conditional — onFeedbackSubmit)    │
└────────────────────────────────────────────────────────────────────────┘
```

### 3.3 "Open Original Source" Implementation

```tsx
// When canonical_url is a real URL:
<div className="source-line">
  <ExternalLink size={14} style={{ color: 'var(--signal)' }} />
  <span>Open Original Source</span>
  <small>{signal.canonical_url}</small>
  <a
    href={signal.canonical_url}
    target="_blank"
    rel="noreferrer noopener"
    style={{ color: 'var(--primary)', fontSize: '11px' }}
  >
    ↗ Open
  </a>
</div>

// When canonical_url is absent, null, or "SOURCE_URL_UNAVAILABLE":
<div className="source-line">
  <AlertTriangle size={14} style={{ color: 'var(--warning)' }} />
  <span>SOURCE URL UNAVAILABLE</span>
  <small>
    {signal.is_synthetic
      ? 'Test fixture — no public source record'
      : 'Provider did not return a stable public URL for this record'}
  </small>
</div>
```

### 3.4 TRACE Section Implementation

```tsx
const traceStages = [
  { label: 'Connector', value: signal.source_id },
  { label: 'Raw Record', value: signal.fingerprint ? `Fingerprint: ${signal.fingerprint}` : null },
  { label: 'Normalized', value: signal.retrieved_at ? `Retrieved: ${signal.retrieved_at}` : null },
  { label: 'Signal', value: signal.signal_id || signal.id },
  { label: 'Score', value: signal.score_breakdown ? `Total: ${signal.score_breakdown.total}/100` : null },
]

// Render each stage — show NOT AVAILABLE when value is null, never fabricate
traceStages.map(stage => (
  <div key={stage.label} className="source-line">
    <span style={{ color: 'var(--muted-foreground)', fontFamily: 'monospace', fontSize: '10px' }}>
      {stage.label}
    </span>
    <span>
      {stage.value ?? (
        <em style={{ color: 'var(--muted-foreground)', fontStyle: 'italic' }}>NOT AVAILABLE</em>
      )}
    </span>
  </div>
))
```

---

## 4. SignalCard Migration

### 4.1 CSS Class Mapping

```
Outer container:
  OLD: rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 ...
  NEW: .panel  (with cursor-pointer and hover:border-[var(--border-selected)] added)

Priority badge:
  OLD: px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider border {badgeClass}
  NEW: .badge .badge-{critical|high|medium|low}

Score:
  OLD: text-xs font-mono font-semibold text-emerald-600 dark:text-emerald-400
  NEW: .signal-score > strong  (or inline style color: var(--success))

Title (h3):
  OLD: text-sm font-semibold text-slate-900 dark:text-slate-200 group-hover:text-blue-600 ...
  NEW: font-size 14px, font-weight 600, letter-spacing -0.02em, color var(--foreground);
       hover: color var(--primary) (via style or CSS variable class)

Summary:
  OLD: text-xs text-slate-600 dark:text-slate-400
  NEW: .muted  (+ font-size 12px, line-height 1.55)

Source chips:
  OLD: text-[11px] font-mono bg-slate-100 dark:bg-slate-800/80 px-2 py-0.5 rounded ...
  NEW: .badge .badge-neutral (monospace only on actual source IDs)

"View Evidence" link:
  OLD: text-xs text-blue-600 dark:text-blue-400 group-hover:underline
  NEW: .text-link (font-size 11px, color var(--signal), display flex, gap 3px)

Footer border:
  OLD: border-t border-slate-100 dark:border-slate-800/60
  NEW: border-top: 1px solid var(--border)
```

### 4.2 Provenance Metadata Row

Add below the summary text, above the footer:

```tsx
<div style={{ fontSize: '10px', color: 'var(--muted-foreground)', display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '6px' }}>
  {signal.pmid && (
    <span>PMID: <code style={{ fontFamily: 'monospace' }}>{signal.pmid}</code></span>
  )}
  {signal.nct_id && (
    <span>NCT: <code style={{ fontFamily: 'monospace' }}>{signal.nct_id}</code></span>
  )}
  {signal.published_at && (
    <span>Published: {new Date(signal.published_at).toLocaleDateString()}</span>
  )}
  {signal.source_id && (
    <span style={{ fontFamily: 'monospace' }}>{signal.source_id}</span>
  )}
</div>
```

---

## 5. Workspace Audit — Component by Component

### `/signals` — [SignalList.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/signals/SignalList.tsx) + [SignalCard.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/signals/SignalCard.tsx)

| Issue | Fix |
|---|---|
| Hardcoded `bg-slate-*` in SignalCard | Replace per §4.1 |
| No page header using `<SectionTitle>` | Add `<SectionTitle eyebrow="Ingested Signal Intelligence" title="Live Signals" detail={...} />` |
| No provenance row | Add per §4.2 |
| Filter bar may use non-canonical classes | Use `.filter-bar button` + `.filter-active` |

---

### `/confluence` — [ConfluenceWorkspace.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/confluence/ConfluenceWorkspace.tsx)

| Issue | Fix |
|---|---|
| Hardcoded color classes | Replace with CSS vars |
| `≥3 distinct source types` wording may not match backend | Audit backend confluence rule threshold; fix wording to match exactly |
| Inspector missing per-evidence provenance | Each contributing evidence item must show: signal title, provider, external ID, pub date, canonical URL, evidence excerpt |

---

### `/red-team` — [ContradictionWorkspace.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/contradictions/ContradictionWorkspace.tsx)

| Issue | Fix |
|---|---|
| Inline `text-[var(--danger)]` wrapping hardcoded | Use `.badge .badge-critical/.badge-high/.badge-medium` |
| Filter buttons using inline conditional classes | Use `.filter-bar button` + `.filter-active` |
| `.panel .redteam-tint`, `.contradiction-pair`, `.claim-box` | Verify these canonical classes are applied |

---

### `/missing-signals` — [MissingSignalsWorkspace.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/missing-signals/MissingSignalsWorkspace.tsx)

Apply: `<SectionTitle>`, `.panel`, `.missingsignal-tint`, `.badge`, `.empty-state`

---

### `/developments` — [DevelopmentsWorkspace.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/developments/DevelopmentsWorkspace.tsx)

Apply: `<SectionTitle>`, `.panel`, `.timeline-track`, `.timeline-node`, `.badge`

---

### `/intelligence` — [AthenaWorkspace.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/intelligence/AthenaWorkspace.tsx)

Verify: `.athena-card`, `.athena-orbit`, `.prompt-list`, `.ask-row`, `.answer-card`, `.confidence` classes are in use. Replace any hardcoded color values.

---

### `/functions` — [FunctionsWorkspace.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/functions/FunctionsWorkspace.tsx)

Apply: `<SectionTitle>`, `.panel`, `.badge`, `.generic-grid`

---

### `/calibrate` — [CalibrationWorkspace.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/calibration/CalibrationWorkspace.tsx)

Verify: `.calibration-widget-card`, `.role-pill`, `.role-pill-active`, `.star-btn`, `.star-active`, `.submit-feedback-btn`, `.recalibrate-btn`, `.before-after-panel`, `.comparison-card` are applied.

---

### `/sources` — [SourcesOperationsWorkspace.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/sources/SourcesOperationsWorkspace.tsx)

| Issue | Fix |
|---|---|
| `h1` with `text-xl font-bold text-slate-900 dark:text-slate-100` | Replace with `<SectionTitle eyebrow="Connector Registry" title="Sources & Connectors" detail="..." />` |
| `getStatusBadge()` returns hardcoded Tailwind `bg-emerald-*`, `bg-amber-*`, `bg-red-*` | Replace with CSS var color-mix, matching `.badge`-style approach |
| No `CONFIGURATION_ERROR` state | When credential env var missing, show `CONFIGURATION_ERROR: <VAR> missing` badge (danger tone) + explanation |
| Missing telemetry fields per connector | Show: HTTP status, records fetched / accepted / rejected, last successful sync, last attempted, latency, error |

#### Connector Status Badge Mapping

| Status | CSS Variable Color | Badge Tone |
|---|---|---|
| HEALTHY | `var(--success)` | success |
| DEGRADED | `var(--warning)` | warning |
| STALE | `var(--warning)` | warning |
| RATE_LIMITED | `var(--warning)` | warning |
| AUTH_FAILED | `var(--danger)` | danger |
| ERROR | `var(--danger)` | danger |
| CONFIGURATION_ERROR | `var(--danger)` | danger |
| NEVER_CONNECTED | `var(--muted-foreground)` | neutral |
| DISABLED | `var(--muted-foreground)` | neutral |

---

### `/observability` — [ActivityStreamWorkspace.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/observability/ActivityStreamWorkspace.tsx)

Apply: `<SectionTitle>`, `.panel`, `.data-table-container > .data-table`, `.badge`

---

### `/settings` — [SettingsWorkspace.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/settings/SettingsWorkspace.tsx)

Apply: `<SectionTitle>`, `.panel`, `.badge`  
Add: Credential status display — show `CONFIGURATION_ERROR: <VAR> missing` with official URL to obtain the key.

---

## 6. Theme Persistence Requirements

### 6.1 Architecture (Current — Keep As-Is)

- `ThemeProvider.tsx` is the single source of truth
- Persists to `localStorage` key
- Applies `.dark` class to `<html>` element
- All components read theme via CSS custom properties on `:root` / `.dark`

### 6.2 Theme Must Survive

| Event | Expected behavior |
|---|---|
| Client-side navigation (`<Link>`) | Theme unchanged |
| Browser refresh | Theme restored from `localStorage` |
| Open/close drawer or modal | Theme unchanged |
| Direct URL navigation | Theme restored |
| Opening new tab with same URL | Theme restored |

### 6.3 Banned Patterns

```tsx
// BANNED — these break light mode
className="bg-slate-900 dark:bg-slate-950"
className="text-slate-400 dark:text-slate-300"
style={{ background: '#0b1220' }}
style={{ color: '#e8eef5' }}
```

### 6.4 Required Patterns

```tsx
// REQUIRED — these work in both themes
style={{ background: 'var(--surface)' }}
style={{ color: 'var(--muted-foreground)' }}
className="text-[var(--foreground)]"
className="bg-[var(--surface-secondary)]"
className="border-[var(--border)]"
// Or via globals.css classes:
className="muted"     // var(--muted-foreground)
className="panel"     // var(--surface) background + border
```

---

## 7. ConfluenceWorkspace Inspector Spec

When a user drills into a specific confluence alert, the inspector MUST show:

```
CONFLUENCE DETAILS
  Score: XX        Label: <label>       Sources: <N> distinct types
  Drivers: [driver1] [driver2] [driver3]

CONTRIBUTING EVIDENCE  (one row per contributing signal)
  ┌──────────────────────────────────────────────────────────┐
  │ Signal Title                              [SOURCE BADGE] │
  │ Provider: <source_name>  ·  External ID: <pmid|nct_id>  │
  │ Published: <date>  ·  [Open Original Source ↗]          │
  │ Excerpt: First ~200 chars of evidence text...            │
  └──────────────────────────────────────────────────────────┘
  (repeat per contributing signal)
```

**Semantics fix:** The wording "≥3 distinct source types required" MUST match the backend enforcement threshold. Audit `backend/app/services/confluence.py` (or equivalent) to read the actual threshold, then update the UI string to match exactly. Do not leave them inconsistent.

---

## 8. Backend Changes Required

### 8.1 `signals.py` — `_serialize_signal()`

- `created_at` must always be returned (it is already in the model)
- `source_name` should be derivable — either join with source registry or derive from `source_id` mapping

### 8.2 Sources / Connectors Endpoint

The `/health/connectors` or `/sources` API response must include per connector:

| Field | Type | Description |
|---|---|---|
| `status` | string | HEALTHY / DEGRADED / AUTH_FAILED / NEVER_CONNECTED / CONFIGURATION_ERROR |
| `configuration_error_message` | string? | `CONFIGURATION_ERROR: NEWSAPI_KEY missing` when env var absent |
| `http_status` | int? | Last HTTP response code |
| `records_fetched` | int | Records returned by source in last attempt |
| `records_accepted` | int | Records inserted/updated in DB |
| `records_rejected` | int | Records filtered or rejected |
| `last_success` | datetime? | Last successful ingestion timestamp |
| `last_attempted` | datetime? | Last attempted ingestion timestamp |
| `latency_ms` | float? | Last request latency |
| `last_error` | string? | Last error message (no secrets) |

**Key rule:** `HTTP 200 with 0 records_fetched` ≠ HEALTHY. Consider it DEGRADED. A connector is HEALTHY only when it successfully returns AND accepts at least one record in its last ingestion attempt (or within a configurable freshness window).

### 8.3 Connector Provenance Construction

| Connector | Action |
|---|---|
| PubMed | If `canonical_url` not set but `pmid` exists: construct `https://pubmed.ncbi.nlm.nih.gov/{pmid}/` in the connector before storing |
| ClinicalTrials.gov | If `canonical_url` not set but `nct_id` exists: construct `https://clinicaltrials.gov/study/{nct_id}` |
| NewsAPI | Store article `url` field as `canonical_url`; store `source.name` (not `newsapi.org`) as `source_name` |
| EMA RSS | Store feed item `<link>` or `href` as `canonical_url` |
| openFDA | Only set `canonical_url` when record type has a verified stable public URL; otherwise leave `null` |

---

## 9. Implementation Checklist

### Frontend

- [ ] [`EvidenceDrawer.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/common/EvidenceDrawer.tsx)
  - [ ] Replace all hardcoded colors with CSS vars (§3.1)
  - [ ] Add SOURCE PROVENANCE section (§3.2)
  - [ ] Add "Open Original Source" / "SOURCE URL UNAVAILABLE" (§3.3)
  - [ ] Add TRACE section (§3.4)
- [ ] [`SignalCard.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/signals/SignalCard.tsx)
  - [ ] Migrate to `.panel`, `.badge`, CSS vars (§4.1)
  - [ ] Add provenance metadata row (§4.2)
- [ ] [`DataModeBadge.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/common/DataModeBadge.tsx)
  - [ ] Use `.badge` class
  - [ ] `TEST FIXTURE` → danger tone
  - [ ] Never label synthetic as `LIVE`
- [ ] [`SignalList.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/signals/SignalList.tsx)
  - [ ] Add `<SectionTitle>`
  - [ ] Use `.filter-bar` canonical classes
- [ ] [`SourcesOperationsWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/sources/SourcesOperationsWorkspace.tsx)
  - [ ] Replace inline `h1` with `<SectionTitle>`
  - [ ] Migrate `getStatusBadge()` to CSS vars
  - [ ] Add CONFIGURATION_ERROR state display
  - [ ] Show full telemetry per connector
- [ ] [`ContradictionWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/contradictions/ContradictionWorkspace.tsx) — §5 audit
- [ ] [`MissingSignalsWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/missing-signals/MissingSignalsWorkspace.tsx) — §5 audit
- [ ] [`DevelopmentsWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/developments/DevelopmentsWorkspace.tsx) — §5 audit
- [ ] [`AthenaWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/intelligence/AthenaWorkspace.tsx) — §5 audit
- [ ] [`FunctionsWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/functions/FunctionsWorkspace.tsx) — §5 audit
- [ ] [`CalibrationWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/calibration/CalibrationWorkspace.tsx) — §5 audit
- [ ] [`ActivityStreamWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/observability/ActivityStreamWorkspace.tsx) — §5 audit
- [ ] [`SettingsWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/settings/SettingsWorkspace.tsx) — §5 audit
- [ ] [`ConfluenceWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/confluence/ConfluenceWorkspace.tsx)
  - [ ] Inspector with per-evidence provenance (§7)
  - [ ] Fix `≥N distinct sources` wording to match backend threshold

### Backend

- [ ] `signals.py` `_serialize_signal()` — ensure `created_at` always returned
- [ ] Sources/health endpoint — add `configuration_error_message`, `records_fetched`, `records_accepted`, `records_rejected`, `http_status` per connector
- [ ] PubMed connector — construct `canonical_url` from `pmid` before storing
- [ ] ClinicalTrials connector — construct `canonical_url` from `nct_id` before storing
- [ ] NewsAPI connector — store article `url` as `canonical_url`; store `source.name` as `source_name`
- [ ] EMA connector — store feed item link as `canonical_url`
- [ ] Confluence service — verify `≥N distinct source types` threshold; align UI wording to match

---

## 10. Verification Plan

### Automated Tests

```bash
# Frontend
cd frontend && npm run lint
cd frontend && npm run build

# Backend
cd backend && pytest tests/ -v
```

### Manual Walkthrough Matrix

| Step | Action | Pass Condition |
|---|---|---|
| 1 | Start app in dark mode | All workspaces render with dark theme colors |
| 2 | Switch to light mode | All workspaces immediately use light theme colors; no dark artifacts |
| 3 | Navigate to 5 different workspaces | Theme persists across all navigations |
| 4 | Refresh browser | Theme restored from storage; correct workspace loads |
| 5 | Open a signal → EvidenceDrawer | SOURCE PROVENANCE section is populated with real data |
| 6 | LIVE signal with PMID | `canonical_url` clickable ↗ → opens correct PubMed record |
| 7 | LIVE signal with NCT ID | `canonical_url` clickable ↗ → opens correct ClinicalTrials.gov study |
| 8 | TEST FIXTURE signal | Shows TEST FIXTURE badge; shows SOURCE URL UNAVAILABLE |
| 9 | `/confluence` → open alert | Contributing evidence shows provider + external ID + canonical URL |
| 10 | `/sources` → check connector list | If NEWSAPI_KEY missing → `CONFIGURATION_ERROR: NEWSAPI_KEY missing` badge |
| 11 | `/sources` → trigger sync | Telemetry updates; records_fetched/accepted/rejected visible |
| 12 | `/signals` → filter by severity | Filter bar uses `.filter-active` visual; results update |
| 13 | `/red-team` → filter by CRITICAL | Contradiction items filter; badges use canonical `.badge-critical` |
| 14 | Direct URL to `/settings` | Theme correct; settings workspace renders cleanly |
| 15 | Repeat steps 1-14 in light mode | All pass |
