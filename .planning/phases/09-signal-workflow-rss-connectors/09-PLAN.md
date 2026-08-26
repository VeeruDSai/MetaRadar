# Phase 09 — PLAN.md

## Phase 09: Real Signal Workflow, NewsAPI Provenance Fix & Pharma RSS Discovery Connectors

**Context:** [09-CONTEXT.md](./09-CONTEXT.md)
**Branch:** `feature/phase-09-signal-workflow-rss-connectors`
**Plans:** 3 execution waves

---

## Wave Summary

| Plan | Title | Focus |
| :--- | :--- | :--- |
| [09-01-PLAN.md](./09-01-PLAN.md) | Bug Fix: NewsAPI URL + Review Workflow API Integration | Backend fix + frontend API wiring |
| [09-02-PLAN.md](./09-02-PLAN.md) | Demo Operator, Audit History UI, Routing Queue Display | Frontend workflow UX |
| [09-03-PLAN.md](./09-03-PLAN.md) | Pharma RSS Connectors + Routing Logic Improvement | New connectors + escalation logic |

---

## Plan 09-01: Bug Fix — NewsAPI URL Provenance & Review Workflow API Integration

### Scope

**Problem 1: NewsAPI source URL**
- `SignalDetailWorkspace.tsx:103` hardcodes `https://newsapi.org` as fallback → users sent to API registration page instead of the actual article
- `resolve_canonical_provenance()` has no `newsapi` handler; existing `article.url` is valid but bypassed
- `LANDING_PAGE_URLS` does not block `newsapi.org/register` or `newsapi.org`

**Problem 2: Review buttons don't persist state**
- `handleUpdateReview()` mutates only React local state → resets on page reload
- `POST /signals/{id}/review` endpoint exists but is never called
- `GET /signals/{id}/audit-history` is never fetched in the UI

---

### Tasks

#### Task 09-01-A: Fix NewsAPI Provenance URL Resolver

**File:** `backend/app/services/provenance_urls.py`

1. Add `newsapi.org`, `newsapi.org/register` to `LANDING_PAGE_URLS` block list.
2. Add `newsapi` handler to `resolve_canonical_provenance()`:
   ```python
   elif source == "newsapi":
       # The connector stores article.url as existing_url — pass it through directly.
       # Do not attempt to construct a URL from external_id (which may be the article URL itself).
       if url and _looks_like_http_url(url) and not is_generic_landing_page(url):
           return url, "available"
       # Try external_id directly if it is a full URL
       if ext and ext.startswith("http"):
           return ext, "available"
       return None, "missing_url"
   ```
3. Add `NEWSAPI_LANDING_PAGES` constant set for clarity.

**File:** `backend/app/connectors/newsapi.py`

4. Ensure `raw_payload["url"]` is set to `url` unconditionally in `_parse_article()` (currently `url or None` which is correct — verify no truncation of URL).
5. Ensure `external_id` is the article URL when available (currently `url or sha256_hash` — correct; verify this path is exercised).

**Verification:** `pytest tests/test_provenance.py -v` must pass. Add test case: newsapi signal with valid article URL → `resolve_canonical_provenance()` returns article URL with status `"available"`.

---

#### Task 09-01-B: Add `submitSignalReview` API Function

**File:** `frontend/lib/api.ts`

Add strongly typed function:
```typescript
export interface SignalReviewPayload {
  status: 'UNREVIEWED' | 'IN_REVIEW' | 'REVIEWED' | 'ACTION_REQUIRED' | 'ACTIONED' | 'DISMISSED'
  reviewer?: string
  decision?: string
  notes?: string
  resulting_action?: string
}

export async function submitSignalReview(
  signalId: string,
  payload: SignalReviewPayload,
  signal?: AbortSignal
): Promise<Signal> {
  const res = await apiFetch(`/signals/${signalId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new ApiError(res.status, (err as any).detail || 'Review submission failed')
  }
  return res.json()
}

