# Phase 8: Provenance Traceability + Canonical Overview/Lifecycle Design System Hardening — Pattern Map

**Mapped:** 2026-08-20
**Files analyzed:** 28 target files
**Analogs found:** 27 / 28

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/app/connectors/base.py` | utility (connector contract) | file-I/O (HTTP fetch → bronze persist) | itself (lines 25-38, 190-258) | exact (modify in place) |
| `backend/app/connectors/pubmed.py` | service (connector) | file-I/O | itself (lines 153-213 `_parse_article`) | exact (modify in place) |
| `backend/app/connectors/clinical_trials.py` | service (connector) | file-I/O | `connectors/pubmed.py` `_parse_article` | role-match |
| `backend/app/connectors/newsapi.py` | service (connector) | file-I/O | `connectors/pubmed.py` `_parse_article` | role-match |
| `backend/app/connectors/fda.py` | service (connector) | file-I/O | `connectors/pubmed.py` `_parse_article` | role-match |
| `backend/app/connectors/ema.py` | service (connector) | file-I/O | `connectors/pubmed.py` `_parse_article` | role-match |
| `backend/app/workflows/nodes/ingest.py` | service (workflow node) | transform | itself (lines 62-78 signal-dict rebuild) | exact (modify in place) |
| `backend/app/workflows/runner.py` | service (pipeline runner) | batch | itself (lines 220-258 pg_insert upsert) | exact (modify in place) |
| `backend/app/api/v1/endpoints/signals.py` | controller | request-response (CRUD read) | itself (lines 40-119 `_serialize_signal`) | exact (modify in place) |
| `backend/app/api/v1/endpoints/intelligence.py` | controller | request-response | itself (lines 183-185, 296-297) | exact (modify in place) |
| `backend/app/api/v1/endpoints/observability.py` | controller | request-response | itself (lines 127-154) | exact (modify in place) |
| `backend/app/api/v1/endpoints/registry.py` | controller | request-response | itself (line 81) | exact (modify in place) |
| `backend/app/api/v1/endpoints/ingestion.py` | controller | request-response | itself (lines 119-124) | exact (modify in place) |
| `backend/app/api/v1/endpoints/health.py` | controller | request-response | itself (lines 117-130, `_CONNECTOR_NAMES`) | exact (modify in place) |
| `backend/app/services/ingestion.py` | service | batch | itself (HEALTHY-on-SUCCESS logic) | exact (modify in place) |
| `backend/app/services/confluence.py` | service | transform | itself (lines 64-119, signal_type → source_id) | exact (modify in place) |
| `backend/app/models/__init__.py` | model | CRUD | itself (Signal, Source, SourceHealthLog) | exact (modify in place) |
| `backend/app/schemas/__init__.py` | model (schema) | CRUD | itself (SignalSchema, ScoreBreakdownSchema) | exact (modify in place) |
| `backend/alembic/versions/005_provenance_traceability.py` | migration | batch | `alembic/versions/004_phase7_truthfulness_and_provenance.py` | exact |
| `tests/test_truthfulness_and_invariants.py` | test | — | itself (lines 83-105 confluence test) | exact (modify in place) |
| `frontend/types/api.ts` | config (contract) | — | itself (regenerated via `scripts/export_openapi.py`) | exact |
| `frontend/lib/mappers.ts` | utility | transform | itself (lines 75-186 `mapSignal`) | exact (modify in place) |
| `frontend/lib/api.ts` | utility | request-response | itself (lines 216-226 fetchOverview) | exact (modify in place) |
| `frontend/components/common/EvidenceDrawer.tsx` | component | request-response | `components/metaradar.tsx` `SignalDrawer` (lines 1663-1973) | role-match |
| `frontend/components/common/DataModeBadge.tsx` | component | request-response | itself + `metaradar.tsx` `Badge` (lines 110-118) | exact (modify in place) |
| `frontend/components/signals/SignalCard.tsx` | component | request-response | `metaradar.tsx` `SignalRow` (lines 471-498) | role-match |
| `frontend/components/signals/SignalList.tsx` | component | request-response | `metaradar.tsx` `SignalsPage` (lines 940-1003) | role-match |
| `frontend/components/sources/SourcesOperationsWorkspace.tsx` | component | request-response | itself (getStatusBadge 49-68) + `metaradar.tsx` `SourcesPage` (1415+) | exact (modify in place) |
| `frontend/components/confluence/ConfluenceWorkspace.tsx` | component | request-response | `metaradar.tsx` `ConfluencePage` (lines 1005-1087) | role-match |
| `frontend/components/{calibration,intelligence,contradictions,functions,developments,missing-signals,observability,settings}/Workspace.tsx` | component | request-response | `metaradar.tsx` pages (token-clean pattern) | role-match |

## Pattern Assignments

### `backend/app/connectors/*.py` (service, file-I/O — add provenance keys to raw_payload)

**Analog:** `backend/app/connectors/pubmed.py` `_parse_article` (lines 153-213)

**Core pattern — raw_payload dict must carry `url`, `signal_type`, `source_name`, `evidence_text`** (pubmed.py:186-200 is the pattern; each connector must extend its own dict):

```python
raw_payload = {
    "external_id": pmid,
    "fingerprint": fingerprint,
    "title": title,
    "abstract": scrubbed,
    "abstract_raw": abstract,
    "journal": journal,
    "pub_date": pub_year,
    "mesh_terms": mesh_terms,
    "entities": mesh_terms,
    "pii_scrubbed": True,
    "retrieved_at": retrieved_at.isoformat(),
    "connector_version": self.connector_version,
    "xml_fragment": ET.tostring(article, encoding="unicode"),
    # NEW Phase 8 keys (per connector):
    # "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
    # "signal_type": "PUBLICATIONS",          # map record → haemophilia.yaml:108-121 enum
    # "source_name": journal or "PubMed",
    # "evidence_text": scrubbed,               # verbatim source-derived excerpt (D-08-04)
}
```

**URL rules per connector (verified facts):**
- pubmed: URL already constructed at pubmed.py:181 — also add to raw_payload so it survives node_ingest.
- clinical_trials: add `raw_payload["url"] = f"https://clinicaltrials.gov/study/{nct_id}"`.
- newsapi: FLATTEN nested article dict — `raw_payload["url"] = article["url"]`, `raw_payload["source_name"] = article["source"]["name"]` (currently nested inside `article`, lost at ingest hop).
- fda: **do NOT set url** (API record has no stable public URL — `api.fda.gov/...?search=` is not human-readable). Leave `url` None → renders `SOURCE URL UNAVAILABLE (openFDA API record has no stable public URL)`.
- ema: raw_payload already keeps `"link"` (not `"url"`) — node_ingest must read `payload.get("link")` as fallback.

**Error handling pattern** (pubmed.py:127-131 — per-profile isolation):
```python
except ConnectorFetchError as e:
    return self._fail(profile_id, started, str(e))
except Exception as e:  # noqa: BLE001 — honest per-profile isolation
    logger.exception("PubMedConnector profile %s failed", profile_id)
    return self._fail(profile_id, started, str(e))
```

**Config pattern** (base.py:92-100, health.py:117-130): connectors read `get_domain_config().connectors.get(self.source_id)`; `get_status()` reads ConnectorState (base.py:264-311) and never fabricates.

**Health log pattern** (base.py:323-371 `_persist_health_log`): writes `SourceHealthLog` + updates `Source` via `update(Source).where(...).values(connector_status=..., http_status=..., records_fetched=..., ...)`. **Fix needed:** `http_status` param defaults to `200` (base.py:328) — pass the real connector HTTP status per attempt (D-08-12 #2).

---

### `backend/app/workflows/nodes/ingest.py` (service, transform — pass provenance through, tag synthetic)

**Analog:** itself (lines 62-78)

**Core pattern — signal dict rebuild (MUST be extended to copy provenance keys unchanged):**
```python
"title": payload.get("title", ""),
"content": payload.get("content", payload.get("abstract", "")),
"published_at": payload.get("published_at", row.retrieved_at.isoformat() if row.retrieved_at else datetime.now(timezone.utc).isoformat()),
"signal_type": payload.get("signal_type", "CLINICAL_TRIAL"),   # ← default hides missing connector field
"disease": payload.get("disease", "haemophilia_a"),
"url": payload.get("url", ""),                                  # ← must fall back to payload.get("link") for EMA
# NEW Phase 8 (copy through, no defaults):
# "external_id": payload.get("external_id"),
# "source_name": payload.get("source_name"),
# "evidence_text": payload.get("evidence_text", payload.get("abstract", "")),
```

**Synthetic fallback tagging** (ingest.py:78, `_load_synthetic_fallback` lines 15-31): every dict loaded from `backend/data/synthetic_signals.json` must be tagged before returning:
```python
for entry in data:
    entry.setdefault("is_synthetic", True)
    entry.setdefault("data_mode", "test_fixture")
    entry["provenance_status"] = "synthetic"   # never persist metaradar.internal fake URLs as canonical
```

**Anti-pattern to remove:** `payload.get("signal_type", "CLINICAL_TRIAL")` — no connector sets signal_type today, so every live signal becomes CLINICAL_TRIAL and confluence never fires on live data.

---

### `backend/app/workflows/runner.py` (service, batch — data_mode + provenance in upsert)

**Analog:** itself (lines 220-258)

**Core pattern — pg_insert upsert (extend values() and set_):**
```python
stmt = pg_insert(Signal).values(
    signal_id=sig_uuid,
    fingerprint=fp,
    source_id=source,
    ...
    score_breakdown=sig.get("score_breakdown") or {},
    development_id=dev_uuid,
    data_mode="live",                                  # ← HARDCODED — must be sig.get("data_mode", "live")
    is_synthetic=bool(sig.get("is_synthetic", False)),
    pipeline_run_id=run_uuid,
    embedding=embedding,
    # NEW Phase 8 (add to values()):
    # source_name=sig.get("source_name"),
    # external_id=sig.get("external_id"),
    # ingested_at=now,
    # provenance_status=sig.get("provenance_status"),
    # evidence_text=sig.get("evidence_text"),
    # raw_record_reference=...,                        # raw_signals_bronze.id for TRACE
).on_conflict_do_update(
    index_elements=["fingerprint"],
    set_={
        "title": sig.get("title", ""),
        "content": sig.get("content", ""),
        "retrieved_at": ret_at,
        "canonical_url": url,
        "facts": sig.get("facts") or [],
        "interpretation": sig.get("interpretation") or "",
        "speculation": sig.get("speculation") or "",
        "priority": priority_str,
        "score_breakdown": sig.get("score_breakdown") or {},
        "pipeline_run_id": run_uuid,
        # NEW: also refresh provenance fields in set_ so re-runs don't stale them
    }
)
```

**URL construction (runner.py:204-212) — REMOVE the fda branch:**
```python
url = sig.get("url") or sig.get("canonical_url")
if not url:
    if source == "pubmed" and ext_id:
        url = f"https://pubmed.ncbi.nlm.nih.gov/{ext_id}/"
    elif source == "clinical_trials" and ext_id:
        url = f"https://clinicaltrials.gov/study/{ext_id}"
    # elif source == "fda" ...: ← DELETE — API endpoint is not a canonical record URL (D-08-02)
```

---

### `backend/app/api/v1/endpoints/signals.py` (controller, request-response — remove fabrication)

**Analog:** itself (lines 40-119 `_serialize_signal`)

**Anti-pattern to remove (lines 44-102):**
```python
# 1. Re-splitting stored total into 25/30/25/20 (lines 47-54, 71-76) — D-08-10 violation
# 2. Re-scoring on read with novelty_distance=0.5 (lines 57-69, 82-98) — fabricated novelty
# 3. data_mode = getattr(s, "data_mode", "live") or "live" (line 111) — default hides missing
# 4. confidence = getattr(s, "confidence", 0.85) or 0.85 (line 134) — no confidence column exists in DB!
```

**Replacement pattern (emit stored values, honest nulls):**
```python
if s.score_breakdown and isinstance(s.score_breakdown, dict):
    try:
        score_breakdown = ScoreBreakdownSchema(**dict(s.score_breakdown))   # verbatim, no recompute
    except Exception:
        score_breakdown = None
else:
    score_breakdown = None
    scoring_status = "not_computed"                                          # never default to 'computed'
```
- Drop the `confidence` field entirely (no DB column); render `confidence_type`/`confidence_rationale` only when present.
- `data_mode = getattr(s, "data_mode", None)` — no `or "live"` default.
- Add to the response: `source_name`, `external_id`, `ingested_at`, `provenance_status`, `evidence_text`, `raw_record_reference` (new columns from migration 005).

**Response serialization pattern** (signals.py:116-136 — `SignalSchema(...)` kwargs dict) stays.

---

### `backend/app/api/v1/endpoints/intelligence.py` (controller, request-response — remove fabrication)

**Analog:** itself (lines 183-185, 296-297)

**Anti-pattern to remove:**
```python
score=score if signals_data else 75.0,                          # line 183 — fabricated 75.0
independent_sources_count=independent_count if signals_data else 3,  # line 185 — fabricated 3
score=score if signal_types else 75.0,                          # line 296
label=f"{conf.confluence_type.capitalize()} Confluence ({independent_count or 3} Independent Sources)",  # line 297
```

**Replacement:** emit `score=None` / `independent_sources_count=0` when no signals; drop `or 3`. Follow the existing "Zero-fabrication gate" comment pattern at signals.py:391 ("If no evidence is found, return honest failure notice").

---

### `backend/app/api/v1/endpoints/observability.py` (controller, request-response — remove fabricated http_code)

**Analog:** itself (lines 127-154)

**Anti-pattern (lines 134-136):**
```python
http_code = hl.http_status if (hl and hl.http_status is not None) else s.http_status
if http_code is None and conn_status == "HEALTHY":
    http_code = 200        # ← fabricated; emit null when not probed
```
**Replacement:** drop the `if http_code is None and conn_status == "HEALTHY"` block; pass `http_status=http_code` (may be `None`). Add `configuration_error_message` (new column) to the response payload, mirroring the existing dict at lines 148-154.

---

### `backend/app/api/v1/endpoints/registry.py` (controller, request-response — remove fabricated LIVE)

**Analog:** itself (line 81)

**Anti-pattern:**
```python
connector_status="LIVE" if s.status == "active" else "DEGRADED",   # 'LIVE' not in canonical 8-state enum
```
**Replacement:** map from real telemetry: `connector_status=s.connector_status or "NEVER_CONNECTED"`; add `configuration_error_message` and `last_attempted` (migration 005 columns) to the emitted item — mirror `SourceRegistryItem` schema in `backend/app/schemas/registry.py`.

---

### `backend/app/api/v1/endpoints/ingestion.py` (controller, request-response — fix AttributeError)

**Analog:** itself (lines 119-124)

**Bug (runtime AttributeError):** references `log.log_id` and `log.error_message` — model has `id` and `last_error` (migration 004:119-133). Replace with:
```python
"id": log.id,
"last_error": log.last_error,
```
plus add `configuration_error_message` surfacing for the NewsAPI missing-key path (`CONFIGURATION_ERROR: NEWSAPI_KEY missing`).

---

### `backend/app/services/ingestion.py` (service, batch — honest telemetry)

**Analog:** itself (HEALTHY-on-SUCCESS logic)

**Changes:**
1. Minimum-records rule: `SUCCESS` with `0` fetched → `DEGRADED` with reason.
2. `records_rejected` = actual rejection count (not `conn_dups` — duplicates ≠ rejected).
3. Record real `http_status` per attempt into Source + SourceHealthLog (see base.py `_persist_health_log`, default-200 fix).

---

### `backend/app/services/confluence.py` + `workflows/nodes/confluence.py` (service, transform — source_id semantics)

**Analog:** `services/confluence.py` (lines 64-119)

**Semantics change (DIR-15 — backend rule and frontend wording must agree):** switch `distinct_types` grouping from `signal_type` to `source_id`:
```python
distinct_types = set(s.get("signal_type", "CLINICAL_TRIAL").upper() for s in window_signals)
# → distinct_sources = set(s.get("source_id") for s in window_signals)
```
- Update `ConfluenceResult.independent_sources_count` semantics + `SIGNAL_TYPE_WEIGHTS` usage (lines 11-19, 49-62).
- **Update the locking test** `tests/test_truthfulness_and_invariants.py:83-105` (currently asserts signal_type semantics: "2 signals from different signal types" / "3 distinct signal types").

---

### `backend/app/models/__init__.py` + `backend/app/schemas/__init__.py` (model, CRUD — new columns)

**Analog:** `models/__init__.py` Signal/Source/SourceHealthLog classes; migration 004 added matching columns

Add to **Signal** model (mirror migration 004 column additions, e.g. lines 20-35):
```python
source_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
ingested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
provenance_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
evidence_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
raw_record_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
```
Add to **Source**: `configuration_error_message: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)`.
Add same fields to `SignalSchema`/`SourceRegistryItem`/`ConnectorHealthStatus` in `schemas/__init__.py` + `schemas/registry.py`.

---

### `backend/alembic/versions/005_provenance_traceability.py` (migration, batch — NEW)

**Analog:** `backend/alembic/versions/004_phase7_truthfulness_and_provenance.py` (lines 8-133)

**Imports + header pattern (lines 8-15):**
```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '005_provenance_traceability'
down_revision = '004_phase7_truthfulness'
branch_labels = None
depends_on = None
```

**Column-add pattern (copy from 004 lines 20-35 and 89-116):**
```python
def upgrade():
    op.add_column('signals', sa.Column('source_name', sa.String(100), nullable=True))
    op.add_column('signals', sa.Column('external_id', sa.String(255), nullable=True))
    op.add_column('signals', sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('signals', sa.Column('provenance_status', sa.String(50), nullable=True))
    op.add_column('signals', sa.Column('evidence_text', sa.Text(), nullable=True))
    op.add_column('signals', sa.Column('raw_record_reference', sa.String(255), nullable=True))
    op.add_column('sources', sa.Column('configuration_error_message', sa.String(255), nullable=True))

def downgrade():
    for col in ['configuration_error_message']:
        op.drop_column('sources', col)
    for col in ['raw_record_reference', 'evidence_text', 'provenance_status', 'ingested_at', 'external_id', 'source_name']:
        op.drop_column('signals', col)
```

---

### `frontend/types/api.ts` (config/contract — regenerate)

**Pattern:** file header (lines 1-2) is auto-generated — never hand-edit:
```typescript
// Auto-generated from FastAPI OpenAPI Schema & Frontend Domain Contract — DO NOT EDIT DIRECTLY
// Generated by scripts/export_openapi.py
```
After backend schema changes, run `scripts/export_openapi.py` (quality gate `contract_sync: true` in `.planning/config.json`). New Signal fields flow into `Signal` (types/api.ts:53-100); `ConnectorHealthStatus` (172-186) and `SourceRegistryItem` (496-511) gain `configuration_error_message`/`last_attempted`.

---

### `frontend/lib/mappers.ts` (utility, transform — remove fabrication, null-safe pass-through)

**Analog:** itself (lines 75-186 `mapSignal`)

**Anti-patterns to remove (all verified):**
```typescript
const sid = raw.signal_id || raw.id || `SIG-${Math.random().toString(36).substring(2, 7)}`  // line 87 — fabricated id
let score = 50                                                                             // line 93 — default score
score = 85 / 70 / 50 / 30                                                                  // lines 101-107 — priority→score map
// lines 110-139: frontend 25/30/25/20 re-split of total (D-08-10 violation)
const confidence = raw.confidence !== undefined ? ... : 85                                  // line 141 — fabricated 85
// lines 158-163: fabricated stakeholders
data_mode: raw.data_mode || 'live',                                                        // line 182
scoring_status: raw.scoring_status || 'computed',                                          // line 184
confidence_type: raw.confidence_type || 'extraction',                                      // line 185
```

**Replacement pattern (pass through, null-safe):**
```typescript
const sid = raw.signal_id || raw.id || ''                    // no random fallback
score: raw.score ?? raw.score_breakdown?.total ?? null,      // derived once on backend, emitted unchanged
confidence: raw.confidence ?? undefined,                     // omit when absent
data_mode: raw.data_mode,                                    // no 'live' default
scoring_status: raw.scoring_status ?? 'not_computed',        // honest default
stakeholders: raw.stakeholders ?? {},                        // no fabricated map
// + pass through NEW fields: source_name, external_id, ingested_at, provenance_status, evidence_text, raw_record_reference
```
Keep `formatTimeAgo` (lines 54-73) and `severityMap` (76-85) as-is.

---

### `frontend/lib/api.ts` (utility, request-response — remove fallback fabrication)

**Analog:** itself (lines 216-226 fetchOverview)

**Anti-patterns to remove:**
```typescript
score: data.confluence?.score || 0,       // line 216 — 0 fabricates "calculating"
confidence: l.confidence || 85,           // line 226 — fabricated 85
score: Math.round((r.similarity_score || 0.5) * 100),  // line 136 — fabricated 0.5
// fetchHealth: hardcoded latencyMs: 85, sourceCount: 6
```
**Replacement:** `score: data.confluence?.score ?? null`, `confidence: l.confidence ?? undefined`, null-safe `??` instead of `||` fallbacks; fetchHealth emits real health values or null.

---

### `frontend/components/common/EvidenceDrawer.tsx` (component, request-response — token sweep + provenance sections)

**Analog:** `components/metaradar.tsx` `SignalDrawer` (lines 1663-1973) — the canonical token-clean drawer

**Core structural pattern to copy (drawer shell):**
```tsx
<div className="drawer-backdrop" onClick={onClose}>
  <motion.aside ... className="signal-drawer overflow-y-auto max-h-screen" onClick={(e) => e.stopPropagation()}>
    <div className="drawer-top">
      <Badge tone={signal.severity}>{signal.severity}</Badge>
      <button className="icon-button" onClick={onClose} aria-label="Close drawer"><X size={18} /></button>
    </div>
    <h2>{signal.title}</h2>
    <p className="drawer-summary">{signal.summary}</p>
    <div className="drawer-score">
      <strong>{signal.score}</strong>
      <span>Priority Score</span>
      <span className="font-semibold text-signal">{signal.confidence}% Confidence</span>
    </div>
    <h3>Evidence & provenance</h3>
    <p className="muted evidence-note">Source material supporting this intelligence.</p>
    {/* source-line rendering per canonical SignalDrawer lines 1956-1969 */}
  </motion.aside>
