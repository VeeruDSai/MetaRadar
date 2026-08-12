# MetaRadar — Risk Register & Guardrails (INTERNAL DECISION SUPPORT ONLY)

**Document:** 9 of the MetaRadar doc set · v1.2 · Aug 13, 2026 (latest stakeholder brief)
**Scope:** Risks of the AI-assisted competitive-intelligence prototype, with detection, mitigation, and human-review requirements. Companion to SRS §3 (Non-Functional / Guardrails), SRS FR-2.2.6/FR-2.2.7 (F-I-S and evidence sufficiency), and the v1.2 additions: relevance-based routing (FR-2.5.1), Congress/Publication first-class signal types (FR-2.2.2), Watch-for-Next (FR-2.3C.1A), and role-aware actions (FR-2.6.1).

---

## 1. GUARDRAIL POLICY (non-negotiable)

### 1.1 Data boundaries

**Allowed:** public information, public APIs, public scientific publications, public company announcements, mock data, synthetic data (labeled `is_synthetic=true`).

**Prohibited:** confidential Novo Nordisk strategy, internal forecasts, patient-level data, patient-identifiable data (PII/PHI — scrubbed before persistence), non-public information, confidential documents, promotional/external-facing content.

### 1.2 System role

> **MetaRadar is INTERNAL DECISION SUPPORT ONLY.**

The system MUST NOT:
- provide treatment recommendations
- make medical conclusions
- claim product superiority without appropriate evidence
- make unsupported competitor comparisons
- determine safety causality
- replace expert review
- autonomously execute business actions

For safety / regulatory / high-impact signals: **AI suggests → human reviews → human decides.**

### 1.3 Evidence rules

- Every high-priority AI output carries: source name, source URL, publication date, source type, supporting excerpt (where available), evidence level, confidence, timestamp, AI-generated label.
- Every output is labeled **FACT / INTERPRETATION / SPECULATION**. Speculation is never presented as fact.
- Evidence-sufficiency gate: insufficient evidence → *"Insufficient evidence to support an interpretation."* + request human review. The system never fabricates an interpretation.
- Suggested actions come from a controlled vocabulary (monitor · review · prepare_internal_briefing · prepare_scientific_faq · escalate · request_stakeholder_review · no_immediate_action); the AI suggests, never executes.

---

## 2. RISK REGISTER (Risk · Cause · Detection · Mitigation · Human review)