export async function fetchSignalAuditHistory(
  signalId: string,
  signal?: AbortSignal
): Promise<AuditLogItem[]> {
  const res = await apiFetch(`/signals/${signalId}/audit-history`, { signal })
  if (!res.ok) throw new ApiError(res.status, 'Failed to fetch audit history')
  return res.json()
}
```

Also add `AuditLogItem` type to `frontend/types/api.ts` (export from OpenAPI contract sync).

---

#### Task 09-01-C: Wire Review Buttons to API in SignalDetailWorkspace

**File:** `frontend/components/signals/SignalDetailWorkspace.tsx`

1. Remove hardcoded `https://newsapi.org` from `evidenceUrl` chain (line 103). The chain should end with `null` — the backend now provides the correct URL via `signal.canonical_url`.

2. Replace local-state-only `handleUpdateReview` with API-backed handler:
```typescript
const [isReviewLoading, setIsReviewLoading] = useState(false)
const [reviewError, setReviewError] = useState<string | null>(null)
const [currentSignal, setCurrentSignal] = useState(signal)

const handleUpdateReview = async (newStatus: string, decision?: string, notes?: string, resultingAction?: string) => {
  setIsReviewLoading(true)
  setReviewError(null)
  try {
    const updated = await submitSignalReview(currentSignal.signal_id, {
      status: newStatus as SignalReviewPayload['status'],
      reviewer: demoOperator,  // from session storage (Phase 09-02)
      decision,
      notes,
      resulting_action: resultingAction,
    })
    setCurrentSignal(updated)
    setReviewNotice(`Status updated: ${newStatus}`)
    setTimeout(() => setReviewNotice(null), 4000)
  } catch (err: any) {
    setReviewError(err?.message || 'Review submission failed')
  } finally {
    setIsReviewLoading(false)
  }
}
```

3. Update review status display to read from `currentSignal.review_status` (not a local state string).

4. Update the lifecycle stepper to reflect backend `currentSignal.review_status`.

**Verification:** `pnpm exec tsc --noEmit`, `pnpm lint` must pass.

---

#### Task 09-01-D: Add Test for NewsAPI Provenance + Review Workflow Persistence

**File:** `tests/test_provenance.py`

Add:
- `test_newsapi_article_url_preserved()` — `resolve_canonical_provenance(source_id="newsapi", existing_url="https://www.fiercepharma.com/article/xyz")` returns that URL with status `available`
- `test_newsapi_landing_page_blocked()` — `resolve_canonical_provenance(source_id="newsapi", existing_url="https://newsapi.org/register")` returns `None` or constructs from external_id

**File:** `tests/test_signal_routing_workflow.py` (NEW)

Create comprehensive workflow state machine test:
```python
# test_signal_routing_workflow.py
"""Tests the end-to-end signal review workflow state machine.
UNREVIEWED → IN_REVIEW → REVIEWED → ACTIONED
Verifies that each transition:
1. Persists to the database
2. Writes an immutable AuditLog record
3. Is reflected in subsequent GET requests
"""
```

Cover:
- `UNREVIEWED` → `IN_REVIEW` (Acknowledge) + audit entry created
- `IN_REVIEW` → `REVIEWED` (Approve/Reject) + decision persisted + reviewer recorded
- `REVIEWED` → `ACTIONED` + resulting_action recorded
- `REVIEWED` → `DISMISSED` + audit entry
- Invalid status transition → 400 HTTP error
- Audit history endpoint returns all transitions in chronological order

---

### 09-01 Verification Gates

```bash
pytest tests/test_provenance.py -v                    # Must pass (includes new newsapi tests)
pytest tests/test_signal_routing_workflow.py -v       # Must pass (all state machine transitions)
pytest tests/ -x -q -m "not live"                    # 115+ passed, 0 failed
pnpm --prefix frontend exec tsc --noEmit             # 0 type errors
node scripts/check-banned-classes.mjs                 # 0 violations
```