</div>
```
(globals.css `.drawer-backdrop`/`.signal-drawer`/`.drawer-top`/`.drawer-score`/`.source-line` already exist — lines 245-270.)

**Banned classes to remove (EvidenceDrawer.tsx):** lines 61-63 (`bg-slate-950/60`, `bg-white dark:bg-slate-900`, `border-slate-200 dark:border-slate-800`), 70, 74, 81, 85, 93, 110-124. Replace per sweep table below.

**Fabrication to remove:** line 104 `Total: ... ${signal.score || 50} pts` → `signal.score ?? 'NOT AVAILABLE'`.

**New provenance sections (DIR-4):** External ID, Retrieved/Ingested timestamps, `Open Original Source ↗` link when `canonical_url` truthy, else `SOURCE URL UNAVAILABLE` + reason (`provenance_status`), verbatim evidence excerpt, TRACE reference (`raw_record_reference`).

---

### `frontend/components/common/DataModeBadge.tsx` (component, request-response — TEST FIXTURE/SYNTHETIC badges)

**Analog:** itself (lines 12-33) + canonical `Badge` (metaradar.tsx:110-118)

**Banned classes (lines 16, 27):** `bg-amber-950/60 text-amber-300 border-amber-800/60`, `bg-emerald-950/60 text-emerald-300 border-emerald-800/60` → replace with `.badge` semantic classes + token colors:
```tsx
<span className={`badge badge-${isSynthetic ? 'critical' : 'neutral'}`}>
```
**Semantics change (UI-SPEC §2.4):** `test_fixture`/synthetic → **"TEST FIXTURE"** danger tone (not "Recorded Demo Data"); live → "LIVE INTELLIGENCE" (keep green tone via `badge` + token `var(--success)` if needed).

---

### `frontend/components/signals/SignalCard.tsx` + `SignalList.tsx` (component, request-response — token sweep)

**Analog:** `metaradar.tsx` `SignalRow` (lines 471-498) + `SignalsPage` (940-1003)

**Canonical SignalRow pattern to copy (metaradar.tsx:478-497):**
```tsx
<button className="signal-row" onClick={() => onSelect(signal)}>
  <span className={`severity-dot ${signal.severity}`} />
  <div className="signal-copy">
    <div><strong>{signal.title}</strong><Badge tone={signal.severity}>{signal.severity}</Badge></div>
    <span>{signal.summary}</span>
    <small>{signal.detectedAt} · {signal.sources.length} sources</small>
  </div>
  <div className="signal-score"><strong>{signal.score}</strong><span>priority score</span></div>
  <ChevronRight size={17} className="muted" />