| # | Risk | Cause | Detection | Mitigation | Human review |
|---|---|---|---|---|---|
| R1 | **Hallucination** — AI generates claims not in the sources | LLM free-form generation; weak grounding | F-I-S label check; evidence-sufficiency gate; every claim mapped to `source_id`/`excerpt`; retrieval confidence < threshold blocks generation | RAG grounded only in retrieved signals; temperature 0.0; prompts require verbatim-excerpt anchoring; insufficiency guardrail text | Human reviews any output with confidence below threshold; red-team flags |
| R2 | **Unsupported claim risk** — conclusion exceeds evidence | Over-synthesis; single-source amplification | Source-count/platform checks; F-I-S = INTERPRETATION or SPECULATION when evidence is thin; EV-1 source-linking checker | Enforce 100% source-linked summaries; gate narrative on `evidence_sufficient`; FACT = directly supported by an authoritative/reliable source (multi-source corroboration preferred for important interpretations but NOT mandatory for every factual statement) | Human review before any use in briefings; B.Pharm evidence-quality QA (Usha) |
| R3 | **Source quality risk** — low-credibility or adversarial sources (e.g., unverified forums) | Reddit/advocacy or unknown domains weighted like primary literature | Per-domain credibility scores; quality_score ≥ threshold; source tier shown in UI | Weighted credibility in confidence; low-credibility signals labeled and demoted; ontology validation | B.Pharm QA on source selection; analysts decide whether a source is usable |
| R4 | **Conflicting evidence** — sources disagree | Genuine scientific/regulatory disagreement; different cohorts | Red-Team NLI contradiction scan (dual evidence chains) | Contradictions surfaced, never hidden; both claims shown; devil's-advocate note; Q2 flags | Human reconciles before use (e.g., HTA engagement) |
| R5 | **Stale information** — aged data presented as current | Long cache TTL; infrequent fetch; discontinued sources | Data-freshness indicators (<5min/2h/24h/>24h); source-status footer; last-verified timestamps | Redis 2h TTL; 2-hour polling; staleness banners; bronze replay for re-processing | Analysts check publication dates before acting |
| R6 | **Model uncertainty** — local models (Gemma 3 4B, BART) produce weaker reasoning | CPU-bound small models; quantization | Confidence scores; F-I-S labels; provider chain + fallback logged and surfaced in UI (model metadata) | Model-agnostic config via `LLMProvider`; known capability envelope documented; provider chain per `LLM_PROVIDER` (Gemma → Grok → BART degraded factual); optional hosted Grok gated by the external-LLM privacy gate (R28) | Human review required for all AI-generated briefs |
| R7 | **Classification errors** — wrong disease/patient type/signal type/priority/function | NER/zero-shot limits; ambiguous text | EV-2/EV-2b/EV-13 metric harness; B.Pharm-labelled validation set; confusion matrix review | ≥85% classification target; ontology validation layer; false-positive test cases (cardiac "gene therapy", engineering "mim8") | B.Pharm manual QA on flagged signals (Ishaaq labels, Usha reviews) |
| R8 | **Missing-signal false positives** — silence flagged when nothing is wrong | Delayed disclosure; incomplete coverage; changed strategy | Confidence-by-silence threshold; configurable `max_lag_days`; status = WATCH (monitoring, not a claim) | WATCH items clearly labeled; never presented as confirmed events; human review gate | Human verifies against other sources before escalating |
| R9 | **Duplicate / confluence errors** — same event counted as independent confluence | Press-wire syndication; near-duplicate articles | Deduplication (>80% similarity); confluence requires ≥3 distinct signal types; control tests (duplicate wires ≠ confluence) | Dedup before confluence; severity formula; EV-8 control scenarios | Analysts review confluence alerts before acting |
| R10 | **Stakeholder bias** — calibration overfits to one persona's preferences | Sparse feedback; single-user dominance | Feedback counts per persona; weight-drift monitoring; per-role agreement metrics; WORM history | Minimum feedback threshold before recalibration; damped weight updates; simulated-persona diversity | Calibration changes audited; stakeholders review weight changes |
| R11 | **Data-source outages / rate limits** — live APIs fail or throttle | Network, quotas, upstream changes | tenacity retries; per-source health status in UI; rate-limit counters | Fallback cascade: Redis cache → bronze → 500-signal synthetic; **target: graceful degradation during tested failures** (verified by failure-injection tests, not an untested guarantee); quota-aware connectors (NewsAPI Developer tier = 100 req/day) | Operators see degraded-mode banners and decide whether to re-fetch |
| R12 | **Function-routing error** — signal routed to wrong function | Matrix weights mis-set; calibration noise; ambiguous signal type | Q3 confidence + "why this score"; calibration feedback; per-function precision | Six-function matrix with B.Pharm-validated weights (Sanjana); extended roles toggleable | Stakeholder feedback loop corrects routing; human review of high-impact misroutes |
| R13 | **Action-suggestion error** — wrong/unsafe action suggested | Template gaps; missing context; escalation logic errors | Controlled vocabulary conformance (EV-14); action↔evidence linkage check | Vocabulary-only suggestions; no autonomous execution; reason + evidence on every action | Human approves every action; safety/regulatory actions require designated reviewers |
| R14 | **PII / confidential-data leak** — patient or private data enters the pipeline | Scraped content containing names/case data | Dedicated PII/PHI detection + redaction layer before persistence (spaCy NER contributes but is not a guaranteed scrubber); reject/quarantine on low confidence; audit scan (EV-4 target = 0) | Redaction `[REDACTED:LABEL]`; public/synthetic source whitelist; `.env` secrets never in repo | Security review of any flagged content; CDA compliance maintained |
| R15 | **Prompt / ontology drift** — rules or ontology become outdated or wrong | Manual ontology edits; model/prompt changes; new assets | Ontology versioning (`updated_by`); calibration/audit history; B.Pharm QA rows (incl. fitusiran/Alhemo error class) | Versioned ontology + prompts; regression tests on evaluation set; change log in `audit_log` | B.Pharm reviews ontology changes before promotion |
| R16 | **Routing misjudgement (relevance-based)** — signal routed to too many/too few functions | Broadcast-style seed matrix; calibration noise; ambiguous signal type | Q3 shows routing_reason + per-function scores; routing agreement metric (EV-6); feedback loop | Relevance-based routing principle ("not every signal goes to everyone"); seed matrix adjustable via calibration; routing_reason explains every decision | Stakeholders review routing on high-impact signals; calibration corrects future routing |
| R17 | **Congress/publication miscoupling** — new evidence wrongly linked to (or detached from) a development | development_id match errors; same drug different trial; press-wire noise | `link_decision` audit field; lifecycle event record (event_type/event_date/development_id/source_id); control scenarios (EV-9/AC-15) | Confluence requires entity+development match; congress/publication subtype classification; human-review flag on ambiguous links | Analysts verify congress card relationships before acting |
| R18 | **Watch-for-Next false expectations** — stakeholder watch rules create misleading monitoring | Ambiguous stakeholder instructions; window too short/long; expected event never plausible | Watch statuses (watching/new_evidence_detected/no_new_evidence/watch_expired/human_review_required); absence wording guardrail | Wording limited to "Watch for / Expected/possible next evidence / Not observed yet"; absence never claimed as fact; human review on watch expiry | Stakeholders confirm watch rules; analysts review watch-expired items |
| R19 | **Role-action mismatch** — role-aware action inappropriate for the function | Template gaps; wrong function mapping; escalation logic errors | EV-14 conformance; action↔function↔evidence linkage check; calibration feedback | Controlled + role-specific vocabulary (FR-2.6.1, MR-ACT-2); no autonomous execution; reason+evidence on every action | Human approves every action; designated reviewers for safety/regulatory |
| R20 | **Causality error** — adverse event mention converted into drug causality | Correlation inferred from co-occurrence | Red-Team check A (FR-2.3B.2A); causality language probe | Preserve uncertainty; "associated" not "caused"; causality requires qualified human review | Clinical/PV review before any causality statement |
| R21 | **Denominator blindness** — risk % or cluster interpreted without exposure/sample size | Small cohort; missing exposure data | Red-Team check C; evidence-maturity penalty | Block confirmation when denominator absent; flag cluster claims for human review | Analysts verify exposure before escalation |
| R22 | **Population-mismatch generalisation** — HA→HB, adult→child, inhibitor+→inhibitor− extrapolation | Disease/factor/inhibitor fields mis-assigned or assumed | Domain-classifier never-guess rule (FR-2.2.5A); Red-Team check D; EV-15 | `unknown` when insufficient evidence; applicability check before generalisation | B.Pharm QA (Ishaaq/Usha) on flagged signals |
| R23 | **Approval≠access conflation** — regulatory approval presented as reimbursement or patient access | Merged lifecycle events; missing access distinction | Red-Team checks M/N/O; EV-17 access-separation harness | Access tracked as separate event with 8 access subtypes; jurisdiction recorded; intended-vs-actual access field | Market Access review of access signals |
| R24 | **Endpoint/comparability mismatch** — ABR or other outcomes compared across differing endpoint definitions | Treated vs all-bleed ABR; assay differences | Red-Team check E; endpoint-definition preservation in `clinical_evidence` | Preserve endpoint definitions; never blind-compare outcomes | Clinical review before cross-trial claims |
| R25 | **Evidence-maturity mislabel** — preliminary evidence presented with regulatory-level confidence | Congress/company evidence over-weighted | EV-16 evidence-maturity harness; `evidence_maturity` field | Maturity ladder (VERY HIGH→LOWER); company announcements never labeled independently verified | Human review of all AI briefs; B.Pharm evidence QA (Usha) |
| R26 | **Negative-evidence omission** — terminated/unpublished trials ignored in a strong positive narrative | Missing result/termination data | Red-Team check L; registry-status diffs | Actively search for disconfirming evidence before strong claims; lifecycle disconnection check (P) | Analysts reconcile before use |
| R27 | **Duplicate-count inflation** — same evidence counted as multiple independent developments | Trial+congress+announcement+publication of one result | Red-Team check B; development_id linking; EV-9 | Congress/publication link to existing development (NEW EVIDENCE, not new card); repeated → low-novelty | Analysts verify development links |
| R28 | **External-LLM privacy/retention (hosted Grok)** — public/synthetic-only data leaves the local environment; xAI retains requests/responses ~30 days (encrypted, for abuse auditing) | Hosted provider misuse; data-boundary breach | Mandatory external-LLM privacy gate before any Grok call (public/synthetic → PII/PHI → confidentiality → ALLOW/BLOCK); gate decisions logged | Blocked content never sent; on block → local Gemma → BART degraded → source-only; xAI data handling does not override the hackathon's stricter public/synthetic-only rule (no training without explicit permission; ~30-day abuse-audit retention unless applicable stricter arrangements are used — https://docs.x.ai/developers/faq/security); EV-20 | Security review of any external send; CDA compliance maintained |
| R29 | **Hosted provider failure/dependency (Grok)** — outage, key expiry, quota, latency, invalid or schema-invalid responses | External dependency; network; key management | tenacity retries; per-provider health; response schema + semantic validation (FR-2.2.3E); model metadata | Fallback chain per `LLM_PROVIDER` (Gemma → Grok → BART degraded factual; no reasoning provider → source-linked factual signal + human-review flag); dashboard is designed to remain available during tested provider failures (EV-19) | Operators see provider/degraded badges and decide whether to re-fetch/review |