---

## Plan 09-02: Demo Operator, Audit History UI & Routing Queue Display

### Scope

Build the frontend UX that makes the review workflow demonstrable: a Demo Role selector, visible audit trail, and a queue-aware routing section that shows the signal's current organizational destination and workflow status.

---

### Tasks

#### Task 09-02-A: Demo Operator Selector Component

**File (NEW):** `frontend/components/common/DemoOperatorSelector.tsx`

```typescript
'use client'
// Demo Role selector — NOT authentication. Clearly labeled "Demo Mode" selector
// that sets the active demo reviewer persona for workflow demonstrations.
// Stored in sessionStorage under key 'metaradar_demo_operator'.

const DEMO_OPERATORS = [
  { value: 'Demo Medical Affairs Reviewer', label: 'Medical Affairs' },
  { value: 'Demo Regulatory Affairs Reviewer', label: 'Regulatory Affairs' },
  { value: 'Demo Safety Reviewer', label: 'Safety / Pharmacovigilance' },
  { value: 'Demo Market Access Reviewer', label: 'Market Access' },
  { value: 'Demo Communications Reviewer', label: 'Medical Communications' },
  { value: 'Demo Leadership Reviewer', label: 'Executive Leadership' },
]
```

Display: Small persistent badge in the top navigation bar showing `Demo Role: Regulatory Affairs` with a popover selector. The badge is visually distinct (amber/warning color scheme) to make it clear this is a demo construct. Include a tooltip: "Select your demo reviewer role. This is for demonstration purposes only."

**File:** `frontend/components/metaradar.tsx` — add `DemoOperatorSelector` to top navigation bar.

**File:** `frontend/lib/hooks.ts` — add `useDemoOperator()` hook that reads/writes `sessionStorage`.

---

#### Task 09-02-B: Audit History Panel in Signal Detail

**File:** `frontend/components/signals/SignalDetailWorkspace.tsx`

Add an "AUDIT TRAIL" section below the 3-pillar cards:
```
AUDIT TRAIL                          [Refresh]
────────────────────────────────────────────────
● SIGNAL_REVIEWED  →  IN_REVIEW
  Reviewer: Demo Regulatory Affairs Reviewer
  2026-08-26  18:34:21 UTC
  Notes: Opening for regulatory review

● SIGNAL_REVIEWED  →  REVIEWED  
  Reviewer: Demo Regulatory Affairs Reviewer
  Decision: APPROVED
  2026-08-26  18:41:05 UTC

DETECTED → CLASSIFIED → PRIORITIZED → ROUTED → [IN REVIEW] → ACTION
```

Fetch via `GET /signals/{id}/audit-history` on component mount. Re-fetch after each review action.

---

#### Task 09-02-C: Routing Queue Display

**File:** `frontend/components/signals/SignalDetailWorkspace.tsx`

Replace the current routing display with a structured "ROUTING & REVIEW QUEUE" card:

```
ROUTING & REVIEW QUEUE
─────────────────────────────────────────────
DESTINATION    Medical Affairs
QUEUE STATUS   ● Awaiting Review
ROUTED ON      26 Aug 2026

REVIEW PROGRESS
Detection ✓  Classification ✓  Priority ✓  Routing ✓  
Medical Affairs Review [●  Awaiting]  Action [○  Pending]

CURRENT REVIEWER
No reviewer assigned yet

[Acknowledge]   [Start Review]   [Approve]   [Reject]   [Request Evidence]
```