</button>
```
(globals.css `.signal-row`/`.signal-copy`/`.signal-score`/`.severity-dot` exist — lines 169-183.) Consume mapper output verbatim — no local score/confidence fabrication. Add a provenance row (source_name + canonical_url link / SOURCE URL UNAVAILABLE).

---

### `frontend/components/sources/SourcesOperationsWorkspace.tsx` (component, request-response — token sweep + real telemetry)

**Analog:** itself (getStatusBadge 49-68) + `metaradar.tsx` `SourcesPage` (1415+)

**Anti-patterns (verified):**
- `getStatusBadge` hardcoded emerald/amber/red/slate classes (lines 49-68); no CONFIGURATION_ERROR case → falls into NEVER_CONNECTED branch. **Add CONFIGURATION_ERROR case** mapped to `configuration_error_message`.
- `{s.http_status || '200 OK'}` (line 178) — fabricated 200 → `s.http_status ?? '—'`.
- `records_accepted || 0` (line 174) — keep but display fetched/rejected/last_attempted too.
- h1 `text-xl font-bold text-slate-900 dark:text-slate-100` (line 74) → `<SectionTitle eyebrow title detail />`.

---

### `frontend/components/confluence/ConfluenceWorkspace.tsx` (component, request-response — remove fabrication + token sweep)

**Analog:** `metaradar.tsx` `ConfluencePage` (lines 1005-1087)

**Canonical confluence card pattern (metaradar.tsx:1033-1071):**
```tsx
<Card key={conf.confluence_id} className="confluence-tint">
  <div className="flex items-center justify-between mb-2">
    <div className="flex items-center gap-2">
      <Zap size={16} className="text-[var(--warning)]" />
      <strong className="text-sm">{conf.development_title}</strong>
    </div>
    <Badge tone="high">{conf.confluence_type}</Badge>
  </div>
  <p className="text-xs text-[var(--muted-foreground)] mb-3">
    Detected {new Date(conf.created_at).toLocaleDateString()} · {conf.signal_count} signals converged within 48h
  </p>
  {/* contributing signals — ADD canonical_url link or SOURCE URL UNAVAILABLE (line 179 currently omits) */}