> **v1.1 (Aug 13, 2026):** Added R20–R27 from the B.Pharm domain research integration (Master Plan v4.0 §12) — causality, denominator, population-mismatch, approval≠access, endpoint comparability, evidence-maturity mislabel, negative-evidence omission, and duplicate-count inflation. The six primary functions remain unchanged.
> **v1.2 (Aug 13, 2026):** Added R28 (external-LLM privacy/retention — hosted Grok, Master Plan v5.0 §13.5) and R29 (hosted provider failure/dependency, §13.6); R6 updated to the provider-agnostic chain (Gemma → Grok → BART degraded factual) per `LLM_PROVIDER`.

---

## 3. AUDIT & RECONSTRUCTION

For every AI-generated intelligence output, the system preserves enough metadata to answer: *"What information did the system use to produce this, and with what model?"*

- `evidence_chain` JSONB (source, URL, published_at, excerpt, credibility, sha256)
- `model_metadata` (provider, model name/version, mode, task, temperature, prompt-template id, config hash, fallback status/reason, generated_at)
- WORM `audit_log` (append-only; no UPDATE/DELETE; **engineering design analogy inspired by electronic-record traceability principles** — MetaRadar does NOT claim 21 CFR Part 11 or GxP compliance)
- Append-only `stakeholder_feedback` and `calibration_history`
- `raw_signals_bronze` verbatim payloads with timestamps (full replay)

## 4. RESPONSIBLE-AI COMPLIANCE NOTE

These guardrails align with current FDA thinking on AI credibility in drug development and EMA AI principles: AI supports, humans decide; outputs are independently reviewable; models carry version/credibility metadata; and hallucination is controlled by grounding AI to verified evidence sets. [WEB-VERIFIED]

---

*Risk Register v1.2 · August 13, 2026 · Novo Nordisk GBS Hackathon 2026 — Problem Statement #3 · Team: MSRIT Aura Pharmers*