Button behavior:
- **Acknowledge** → `POST /review` with `status: IN_REVIEW`, `reviewer: demoOperator`
- **Approve** → `POST /review` with `status: REVIEWED`, `decision: APPROVED`, `reviewer: demoOperator`
- **Reject** → `POST /review` with `status: REVIEWED`, `decision: REJECTED` + notes modal
- **Request Evidence** → `POST /review` with `status: ACTION_REQUIRED`, `resulting_action: "Request additional evidence"`, `reviewer: demoOperator`
- **Action** → `POST /review` with `status: ACTIONED`, `resulting_action: user-provided text`
- **Dismiss** → `POST /review` with `status: DISMISSED`, `reviewer: demoOperator`

Add a simple inline notes input for Reject and Request Evidence buttons (not a modal — inline collapsible textarea to reduce friction).

---

#### Task 09-02-D: Signal Card Queue Badge

**File:** `frontend/components/signals/SignalCard.tsx`

Add a review queue status badge to signal cards:
- `UNREVIEWED` → amber dot "Awaiting Review"
- `IN_REVIEW` → blue dot "In Review"
- `REVIEWED` → green check "Reviewed"
- `ACTIONED` → green check "Actioned"
- `DISMISSED` → grey slash "Dismissed"

---

### 09-02 Verification Gates

```bash
pnpm --prefix frontend exec tsc --noEmit             # 0 type errors
node scripts/check-banned-classes.mjs                 # 0 violations
pnpm --prefix frontend run lint                      # 0 warnings
pnpm --prefix frontend run build                     # Clean Turbopack build
```

---

## Plan 09-03: Pharma RSS Connectors + Routing Logic Improvement

### Scope

Add Fierce Pharma and ET Pharma as Tier 3 Discovery RSS connectors (following the existing `EMARSSConnector` pattern). Register BioPharma Dive with honest `configured_no_feed` status. Improve the leadership escalation logic to use compound domain+score rules instead of the blunt `score >= 80` threshold.

---

### Tasks

#### Task 09-03-A: Fierce Pharma RSS Connector

**File (NEW):** `backend/app/connectors/fierce_pharma.py`

```python
class FiercePharmaRSSConnector(SourceConnector):
    """Fierce Pharma RSS feed connector (REQ-P9-07).
    
    Official RSS feed: https://www.fiercepharma.com/rss/xml
    Tier 3 Discovery source. Parses <item> elements, filters by haemophilia
    domain keywords from connector profile, persists to bronze with article
    <link> as canonical URL. Pattern mirrors EMARSSConnector.
    """
    source_id = "fierce_pharma"
    source_type = "news"
    freshness_class = "delayed"
    DEFAULT_RSS_URL = "https://www.fiercepharma.com/rss/xml"
```

Implementation mirrors `EMARSSConnector`:
- `run_profile()`: fetch RSS, parse XML, filter by profile keywords, persist to bronze
- `_parse_item()`: extract title, description, `<link>` as URL, `<pubDate>`, publisher="Fierce Pharma"
- `_detect_entities()`: reuse pattern from NewsAPIConnector
- Fingerprint: SHA256 of `title + pubDate`
- `raw_payload["url"]` = RSS `<link>` value (the actual article URL)

**File:** `backend/app/connectors/__init__.py`

Register `FiercePharmaRSSConnector` in the connector registry.

---

#### Task 09-03-B: ET Pharma RSS Connector

**File (NEW):** `backend/app/connectors/et_pharma.py`

```python
class ETPharmaRSSConnector(SourceConnector):
    """ET Pharma (Economic Times Pharma) RSS feed connector (REQ-P9-08).
    
    Primary RSS: https://pharma.economictimes.indiatimes.com/rss/topstories
    Drug Approvals RSS: https://pharma.economictimes.indiatimes.com/rss/drug_approvals
    Tier 3 Discovery source. Each profile maps to a specific feed URL.
    Pattern mirrors EMARSSConnector.
    """
    source_id = "et_pharma"
    source_type = "news"
    freshness_class = "delayed"
    DEFAULT_RSS_URL = "https://pharma.economictimes.indiatimes.com/rss/topstories"
```