</Card>
```
**Fabrications to remove:** `score || 75.0` (line 45), `independent_sources_count || 3` (46, 49, 51), `reasoning` fallback (51), `calculation_version || 'confluence_v2.0'` (134), full inspect fallback (41-54). **Copy change:** "≥3 distinct source types required" (66, 99) → align wording with backend source_id semantics (DIR-15). Banned classes at 202-204.

---

### Workspace components: calibration, intelligence/Athena, contradictions, functions, developments, missing-signals, observability/ActivityStream, settings (component, request-response — token sweep only)

**Analog (token-clean page pattern):** `metaradar.tsx` `LifecyclePage` (lines 1089-1149) — the canonical token-var() page; `DashboardPage` (760-938).

**Shared structural pattern to copy (SectionTitle + Card + loading/error/empty):**
```tsx
<SectionTitle eyebrow="..." title="..." detail="..." />
<Card>
  {loading && !data ? (
    <div className="py-12 text-center text-[var(--muted-foreground)]">
      <Activity size={24} className="animate-spin text-signal mx-auto mb-2" />
      <p>Loading ...</p>
    </div>
  ) : error && !data ? (
    <div className="error-card">
      <h3>Failed to load</h3>
      <p>{error.message}</p>
      <button className="retry-button" onClick={() => refetch()}><RefreshCw size={14} /> Retry</button>
    </div>
  ) : items.length > 0 ? (
    /* content */
  ) : (
    <div className="empty-state">...</div>
  )}
</Card>
```
(globals.css `.error-card` lines 339-341, `.empty-state` 234/272-276, `.retry-button` 338 already exist.)

**Banned-class sweep table (UI-SPEC §4; verified occurrences):**

| Banned utility | Replace with |
|----------------|--------------|
| `bg-white dark:bg-slate-900` / `bg-white dark:bg-slate-900/60` | `var(--surface-elevated)` / `var(--surface)` |
| `bg-slate-50 dark:bg-slate-950/60` | `var(--surface-secondary)` |
| `border-slate-200 dark:border-slate-800` | `var(--border)` |
| `text-slate-900 dark:text-slate-100` (h1) | `<SectionTitle>` + `var(--foreground)` |
| `text-slate-600 dark:text-slate-400` | `var(--muted-foreground)` |
| `bg-slate-100 ... text chip` | `.badge .badge-neutral` |
| `bg-amber-500`/`bg-red-600` buttons | `var(--warning)` / `var(--danger)` via `bg-[var(--...)]` |

Files with 100+ matches confirmed: `CalibrationWorkspace.tsx`, `SettingsWorkspace.tsx`, `EvidenceDrawer.tsx`, `ContradictionWorkspace.tsx`, `FunctionsWorkspace.tsx`, `AthenaWorkspace.tsx` (plus SignalCard/SignalList/SourcesOperations/Confluence).

**Data fetching pattern (copy, don't hand-roll):** `useLiveData<T>(fetcher, intervalMs, deps)` from `@/lib/hooks` (hooks.ts:21-131) — used by every canonical page (metaradar.tsx:761, 944, 1006, 1090, 1153).

**Error display pattern:** `formatError(err, fallback)` + `<ErrorState ... />` from `@/lib/errors` (errors.ts:24-56) — SettingsWorkspace.tsx:25-26, 86-93 is the reference.

**Theme pattern (do NOT modify):** ThemeProvider + FOUC inline script (layout.tsx:43-59) + `@theme inline` (globals.css:7-27) are correct (D-08-09). The theme bug source is banned classes in components — the fix IS the token sweep.

---

## Shared Patterns

### Banned Tailwind classes (UI-SPEC BANNED list)
**Apply to:** all frontend workspace components, drawers, modals
```text
bg-slate-*, text-slate-*, border-slate-*, bg-[#...], text-[#...], border-[#...],
dark: variants paired with hardcoded light values
```
**Token-compliant alternatives (globals.css `@theme inline` lines 7-27 + CSS vars):**
- `bg-surface`, `bg-surface-secondary`, `bg-surface-elevated` → `var(--surface)`, `var(--surface-secondary)`, `var(--surface-elevated)`
- `text-foreground`, `text-muted-foreground` → `var(--foreground)`, `var(--muted-foreground)`
- `border-border` → `var(--border)`; semantic `text-[var(--signal)]`, `text-[var(--warning)]`, `bg-[var(--danger)]` are COMPLIANT (metaradar.tsx uses them throughout — e.g. lines 1037, 1533, 1640).

### Canonical design primitives (metaradar.tsx — do NOT modify)
**Source:** `frontend/components/metaradar.tsx` lines 110-148, 760-938, 1089-1149
```tsx
export function Badge({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: 'critical'|'high'|'medium'|'low'|'neutral' }) {
  return <span className={`badge badge-${tone}`}>{children}</span>
}
export function Card({ children, className = '' }) { return <section className={`panel ${className}`}>{children}</section> }
export function SectionTitle({ eyebrow, title, detail }) { ... }
```
Backing CSS: globals.css `.badge`/`.badge-critical|high|medium|low|neutral` (143-148), `.panel` (138-139), `.section-title`/`.eyebrow`/`.muted` (133-137).

### Honest state rendering (SOURCE URL UNAVAILABLE)
**Apply to:** EvidenceDrawer, SignalCard, ConfluenceWorkspace contributing-signal list
```tsx
{signal.canonical_url ? (
  <a href={signal.canonical_url} target="_blank" rel="noreferrer" className="text-link">
    Open Original Source <ChevronRight size={14} />
  </a>
) : (
  <span className="muted text-[10px] uppercase tracking-wider">
    SOURCE URL UNAVAILABLE {signal.is_synthetic ? '(test fixture)' : `(${unavailableReason})`}
  </span>
)}
```
Canonical `text-link` styling: globals.css line 167.

### No-fabrication invariant (backend)
**Source:** `backend/app/core/logging.py` (structlog + `_scrub_secrets` lines 7-21), `base.py:262` ("honest health, no fabricated state")
**Apply to:** all endpoints — never `x || constant` for missing values; emit null/honest states (`not_computed`, `SOURCE URL UNAVAILABLE`, `CONFIGURATION_ERROR: <message>`).

### Logging (structlog, no hand-rolled tables)
**Source:** `backend/app/core/logging.py` (lines 24-50)
```python
def get_logger(name: str = "metaradar") -> Any:
    return structlog.get_logger(name)
```
Per-attempt events must include connector, url, status, latency, fetched/accepted/rejected, rejection reason, signals created/updated — `_scrub_secrets` already guards (SENSITIVE_KEYS lines 7-11).

### Tests
**Source:** `tests/test_truthfulness_and_invariants.py` (lines 1-17 setup; 23-53 scoring invariant; 83-105 confluence threshold; 111-126 scrubbing; 132-146 correlation id)
- Setup: `sys.path.insert(0, str(base_dir / "backend"))`, `from app.main import app`, `AsyncClient(transport=ASGITransport(app=app))`.
- **Must update** confluence test (83-105) for source_id semantics.
- **Must add** regression tests: `POST /api/v1/ingestion/run` no AttributeError (log.id/last_error fix); signals serializer emits stored score_breakdown verbatim (no recompute); live signal persists correct signal_type; connector raw_payload carries url/signal_type/source_name.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/alembic/versions/005_provenance_traceability.py` | migration | batch | No exact-name analog — use 004 migration pattern (exact structural match, listed above) |

(All other 27 files have in-place or role-match analogs — the codebase already contains every pattern needed.)

## Metadata

**Analog search scope:** `backend/app/` (connectors, workflows/nodes, workflows/runner.py, api/v1/endpoints, services, models, schemas, core), `backend/alembic/versions/`, `frontend/components/`, `frontend/lib/`, `frontend/types/`, `frontend/app/`, `tests/`
**Files scanned:** 40+
**Pattern extraction date:** 2026-08-20

## PATTERN MAPPING COMPLETE