Implementation mirrors `FiercePharmaRSSConnector` but supports per-profile RSS URL overrides from `config/haemophilia.yaml`.

---

#### Task 09-03-C: BioPharma Dive Honest Registration

**File:** `config/haemophilia.yaml`

Add under `connectors:`:
```yaml
  biopharmadive:
    freshness_class: manual
    tier: 3
    status: configured_no_feed
    notes: >
      BioPharma Dive covers FDA approvals, clinical readouts, drug pricing, and M&A.
      No public RSS or API feed available. Integration pending compliant mechanism.
      Source URL: https://www.biopharmadive.com/
    profiles: []
```

This makes BioPharma Dive visible in the Sources Registry as `CONFIGURATION_PENDING` rather than absent.

**File:** `backend/app/services/ingestion.py` — ensure connectors with `profiles: []` do not attempt to run and set status to `CONFIGURATION_PENDING` rather than erroring.

---

#### Task 09-03-D: Update `haemophilia.yaml` Source Tiers

**File:** `config/haemophilia.yaml`

```yaml
source_tiers:
  tier_1_authoritative:
    - "clinical_trials"
    - "pubmed"
    - "fda"
    - "ema"
    - "who_ictrp"
  tier_2_high_value:
    - "ash"
    - "isth"
    - "eha"
    - "company_ir"
    - "company_press"
  tier_3_discovery:
    - "newsapi"
    - "fierce_pharma"
    - "et_pharma"
    - "biopharmadive"
    - "reuters"
    - "bloomberg"
  tier_4_lead_only:
    - "blogs"
    - "social"
    - "unverified_aggregators"
```

Add connector profiles for `fierce_pharma` and `et_pharma`:
```yaml
  fierce_pharma:
    freshness_class: delayed
    tier: 3
    rss_url: "https://www.fiercepharma.com/rss/xml"
    backfill_days: 30
    rolling_window_days: 7
    profiles:
      - id: haemophilia_pharma_news
        rss_url: "https://www.fiercepharma.com/rss/xml"
        keywords: ["haemophilia", "hemophilia", "emicizumab", "fitusiran", "concizumab",
                   "mim8", "gene therapy", "Novo Nordisk", "FDA approval", "EMA", "Alhemo",
                   "Hemlibra", "Hemgenix", "Hympavzi", "Qfitlia"]

  et_pharma:
    freshness_class: delayed
    tier: 3
    backfill_days: 30
    rolling_window_days: 7
    profiles:
      - id: haemophilia_pharma_news
        rss_url: "https://pharma.economictimes.indiatimes.com/rss/topstories"
        keywords: ["haemophilia", "hemophilia", "bleeding disorder", "gene therapy",
                   "Novo Nordisk", "Roche", "CSL Behring", "Sanofi", "emicizumab", "fitusiran"]
      - id: drug_approvals
        rss_url: "https://pharma.economictimes.indiatimes.com/rss/drug_approvals"
        keywords: ["haemophilia", "hemophilia", "factor VIII", "factor IX", "rare disease"]
```

---

#### Task 09-03-E: Improve Routing Escalation Logic

**File:** `backend/app/services/routing.py`

Replace the current escalation logic:
```python
# BEFORE (blunt score threshold):
has_high_score = (priority_score is not None and priority_score >= 80.0)
if is_critical or (has_high_score and is_major_event):
    is_escalated = True
```

With compound domain+event+score rule:
```python
# AFTER (compound escalation):
is_major_event = any(w in f"{title} {content}".lower() for w in [
    "approved", "approval", "crl", "complete response letter",
    "black box", "trial halted", "suspended", "acquisition", "merger"
])
is_strategic_domain = primary_fn in (StakeholderFunction.REGULATORY, StakeholderFunction.LEADERSHIP)
has_critical_priority = priority.upper() == "CRITICAL"
has_strategic_score = (priority_score is not None and priority_score >= 85.0)

# Escalation: CRITICAL domain event OR (Regulatory + major event + high score)
if has_critical_priority or (is_strategic_domain and is_major_event and has_strategic_score):
    is_escalated = True
    route_destination = "LEADERSHIP"
    route_role = "LEADERSHIP"
else:
    is_escalated = False
    route_destination = primary_fn.value
    route_role = "FUNCTION"
```

Also add config-driven overrides from `haemophilia.yaml` routing matrix as the primary lookup, with the heuristic as fallback. Read `baseline_routing_matrix` from `get_domain_config()` when available.

---

#### Task 09-03-F: Register New Connectors in Scheduler

**File:** `backend/app/services/scheduler.py`

Add `FiercePharmaRSSConnector` and `ETPharmaRSSConnector` to the connector registry list that the scheduler initializes. The scheduler's existing pattern (dict of `source_id → SourceConnector instance`) requires only adding entries for the two new connectors.

---

#### Task 09-03-G: Add Connector Tests

**File:** `tests/test_connector_health.py`

Add:
- `test_fierce_pharma_connector_registered()` — connector is in registry with correct source_id and tier
- `test_et_pharma_connector_registered()` — same for ET Pharma
- `test_biopharmadive_configured_no_feed()` — source appears in domain config with status `configured_no_feed` and no profiles

---

### 09-03 Verification Gates

```bash
pytest tests/test_connector_health.py -v              # New connector registration tests pass
pytest tests/test_signal_routing_workflow.py -v       # All state machine transitions pass
pytest tests/ -x -q -m "not live"                    # All existing + new tests pass, 0 failures
python scripts/export_openapi.py                       # No schema drift
git diff --exit-code frontend/types/api.ts            # Contract synchronized
pnpm --prefix frontend exec tsc --noEmit             # 0 type errors
node scripts/check-banned-classes.mjs                 # 0 violations
pnpm --prefix frontend run lint                      # 0 warnings
pnpm --prefix frontend run build                     # Clean Turbopack build
```

---

## Full Phase 09 Definition of Done

- [ ] `article.url` correctly used for NewsAPI signals in Signal Detail page — never `newsapi.org/register`
- [ ] `resolve_canonical_provenance()` handles newsapi source_id with pass-through of valid URLs
- [ ] All 6 review action buttons (Acknowledge, Start Review, Approve, Reject, Request Evidence, Dismiss) call `POST /signals/{id}/review`
- [ ] Review state survives page reload (fetched from backend `signal.review_status`)
- [ ] Audit history renders in Signal Detail with reviewer, timestamp, and decision
- [ ] Demo Operator selector in top nav; selected role passed as `reviewer` in review API calls
- [ ] `FiercePharmaRSSConnector` fetches, keyword-filters, and persists to bronze; article link stored as canonical URL
- [ ] `ETPharmaRSSConnector` fetches from topstories + drug_approvals feeds with keyword filtering
- [ ] BioPharma Dive registered in `haemophilia.yaml` with `configured_no_feed` status; appears in Sources Registry
- [ ] `haemophilia.yaml` tier_3_discovery updated with `fierce_pharma`, `et_pharma`, `biopharmadive`
- [ ] Leadership escalation uses compound rule; `score >= 80` alone does not trigger escalation
- [ ] `tests/test_signal_routing_workflow.py` covers full UNREVIEWED→IN_REVIEW→REVIEWED→ACTIONED→DISMISSED state machine
- [ ] `pytest tests/ -x -q -m "not live"` → 115+ passed, 0 failed
- [ ] `pnpm exec tsc --noEmit` → 0 errors
- [ ] `node scripts/check-banned-classes.mjs` → 0 violations
- [ ] `pnpm lint` → 0 warnings
- [ ] `pnpm build` → clean Turbopack build
- [ ] `python scripts/export_openapi.py && git diff --exit-code frontend/types/api.ts` → 0 drift
