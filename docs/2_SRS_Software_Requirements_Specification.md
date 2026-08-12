# MetaRadar: Software Requirements Specification (SRS)

**Project:** MetaRadar - Real-Time Haemophilia Competitive Intelligence Radar  
**Version:** 2.2  
**Date:** August 13, 2026  
> **v2.2 Change Note:** Provider-agnostic reasoning layer (Master Plan v5.0 §13): FR-2.2.3A/B rewritten — default local Gemma 3 4B, optional hosted xAI Grok (`LLM_PROVIDER=local|xai|auto`), BART degraded factual mode only; new FR-2.2.3C (provider modes), FR-2.2.3D (external-LLM privacy gate), FR-2.2.3E (Grok structured-output + semantic validation), FR-2.2.3F (model metadata), FR-2.2.3G (provider interface + two output schemas); §3.5, §4.2 env vars, §4.3 schema, and AC-23..25 updated. Architecture, ten nodes, five mechanisms, and six primary functions unchanged.
> **v2.1 Change Note:** Integrated B.Pharm domain research (v4.0 master-plan rules): canonical haemophilia classification fields (FR-2.2.5A), nullable clinical-evidence fields (FR-2.2.5B), evidence maturity (FR-2.2.5C), access as a separate intelligence event with 8 access subtypes (FR-2.2.2), Red-Team evidence-check suite A–S (FR-2.3B.2A), and acceptance criteria AC-18..22. Architecture and six primary functions unchanged.
**Organization:** MS Ramaiah Institute of Technology (MSRIT)  
**Hackathon:** Novo Nordisk GBS Hackathon 2026  
**Problem Statement:** #3 - From Inbox Noise to Strategic Signal | Pilot Area: Haemophilia within Rare Disease

> [!IMPORTANT]
> **HISTORICAL REFERENCE DOCUMENT**  
> *Note: This document is a secondary/historical reference and must not override the Master Plan. The sole canonical and authoritative specification for MetaRadar is [METARADAR_MASTER_PLAN_v5.0.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/METARADAR_MASTER_PLAN_v5.0.md).*

---

## **1. INTRODUCTION**

### 1.1 Purpose
MetaRadar is an intelligence radar that converts fragmented public signals into evidence-backed developments and role-specific actions in the **haemophilia treatment landscape within Rare Disease** (Haemophilia A and Haemophilia B — from IV factor replacement to subcutaneous bispecific antibodies like emicizumab, concizumab, and mim8, and single-administration gene therapies like Hemgenix and Roctavian).

Unlike conventional AI systems that merely summarize documents, MetaRadar builds an evidence story around every key development, formatting intelligence into a **Four-Question Framework**:
- **Q1 WHAT CHANGED?** — Signal detection and event understanding, supported by multi-source confluence
- **Q2 WHY DOES IT MATTER?** — Clinical/commercial significance, lifecycle stage, competitive context, and contradiction analysis
- **Q3 WHICH NOVO NORDISK FUNCTION SHOULD REVIEW IT?** — Function relevance and stakeholder-calibrated routing (Medical Affairs / Regulatory / Safety-PV / Market Access / Medical Communications / Leadership; extended: Commercial, R&D)
- **Q4 WHAT INTERNAL ACTION MAY BE REQUIRED?** — AI-suggested actions based on evidence, lifecycle, and missing-signal context (human review required)

### 1.2 Scope
**MVP Scope (Weeks 1-4):**
- 6 Primary Functions: Medical Affairs, Regulatory, Safety / Pharmacovigilance, Market Access, Medical Communications, Leadership (ONE engine routes to all six; Commercial & R&D retained as extended/future roles)
- Therapy Area: **Haemophilia within Rare Disease (Haemophilia A + Haemophilia B)**
- Scope includes: current and emerging treatment approaches, competitor activity, regulatory changes, trial milestones, congress updates, publications, patient/access narratives, future pipeline developments (emerging competitor assets)
- Multi-Source Public Ingestion: NCBI PubMed (E-utilities), NewsAPI, ClinicalTrials.gov, FDA OpenFDA, EMA RSS, Reddit PRAW, Congress Abstract archives (ASH, ISTH, WFH, EHA), 500-signal synthetic demo fallback (PubMed Central/PMC full-text is an OPTIONAL/EXTENSION, not an MVP source)
- 10-Agent LangGraph Pipeline: Ingestion → Validation → NLP → Signal Confluence → **Signal Lifecycle Tracking → Red-Team Contradiction → Missing-Signal Detection** → Narrative Synthesis → Brief → **Stakeholder Calibration Agent**
- Core Features: Entity extraction, B.Pharm Haemophilia ontology, **the Five Advanced Analyses** (Confluence Detection, Signal Lifecycle Tracking, Red-Team Contradiction Analysis, Missing-Signal Detection, Stakeholder Learning Loop), Four-Question UX, Ask Athena RAG conversational search

### 1.3 Definitions & Acronyms
- **Signal:** Any piece of public information (article, clinical trial result, regulatory filing, patient forum post) relevant to haemophilia CI
- **Entity:** Named drug, company, trial phase, mechanism, or indication (e.g., emicizumab, mim8, concizumab, Hemgenix, Roctavian)
- **Function (also "role"):** Internal team. Primary six (kickoff 2026): Medical Affairs, Regulatory, Safety / Pharmacovigilance, Market Access, Medical Communications, Leadership. Extended: Commercial, R&D
- **Four-Question Framework:** Panel 1 (What changed?), Panel 2 (Why does it matter?), Panel 3 (Which function?), Panel 4 (What action may be required?)
- **Stakeholder Calibration Loop:** HITL feedback process recalibrating function scoring weights based on simulated or real persona ratings
- **Confluence:** Detection that multiple independent signal types converge on the same haemophilia entity within 48h → elevated alert
- **Signal Lifecycle:** Chronological state machine per development (Announced → In Trial → Results In → Under Review → Approved → Post-Market / Discontinued); the timeline that links isolated signals into one story
- **Red-Team / Contradiction Analysis:** NLI entailment scan (local `facebook/bart-large-mnli`) flagging contradicting claims about the same entity in a rolling window, plus a devil's-advocate AI review
- **Missing-Signal Detection:** Event-progression state machine flagging expected-but-absent milestones (silent readouts, stalled submissions); confidence grows with silence
- **Pharma Ontology:** Domain knowledge graph (Hemlibra → emicizumab → Roche → Haemophilia A competitor) maintained by B.Pharm team
- **Traceable Insight:** Intelligence output with a complete evidence chain (source URL, date, excerpt, credibility)
- **RAG:** Retrieval-Augmented Generation (pgvector + local LLM for "Ask Athena")
- **HTA:** Health Technology Assessment (e.g., NICE, G-BA) — reimbursement/cost-effectiveness evaluations
- **FVIII / FIX:** Coagulation Factor VIII / Factor IX — deficient in Haemophilia A / Haemophilia B respectively
- **Inhibitor:** Neutralizing antibody developed against factor replacement therapy (~30% of severe Haemophilia A patients) — the key complication and differentiator for non-factor therapies
- **Prophylaxis:** Regular preventive treatment to avoid bleeds (vs. on-demand treatment)
- **AAV Gene Therapy:** Adeno-associated virus based single-administration therapy (e.g., Hemgenix, Roctavian)
- **Bispecific Antibody:** Antibody bridging Factor IXa and Factor X (e.g., emicizumab, mim8)
- **Anti-TFPI:** Antibody blocking Tissue Factor Pathway Inhibitor (e.g., concizumab, marstacimab)
- **EHL Factor:** Extended Half-Life clotting factor (less frequent dosing)
- **RNAi:** RNA interference therapy (e.g., fitusiran — lowers antithrombin)
- **WFH:** World Federation of Hemophilia (patient advocacy)
- **ISTH:** International Society on Thrombosis and Haemostasis (biennial congress)
- **ASH:** American Society of Hematology (annual December congress)

### 1.4 References
- Novo Nordisk GBS Hackathon 2026 Problem Statement #3 & Pilot Guidelines (Haemophilia within Rare Disease)
- Confidentiality Agreement between MS Ramaiah and Novo Nordisk
- Kickoff email scope update (August 12, 2026) — therapy area pivot to haemophilia, Four-Question Framework, Stakeholder Calibration Loop
- Refined Architecture & GitHub Landscape Analysis (doc 5)
- Novo Nordisk Company Analysis & Hackathon Intelligence (doc 6)

---

## **2. FUNCTIONAL REQUIREMENTS**

### 2.1 Signal Ingestion & Aggregation

**FR-2.1.1: Multi-Source Data Fetch**
- System SHALL fetch signals from NCBI PubMed (E-utilities), NewsAPI, ClinicalTrials.gov, FDA OpenFDA, EMA RSS, Reddit PRAW, and Congress abstract repositories using haemophilia query terms
- System SHALL support async parallel fetching
- System SHALL implement rate limiting per source (NewsAPI Developer/free tier = 100 requests/day, development/testing use only; articles delayed up to 24h; NOT real-time, NOT for production/internal deployment — quota-aware connector; on exhaustion fall back to Redis cache → bronze DB → synthetic dataset)
- System SHALL cache fetched data for 2 hours minimum
- System SHALL maintain a 500-signal synthetic dataset for offline demo fallback

**Haemophilia Query Terms:**
```python
HAEMOPHILIA_QUERY_TERMS = {
    "primary": [
        "haemophilia", "hemophilia", "factor VIII", "factor IX",
        "haemophilia A", "haemophilia B", "bleeding disorder"
    ],
    "drugs": [
        "emicizumab", "Hemlibra", "concizumab", "Alhemo", "fitusiran",
        "mim8", "marstacimab", "Hemgenix", "Roctavian", "gene therapy haemophilia"
    ],
    "clinical": [
        "inhibitor development", "prophylaxis haemophilia", "factor replacement",
        "extended half-life factor", "AAV gene therapy", "antithrombin"
    ],
    "regulatory": [
        "haemophilia FDA approval", "haemophilia EMA", "rare disease designation",
        "orphan drug haemophilia", "NICE haemophilia", "haemophilia HTA"
    ],
    "congress": [
        "ASH 2026 haemophilia", "ISTH haemophilia", "WFH congress", "EHA haemophilia"
    ],
    "patient_access": [
        "haemophilia treatment access", "haemophilia reimbursement",
        "haemophilia patient advocacy", "WFH", "NHF hemophilia"
    ]
}
```

**FR-2.1.2: Error Handling & Fallback**
- If any source fails, system SHALL NOT crash
- System SHALL fall back to cached data or synthetic demo dataset
- System SHALL log all failures with timestamp and error details

**FR-2.1.3: Data Deduplication**
- System SHALL identify and remove duplicate signals across sources
- Duplicates identified by > 80% semantic similarity in titles

**FR-2.1.4: Data Validation**
- System SHALL reject signals with text < 50 characters, non-English text, or non-haemophilia scope
- System SHALL assign quality score (0.0-1.0) to each signal

### 2.2 NLP & Entity Extraction

**FR-2.2.1: Named Entity Recognition (NER)**
- System SHALL extract:
  - Drug names (e.g., "emicizumab", "mim8", "concizumab", "fitusiran", "Hemgenix", "Roctavian", "marstacimab")
  - Company names (e.g., "Novo Nordisk", "Roche", "Sanofi", "Pfizer", "BioMarin", "CSL Behring", "Takeda")
  - Indications & Mechanisms (e.g., "Haemophilia A", "Haemophilia B", "bispecific antibody", "gene therapy", "inhibitor development", "anti-TFPI", "EHL factor")
  - Clinical phases (e.g., "Phase 3", "FDA approval", "NICE HTA")
- Extraction SHALL use local spaCy model (`en_core_sci_md`)
- Extraction accuracy target: > 90%

**FR-2.2.2: Signal Classification (Kickoff-aligned)**
- System SHALL classify each normalized signal into the canonical 11-category `signal_type` taxonomy:
  - `clinical_trial` — trial registrations, status changes, protocol amendments, readouts
  - `publication` — FIRST-CLASS signal type (not generic news). Subtypes: `peer_reviewed_publication` · `preprint` · `real_world_evidence` · `post_hoc_analysis` · `long_term_follow_up` · `safety_publication` · `patient_reported_outcomes` · `mechanistic_publication`
  - `congress` — FIRST-CLASS signal type (not generic news). Subtypes: `congress_abstract` · `oral_presentation` · `poster` · `new_congress_data` · `updated_congress_analysis` · `presentation_of_previously_known_data` · `congress_related_safety_signal` · `congress_related_efficacy_signal` · `congress_related_pro` · `congress_related_mechanism_dosing`
  - `regulatory` — FDA, EMA, HTA decisions and filings
  - `safety` — adverse events, safety signals, risk communications
  - `access` — reimbursement decisions, access restrictions, pricing/HTA guidance. **Canonical access subtypes (v4.0):** `access_reimbursement_event` · `restricted_reimbursement` · `supply_access_risk` · `geographic_access_gap` · `budget_impact_signal` · `outcome_based_access_model` · `real_world_access_gap` · `access_support`. Access SHALL be tracked as a **separate intelligence event from regulatory approval** (approval ≠ reimbursement ≠ commercial availability ≠ actual patient access)
  - `market` — market dynamics, share, pricing signals
  - `patient_advocacy` — patient/advocacy positions and narratives
  - `company_news` — press releases, investor communications, corporate announcements
  - `pipeline` — competitor/own asset development moves
  - `other` — relevant but uncategorized
- System SHALL additionally assign a haemophilia domain `signal_subtype` (retained B.Pharm taxonomy, used by confluence patterns): `gene_therapy_milestone` · `non_factor_therapy_update` · `inhibitor_development_signal` · `regulatory_milestone` · `congress_publication` · `patient_access_signal` · `competitive_pipeline_move`
- **Congress and publication signals SHALL participate in Confluence, Lifecycle, Red-Team, priority scoring, function routing, the evidence chain, and stakeholder calibration** (they are first-class signals, never isolated cards). Publications SHALL be connected to the relevant `company`, `asset`, `trial`, `development`, `disease`, and `patient population`.

**FR-2.2.3: Text Summarization (Batch, Model-Agnostic)**
- System SHALL generate 1-line (< 50 character) summary of each signal using a fast local batch summarizer selected via `SUMMARIZER_MODEL` (`SUMMARIZER_TASK` = `summarization`)
- Default (hackathon/CPU): `facebook/bart-large-cnn` (seq2seq — CPU-friendly, meets the < 60s/100-signal target)
- Summarization SHALL use a **locally-hosted, configurable model** — no external API calls; the system MUST NOT hard-code any specific model name
- Summary SHALL preserve key entities and metrics
- Every AI-generated summary SHALL carry a disclaimer: *"Auto-generated — verify clinically before use"*

**FR-2.2.3A: Reasoning & Generation (Provider-Agnostic — Gemma 3 Default Local, Grok Optional Hosted)**
- System SHALL power narrative synthesis, Four-Question reasoning, AI-suggested actions (Q4), and Ask Athena grounded answers through a **provider-agnostic reasoning layer** (`LLMProvider`, FR-2.2.3C/2.2.3G) — default **local provider** `google/gemma-3-4b-it` loaded via `LOCAL_LLM_MODEL` (`LOCAL_LLM_TASK` = `text-generation`), with an **optional hosted provider: xAI Grok API** (`LLM_PROVIDER=xai|auto`; FR-2.2.3C/2.2.3D/2.2.3E)
- Default (hackathon/CPU): `google/gemma-3-4b-it` (Gemma 3 4B Instruct — local, Q4-quantized; **estimated** ~2.6GB weights / ~4.5–7.5GB RAM — planning estimates, actual usage depends on runtime, quantization, context length, and system configuration)
- Light-hardware alternative: `google/gemma-3-1b-it`; other supported local swaps: `mistralai/Mistral-7B-Instruct`, `microsoft/phi-3-mini-4k-instruct`, `TinyLlama/TinyLlama-1.1B-Chat`, or any HuggingFace-compatible text-generation model
- The hosted Grok provider is **required only when `LLM_PROVIDER=xai|auto`**; Gemma SHALL remain fully usable without any external API key, and no deployment SHALL be forced to use Grok
- LLM outputs SHALL remain strictly grounded in retrieved source excerpts (temperature locked, "INSUFFICIENT EVIDENCE" guardrail when no source supports the answer)

**FR-2.2.3B: Automatic Provider Fallback (Demo Safety)**
- The reasoning layer SHALL follow the configured fallback chain (FR-2.2.3C): `local` → Gemma → BART degraded; `xai` → Grok → BART degraded; `auto` → Gemma → Grok → BART degraded
- On reasoning-provider failure (load failure, latency budget, missing API key, timeout, rate limit, quota exhaustion, network failure, invalid or schema-invalid response), the system SHALL move to the next provider in the configured chain; if **no reasoning provider is available**, the system SHALL enter **degraded mode**: `facebook/bart-large-cnn` produces a **source-grounded factual summary only** (no interpretation, no reasoning-based action recommendation, no safety causality), so the dashboard remains available during tested failures
- Degraded mode SHALL be flagged in the UI with the text: *"AI reasoning unavailable — showing source-grounded factual summary"*
- Every fallback SHALL be logged and surfaced in the UI with `fallback_from` + `fallback_reason` (e.g., "running in BART degraded mode — api_timeout") and recorded in model metadata (FR-2.2.3F)

**FR-2.2.3C: Provider Modes (`LLM_PROVIDER`)**
- System SHALL support the `LLM_PROVIDER` env var: `local` (default — Gemma → BART degraded), `xai` (Grok → BART degraded), `auto` (Gemma → Grok → BART degraded)
- System SHALL route all reasoning through one provider interface (FR-2.2.3G): LangGraph nodes SHALL call the provider interface, NOT Gemma or Grok directly; provider-specific logic SHALL NOT be introduced into other nodes
- Providers: `LocalGemmaProvider` · `XAIProvider` · `BartDegradedProvider`
- No deployment SHALL be forced to use Grok; local mode runs with zero external API calls

**FR-2.2.3D: External LLM Privacy Gate (mandatory for hosted providers)**
- Before any external (Grok) API call, the system SHALL run the privacy gate: PUBLIC/SYNTHETIC check → PII/PHI check → CONFIDENTIALITY check → allowed? YES → call Grok; NO → **BLOCK**
- The system SHALL NEVER send: confidential Novo Nordisk strategy · internal forecasts · launch plans · patient-level information · PII/PHI · non-public information · confidential documents
- If blocked: use local Gemma if available → otherwise BART degraded mode → otherwise source-only display
- xAI API data handling does NOT override the hackathon's stricter public/synthetic-only rule (xAI does not use API inputs/outputs for training without explicit permission, but requests/responses are normally retained ~30 days for abuse auditing unless applicable stricter retention arrangements are used — https://docs.x.ai/developers/faq/security)

**FR-2.2.3E: Grok Structured Output & Validation**
- Grok calls SHALL use JSON-Schema structured outputs (`response_format` with `json_schema`) — "please return JSON" alone is insufficient (https://docs.x.ai/developers/model-capabilities/text/structured-outputs)
- The system SHALL validate responses at application level: required fields · enum values · evidence IDs exist · source URLs correspond to retrieved sources · confidence within valid range · evidence level valid · suggested action from the controlled vocabulary · primary/secondary functions valid · no unsupported source IDs · no fabricated entities
- Even when the provider guarantees schema conformity, semantic/evidence validation SHALL still be performed; on validation failure → retry once → fall back per FR-2.2.3B

**FR-2.2.3F: Model Metadata (every generated output)**
- Every generated output SHALL record and persist: `provider` · `model` · `model version/ID` · `task` · `temperature` · `prompt-template ID` · `config hash` · `timestamp` · `fallback status` · `fallback reason` (examples: `{provider: xai, fallback_from: local_gemma, fallback_reason: model_load_failure}`; `{provider: local, model: facebook/bart-large-cnn, mode: degraded_factual, fallback_reason: api_timeout}`)
- Model metadata SHALL be rendered in the UI (provider/degraded badge) and written to the WORM audit log

**FR-2.2.3G: Provider Interface & Two Output Schemas**
- System SHALL implement one conceptual provider interface: `generate_intelligence(evidence, task, output_schema, metadata) -> IntelligenceResult`
- **FULL INTELLIGENCE OUTPUT** (Gemma/Grok): `what_changed` · `why_it_matters` · `primary_function` · `secondary_functions` · `routing_reason` · `suggested_action` · `evidence_level` · `confidence` · `supporting_sources` · `uncertainties` · `contradictions` · `watch_for_next` (+ relevant signal metadata)
- **DEGRADED FACTUAL SUMMARY** (BART only): `factual_summary` · `source_ids` · `source_urls` · `published_at` · `evidence_level` · `degraded_mode=true` · `reason_for_degradation`
- BART SHALL NOT be forced to produce the reasoning schema, and SHALL NOT generate strategic interpretation, unsupported competitor conclusions, treatment recommendations, safety causality, or role-specific strategic recommendations

**FR-2.2.4: Pharma Ontology Enrichment**
- System SHALL maintain a local pharma ontology (JSON) mapping: drug → brand names → mechanism → manufacturer → indications → competitor drugs (haemophilia ontology)
- Ontology SHALL be authored and validated by the B.Pharm team
- Every extracted entity SHALL be cross-referenced against the ontology (e.g., "Hemlibra" → emicizumab → bispecific antibody → Roche → Haemophilia A competitor)
- When an extracted drug belongs to a competitor of Novo Nordisk, the signal SHALL be flagged as a competitive signal at zero extra API cost
- Signals with extracted entities that fail ontology validation SHALL be flagged for B.Pharm QA review

**Haemophilia Ontology (excerpt):**
```json
{
  "drugs": {
    "emicizumab": {
      "brand_names": ["Hemlibra"],
      "mechanism": "Bispecific antibody (Factor IXa/Factor X bridge)",
      "manufacturer": "Roche/Genentech",
      "indications": ["Haemophilia A", "Haemophilia A with inhibitors"],
      "formulations": ["subcutaneous injection"],
      "competitors": ["concizumab", "fitusiran", "mim8"],
      "status": "Approved (FDA 2017, EMA 2018)"
    },
    "concizumab": {
      "brand_names": ["Alhemo"],
      "mechanism": "Anti-TFPI monoclonal antibody",
      "manufacturer": "Novo Nordisk",
      "indications": ["Haemophilia A", "Haemophilia B", "with/without inhibitors"],
      "formulations": ["subcutaneous injection"],
      "competitors": ["emicizumab", "fitusiran", "marstacimab"],
      "status": "EU approved 2023; FDA approved December 2024 (12+ HA with FVIII inhibitors or HB with FIX inhibitors); US expansion July 2025 to specified non-inhibitor populations"
    },
    "mim8": {
      "brand_names": ["Investigational"],
      "mechanism": "Next-generation bispecific antibody (Factor IXa/Factor X bridge)",
      "manufacturer": "Novo Nordisk",
      "indications": ["Haemophilia A", "Haemophilia B"],
      "formulations": ["subcutaneous injection"],
      "competitors": ["emicizumab"],
      "status": "Phase 3 (key Novo Nordisk pipeline asset)"
    },
    "fitusiran": {
      "brand_names": ["Qfitlia"],
      "mechanism": "RNAi (antithrombin inhibitor, subcutaneous)",
      "manufacturer": "Sanofi",
      "indications": ["Haemophilia A and B", "with/without inhibitors"],
      "formulations": ["subcutaneous injection"],
      "competitors": ["emicizumab", "concizumab"],
      "status": "FDA approved March 2025 (Qfitlia) — routine prophylaxis 12+ HA/HB with or without FVIII/FIX inhibitors"
    },
    "marstacimab": {
      "brand_names": ["Hympavzi"],
      "mechanism": "Anti-TFPI monoclonal antibody",
      "manufacturer": "Pfizer",
      "indications": ["Haemophilia A and B", "with/without inhibitors"],
      "formulations": ["subcutaneous injection"],
      "competitors": ["concizumab"],
      "status": "FDA approved October 2024 (12+ without inhibitors); approval expanded June 2026 (6+ with or without inhibitors)"
    },
    "etranacogene_dezaparvovec": {
      "brand_names": ["Hemgenix"],
      "mechanism": "AAV5-based gene therapy (Factor IX)",
      "manufacturer": "CSL Behring/UniQure",
      "indications": ["Haemophilia B"],
      "formulations": ["single IV infusion"],
      "competitors": ["valoctocogene_roxaparvovec"],
      "status": "FDA approved November 2022"
    },
    "valoctocogene_roxaparvovec": {
      "brand_names": ["Roctavian"],
      "mechanism": "AAV5-based gene therapy (Factor VIII)",
      "manufacturer": "BioMarin",
      "indications": ["Haemophilia A without inhibitors"],
      "formulations": ["single IV infusion"],
      "competitors": ["emicizumab", "mim8"],
      "status": "FDA approved June 2023"
    }
  },
  "companies": {
    "Novo Nordisk Rare Disease": {
      "portfolio": ["concizumab", "mim8"],
      "pipeline_focus": ["Haemophilia A", "Haemophilia B", "rare bleeding disorders"],
      "key_competitors": ["Roche", "Sanofi", "Pfizer", "BioMarin", "CSL Behring", "Takeda"]
    }
  },
  "indications": {
    "haemophilia_a": {
      "description": "Factor VIII deficiency (most common, ~80% of haemophilia cases)",
      "global_prevalence": "~200,000 patients",
      "genetic_basis": "X-linked recessive",
      "treatment_paradigm": "Factor replacement → EHL factors → non-factor (emicizumab) → gene therapy"
    },
    "haemophilia_b": {
      "description": "Factor IX deficiency (Christmas disease, ~20% of cases)",
      "global_prevalence": "~50,000 patients",
      "treatment_paradigm": "Factor replacement → EHL factors → gene therapy (Hemgenix)"
    },
    "inhibitor_development": {
      "description": "Antibody development against factor replacement — major complication",
      "prevalence": "~30% of severe Haemophilia A patients",
      "relevance": "Key differentiator for non-factor therapies (emicizumab, concizumab, fitusiran)"
    }
  },
  "treatment_categories": {
    "factor_replacement": "Standard of care — IV infusion of missing clotting factor",
    "extended_half_life": "EHL factors — less frequent dosing",
    "non_factor_bypassing": "Bispecific antibodies, anti-TFPI (subcutaneous, inhibitor-agnostic)",
    "gene_therapy": "Single-administration curative approach (Hemgenix, Roctavian)",
    "rna_interference": "RNAi-based (fitusiran, antithrombin reduction)"
  },
  "key_congresses": [
    "ASH (American Society of Hematology) — December annually",
    "ISTH (International Society on Thrombosis and Haemostasis) — biennial",
    "WFH World Congress — biennial",
    "EHA (European Hematology Association) — June annually"
  ],
  "patient_advocacy": [
    "World Federation of Hemophilia (WFH)",
    "National Hemophilia Foundation (NHF, USA)",
    "European Haemophilia Consortium (EHC)"
  ]
}
```

**FR-2.2.5: Normalized Signal Dimensions (canonical schema)**
Every normalized signal SHALL carry all of the following dimensions (added to the `signals` schema — not merely documented):
- `disease`: `haemophilia_a` | `haemophilia_b` | `both` | `unknown`
- `patient_type`: `with_inhibitors` | `without_inhibitors` | `unknown`
- `company`: ontology-normalized company name (e.g., Roche, CSL Behring, Novo Nordisk)
- `asset`: ontology-normalized asset/product name (e.g., emicizumab, mim8, Hemgenix)
- `asset_type`: `bispecific_antibody` | `anti_tfpi` | `rnai` | `gene_therapy` | `factor_replacement` | `ehl_factor` | `other`
- `signal_type`: one of the 11 canonical categories (FR-2.2.2) · `signal_subtype`: one of the 7 domain categories (plus congress/publication subtypes per FR-2.2.2)
- `priority`: `high` | `medium` | `low`
- `impacted_functions`: list of impacted functions (primary + secondary)
- `development_id`: identifier of the development chain this signal belongs to (NULL = NEW DEVELOPMENT candidate)
- `event_date`: date of the underlying event (e.g., congress presentation date, publication date)
- `source_id`: canonical reference to the source record in `raw_signals_bronze`
- `evidence_level` / `fis_label`: `fact` | `interpretation` | `speculation`
- `evidence_sufficient`: boolean — result of the evidence-sufficiency gate (FR-2.2.7)

**FR-2.2.5A: Haemophilia Domain Classification (mandatory, B.Pharm research — v4.0)**
- In addition to FR-2.2.5 dimensions, every normalized signal SHALL carry these canonical domain fields: `disease` (`haemophilia_a` · `haemophilia_b` · `both` · `unknown`), `factor` (`fviii` · `fix` · `unknown`), `inhibitor_status` (`with_inhibitor` · `without_inhibitor` · `mixed` · `unknown`), `population` (`adult` · `adolescent` · `child` · `other_or_unknown`), `therapy_modality` (`factor_replacement` · `extended_half_life_factor` · `non_factor` · `bispecific_antibody` · `sirna` · `gene_therapy` · `aav_gene_therapy` · `lentiviral` · `gene_editing` · `other`)
- System SHALL attempt entity resolution (source, product, trial ID, context) before assigning A/B; if the signal says only "haemophilia" and the subtype cannot be established, `disease` SHALL be `unknown`
- System SHALL NOT assume inhibitor status: extract from trigger terms ("FVIII/FIX inhibitor", "neutralising antibody", "inhibitor-positive/negative") or set `unknown`
- System SHALL treat inhibitor status as a core segmentation variable (WFH maintains separate guidance for inhibitors, outcome assessment, and AAV gene therapy — https://guidelines.wfh.org/guidelines/)
- System SHALL detect `INDICATION_EXPANSION` when an indication crosses the inhibitor boundary (e.g., with-inhibitor → with/without-inhibitor), scoring it high-priority

**FR-2.2.5B: Clinical Evidence Fields (nullable, v4.0)**
- For clinical/trial signals, system SHALL support (populated only when supported by source, otherwise NULL): `trial_id` · `trial_phase` · `study_design` · `population` · `comparator` · `primary_endpoint` · `secondary_endpoints` · `abr` · `bleeding_outcome` · `joint_or_target_joint_outcome` · `patient_reported_outcome` · `quality_of_life_outcome` · `treatment_burden` · `follow_up_duration` · `sample_size` · `safety_findings` · `effect_size` · `confidence_interval` · `p_value` · `interim_or_final` · `evidence_maturity`
- System SHALL preserve endpoint definitions (e.g., treated vs all-bleed ABR) and never compare ABR values blindly across differing endpoint definitions

**FR-2.2.5C: Evidence Maturity (v4.0)**
- Every important signal SHALL carry `source_type` · `source_authority` · `evidence_maturity` · `source_date`
- Evidence maturity hierarchy (evidence-context indicator, NOT a truth ranking): **VERY HIGH** = regulatory decision/assessment · **HIGH** = peer-reviewed publication / ClinicalTrials.gov structured update · **MEDIUM/HIGH** = congress abstract/presentation · **MEDIUM** = official company announcement · **LOWER** = secondary media/commentary
- Congress evidence SHALL be ingested as provisional (never discarded); confidence upgrades only on peer-reviewed/registry/regulatory confirmation
- Company announcements SHALL be treated as important early signals but NOT as independently verified evidence

**FR-2.2.6: Fact / Interpretation / Speculation (F-I-S) Classification (mandatory)**
- **FACT** — directly supported by reliable source evidence.
- **INTERPRETATION** — a reasoned interpretation of available evidence (always presented as AI interpretation, never as fact).
- **SPECULATION** — an early/uncertain signal not sufficiently established.
- System SHALL label every intelligence output (summaries, briefs, Q2 explanations, Q4 actions, Athena answers, digest items) with exactly one of FACT / INTERPRETATION / SPECULATION.
- System SHALL NEVER present speculation as fact; F-I-S labels SHALL be stored in the database, rendered in UI signal cards, returned in API responses, written to the audit trail, and evaluated in the evaluation suite.

**FR-2.2.6A: Source Authority Model (v4.0)**
- System SHALL evaluate evidence using: `source type` + `source authority` + `publication/event date` + `evidence maturity` + `corroboration` + `contradictory evidence` (never a simplistic "source X is always true" rule)
- Authority framing SHALL be contextual: authoritative regulatory source (high authority for regulatory facts) · trial registry (high authority for registry/status facts) · peer-reviewed publication (high authority for published findings) · congress (important but potentially preliminary) · company announcement (important primary source but sponsor-originated) · secondary media (discovery, lower authority) · social/community (signal/discovery, not strong evidence by itself)
- System SHALL preserve the distinction between "source says X" and "MetaRadar interprets X as Y": outputs SHALL separate the source claim from the system's own interpretation (F-I-S labels + `source_authority` + `evidence_maturity`)

**FR-2.2.7: Evidence Sufficiency Check (gate before narrative generation)**
- Required flow: Signal → retrieve evidence → evidence sufficient? → YES: generate grounded interpretation → NO: restrict output to verified facts and/or return *"Insufficient evidence to support an interpretation."* + request human review.
- System SHALL NOT invent an interpretation when evidence is insufficient.
- This is consistent with current FDA thinking on AI credibility and enabling independent review of AI-supported outputs.

### 2.3 Signal Confluence Detection

**FR-2.3.1: Confluence Pattern Matching**
- System SHALL detect confluence using the configured `HAEMOPHILIA_CONFLUENCE_PATTERNS`
- Pattern: multiple independent signals (≥ 3) mentioning the same haemophilia entity within a 48-hour window → confluence alert
- **Development-link decision (mandatory for congress/publication signals, tri-state — v4.0):** before creating a new intelligence card, the system SHALL check whether the signal belongs to an existing development (`development_id` match via trial/asset/company). The decision SHALL be one of: **`linked`** (confident match → new evidence event in the existing development/evidence chain; e.g., trial → congress abstract → oral presentation → poster → publication = ONE development, not four unrelated cards), **`possibly_linked`** (ambiguous/partial match → attach **`requires_human_review`** flag; never auto-linked, never auto-created as new), or **`unlinked`** (no plausible match → candidate NEW DEVELOPMENT, human-reviewable). A signal that only repeats known information SHALL be marked repeated/low novelty rather than creating a new event. The link SHALL NOT be forced when evidence is insufficient. Stored: `development_id` · `event_id` · `source_id` · `link_decision`.

**Haemophilia Confluence Patterns (excerpt):**
```python
HAEMOPHILIA_CONFLUENCE_PATTERNS = [
    {
        "name": "gene_therapy_milestone_parade",
        "description": "Multiple independent signals on a gene therapy (Hemgenix/Roctavian) milestone within 48h",
        "signals_required": 3,
        "window_hours": 48,
        "example": "Hemgenix 3-year durability data + ASH 2026 abstract + CSL Behring press release + patient forum discussion in 48h"
    },
    {
        "name": "competitive_regulatory_filing",
        "description": "Multiple signals on a competitor regulatory filing (FDA/EMA) within 48h",
        "signals_required": 3,
        "window_hours": 48,
        "example": "Roche files mim8 sBLA + ASH abstract + analyst commentary"
    },
    {
        "name": "inhibitor_safety_wave",
        "description": "Multiple signals flagging inhibitor development or thromboembolic risk",
        "signals_required": 2,
        "window_hours": 24,
        "example": "Two independent patient reports of thrombosis on fitusiran"
    }
]
```

**FR-2.3.2: Temporal Pattern Detection**
- System SHALL detect temporal patterns using `HAEMOPHILIA_TIMELINE_PATTERNS`:
  - Signal cascades (publication → congress → FDA → journal) within 1 week
  - Follow-up signals (phase 1 → 2 → 3 progression)
  - Gap detection (no signals for a tracked entity for 14+ days)

### 2.3A Signal Lifecycle Tracking (Analysis 2 of the Five)

**FR-2.3A.1: Lifecycle State Machine**
- System SHALL maintain a lifecycle state machine per tracked development (entity + modality + indication): `announced → in_trial → interim_result → final_result → congress_publication → regulatory_development → approved → post_market | discontinued` (legacy `results_in` maps to interim/final result)
- System SHALL assign each new signal to the matching lifecycle chain and advance the current state
- System SHALL order chain events chronologically and link them by entity (temporal linking)
- **Every lifecycle event SHALL record: `event_type` · `event_date` · `development_id` · `source_id`** so evidence events (congress abstract, oral presentation, poster, additional analysis, publication) attach to ONE development timeline
- System SHALL distinguish **NEW DEVELOPMENT** (no matching `development_id` → new chain) from **NEW EVIDENCE ABOUT EXISTING DEVELOPMENT** (matching chain → append event; confluence attempts to connect them)

**FR-2.3A.2: Expected Next Event**
- System SHALL compute the expected next event from the current state (e.g., `results_in → submission announced`; trial → subsequent congress disclosures)
- System SHALL expose `GET /api/v1/lifecycles` and `GET /api/v1/lifecycles/{entity}` returning the full timeline + current state + expected next event

**Haemophilia lifecycle example (mim8):**
```
mim8 (Novo Nordisk · bispecific · Haemophilia A)
├─ 2024-05 announced → Phase 3 initiation
├─ 2026-01 results_in → Phase 3 primary endpoint met
├─ 2026-03 under_review → FDA/EMA submission expected
└─ NEXT EXPECTED: submission announced
```

### 2.3B Red-Team Contradiction Analysis (Analysis 3 of the Five)

**FR-2.3B.1: Contradiction Detection (NLI Entailment)**
- System SHALL run pairwise entailment checks between signals about the same entity within a rolling window (default 90 days) using the local zero-shot NLI model (`facebook/bart-large-mnli`)
- System SHALL flag a contradiction when entailment label = `contradiction` with score > 0.6
- System SHALL NOT make additional API or model-download calls — NLI reuses the same model as signal classification

**FR-2.3B.2: Red-Team Review**
- System SHALL attach a devil's-advocate AI note to every contradiction listing how the evidence could be misleading/incomplete
- System SHALL show BOTH evidence chains (claim A + claim B with source, URL, date) with a `requires_human_review` flag

**FR-2.3B.2A: Evidence-Check Suite (Red-Team checks A–S, v4.0)**
- In addition to NLI contradiction detection, system SHALL run the 19 evidence checks from Master Plan §12.7 on high-impact signals: (A) causality error — never convert "adverse event occurred" into "drug caused adverse event"; (B) duplicate counting — same underlying evidence via trial+congress+announcement+publication ≠ 4 developments; (C) denominator blindness — no risk/cluster interpretation without exposure/sample size where available; (D) population mismatch — no HA→HB, adult→child, inhibitor+→inhibitor− generalisation; (E) endpoint mismatch — no blind ABR comparison across differing endpoint definitions; (F) surrogate overclaim — factor activity ≠ proof of patient-important benefit; (G) small-sample overconfidence; (H) short-follow-up/durability overclaim — early gene-therapy data ≠ lifelong durability; (I) preliminary-evidence error — congress abstract/preprint/press release ≠ final evidence; (J) sponsor/source-independence error — company statement ≠ independent confirmation; (K) stale information; (L) negative-evidence omission — search terminated/withdrawn/unpublished trials; (M) approval ≠ reimbursement; (N) approval ≠ actual patient access; (O) jurisdiction mismatch — no cross-country generalisation of payer decisions; (P) lifecycle disconnection — link publication/congress/registry update to existing record; (Q) statistical significance ≠ clinical significance; (R) contradiction blindness — never report a strong claim without searching for conflicting evidence; (S) governance bypass — no autonomous diagnosis/causality/treatment/decision without qualified human review
- Each triggered check SHALL be surfaced on the signal card as a Red-Team flag with the governing rule cited

**FR-2.3B.3: Contradiction Endpoint**
- System SHALL expose `GET /api/v1/contradictions` (filter by entity, role, date range)

**Haemophilia example:**
```
⚔ CONTRADICTION — "sustained 3-yr Factor IX efficacy" (ASH 2026)
                 vs "declining Factor IX expression in subset" (real-world cohort)
Score: 0.81 · [View evidence A] [View evidence B] · Requires human review
```

### 2.3C Missing-Signal Detection (Analysis 4 of the Five)

**FR-2.3C.1: Expected-Event State Machine (WATCH items)**
- System SHALL derive expected next events from lifecycle state + B.Pharm-authored rules (`MISSING_SIGNAL_RULES`)
- When an expected event is not observed within the configured `max_lag_days`, system SHALL create a **WATCH item** (missing-signal alert): a monitoring signal, NOT a claim that the event will definitely happen
- WATCH items SHALL be clearly labeled as monitoring signals and require human review where appropriate

**FR-2.3C.1A: Stakeholder-Defined WATCH RULES (Watch-for-Next)**
- System SHALL support **stakeholder-defined watch expectations**: a stakeholder may request e.g. *"monitor this competitor Phase III programme for subsequent congress disclosures"*
- Watch relationship: `source_event → expected/interesting next event → monitoring window → responsible function → status`
- Watch statuses SHALL include: `watching` · `new_evidence_detected` · `no_new_evidence` · `watch_expired` · `human_review_required`
- When a new matching signal is detected (e.g., a congress abstract for the watched trial), the system SHALL: link it to the existing development (confluence/lifecycle), flip the watch status to `new_evidence_detected`, and notify the responsible functions
- If nothing appears within the monitoring window, the system SHALL report: *"No subsequent congress evidence observed during the configured monitoring window."* — absence is NEVER interpreted as proof that no activity occurred
- Wording SHALL be limited to *"Watch for" / "Expected/possible next evidence" / "Not observed yet"* — the system never claims the next event will definitely happen
- This extends the existing Missing-Signal mechanism (no separate watch engine)
- System SHALL expose `GET /api/v1/watchlist` and `POST /api/v1/watchlist` (create watch rule)

**FR-2.3C.2: Confidence-by-Silence + False-Positive Discipline**
- System SHALL compute missing-signal confidence that grows with days of silence (e.g., `0.4 + days_since_last_signal * 0.02`, capped at 0.95)
- System SHALL require configurable minimum windows before alerting to avoid over-warning
- System SHALL expose `GET /api/v1/missing-signals` (filter by entity, role, confidence threshold)

**Haemophilia example:**
```
🕳 MISSING SIGNAL — mim8 regulatory submission expected (max lag 180d)
   Last signal: Jan 2026 (Phase 3 readout) · Silence: 95 days · Confidence: 0.66
```

### 2.4 Four-Question Dashboard

**FR-2.4.1: Four-Question UI Layout**
- System SHALL present intelligence in 4 panels:
  - **Q1 WHAT CHANGED?** — Signal Feed (real-time, signal type badges, entity tags, lifecycle state, contradiction/missing-signal flags)
  - **Q2 WHY DOES IT MATTER?** — Relevance breakdown, AI explanation, confluence alert, lifecycle stage, contradiction flags, competitive context
  - **Q3 WHICH FUNCTION SHOULD REVIEW IT?** — Role-routing badges with confidence scores (calibration-informed)
  - **Q4 WHAT ACTION MAY BE REQUIRED?** — AI-suggested action bullets prefaced *"Suggested — requires human review"*

**FR-2.4.2: Role-Specific Views**
- System SHALL display a role badge for each signal (Q3)
- System SHALL display function-specific insight panel per function:
  - Medical Affairs: clinical evidence context, KOL opinion, congress data
  - Regulatory: filing/review context, approval timelines, label updates
  - Safety / Pharmacovigilance: adverse events, safety signals, causality context, risk-communication watch
  - Market Access: HTA/reimbursement context, access barriers, patient impact
  - Medical Communications: scientific FAQ / response readiness, publication plan impact, HCP communication
  - Leadership: executive summary, strategic/portfolio impact, escalation triggers
  - Extended (retained): Commercial — market share, competitor positioning, pricing; R&D — mechanistic context, pipeline, trial design

**FR-2.4.3: Filtering & Search**
- System SHALL support filtering by role, signal type, entity, date range, source, and confluence status
- System SHALL support keyword search across signals

### 2.5 Role-Based Routing (Q3)

**FR-2.5.1: Automatic Role Routing (relevance-based — "Not every signal goes to everyone")**
- System SHALL score each signal against the 6 primary Novo Nordisk functions (plus 2 extended roles) using a weighted scoring matrix
- Each signal SHALL identify a **primary function** and **secondary functions[]**, each with: `function_relevance_score`, role-specific explanation, role-specific impact, and role-specific suggested action — all sharing the same underlying evidence chain
- Each signal SHALL store: `primary_function` · `secondary_functions[]` · `function_relevance_score` · **`routing_reason`** (why this function, why now) · `suggested_action`
- **The routing decision SHALL be explainable.** Example: Signal = Competitor Phase III clinical result → Medical Affairs 91% · Medical Communications 82% · Regulatory 64%, reason: *"Clinical efficacy/safety data with potential implications for scientific understanding and future regulatory review."*
- **Initial routing matrix is a seed, not a hard-coded universal rule:** routes for clinical trial / safety / access / regulatory decision / congress data / publication SHALL follow the initial matrix in the Master Plan §2 (e.g., safety signal → Safety/PV primary; congress data → Medical Affairs + Medical Communications; access issue → Market Access) and SHALL be adjustable through stakeholder calibration (FR-2.8)
- Weights SHALL be dynamically recalibrated by the Stakeholder Calibration Loop (FR-2.8)
- System SHALL display role assignment with confidence score (e.g., `Regulatory 92% · Medical Affairs 84%`) plus the routing reason
- System SHALL NOT create separate intelligence engines per function — one pipeline, role-specific views

**Role Scoring Matrix (initial weights):**
| Function | Clinical Trial | Regulatory | Congress/Publication | Patient Access | Pipeline | Safety | Market |
|----------|----------------|------------|----------------------|----------------|----------|--------|--------|
| Medical Affairs | 0.9 | 0.4 | 0.8 | 0.4 | 0.6 | 0.7 | 0.3 |
| Regulatory | 0.3 | 0.95 | 0.3 | 0.2 | 0.5 | 0.8 | 0.2 |
| Safety / Pharmacovigilance | 0.4 | 0.6 | 0.3 | 0.2 | 0.4 | 0.95 | 0.2 |
| Market Access | 0.3 | 0.5 | 0.4 | 0.9 | 0.3 | 0.2 | 0.6 |
| Medical Communications | 0.5 | 0.3 | 0.7 | 0.5 | 0.5 | 0.5 | 0.3 |
| Leadership | 0.4 | 0.5 | 0.5 | 0.6 | 0.6 | 0.5 | 0.5 |
| Commercial (extended) | 0.4 | 0.4 | 0.6 | 0.7 | 0.8 | 0.3 | 0.8 |
| R&D (extended) | 0.7 | 0.3 | 0.5 | 0.2 | 0.85 | 0.3 | 0.3 |

### 2.6 Brief Generation (Q4)

**FR-2.6.1: Action Suggestion Generation (controlled vocabulary)**
- System SHALL suggest actions from a **controlled action vocabulary** (never only generic "review/monitor"):
  - `monitor` · `review` · `prepare_internal_briefing` · `prepare_scientific_faq` · `escalate` · `request_stakeholder_review` · `no_immediate_action`
- The AI may SUGGEST an action; it MUST NOT autonomously execute any action.
- Every suggested action SHALL include: **Action · Reason · Relevant function · Evidence · Confidence · Human-review requirement** (always required).
- Every suggestion is prefaced with *"Suggested — requires human review"*.
- **Role-aware action mapping (suggestions must be role-specific, not generic):**
  - **Medical Affairs:** Review scientific evidence · Prepare internal scientific briefing · Monitor new clinical evidence
  - **Medical Communications:** Review congress/publication development · Prepare scientific FAQ · Monitor emerging scientific narrative
  - **Regulatory:** Review regulatory implication · Monitor regulatory milestone
  - **Safety / Pharmacovigilance:** Safety review · Request pharmacovigilance assessment · Monitor safety evidence
  - **Market Access:** Review access/reimbursement implications · Monitor HTA/payer developments
  - **Leadership:** Escalate material cross-functional development · Request strategic review
- The AI only SUGGESTS actions; it never executes them (no autonomous execution).
- Examples:
  - Regulatory signal on competitor: *"Suggested — Review: mim8 label change for haemophilia B alignment (Regulatory; requires human review)"*
  - Gene therapy durability data: *"Suggested — Prepare internal briefing: gene therapy durability vs factor replacement (Medical Affairs; requires human review)"*
  - Market access blocker: *"Suggested — Prepare scientific FAQ: inhibitor data implications for HTA (Market Access; requires human review)"*
  - Safety signal: *"Suggested — Escalate: thromboembolic event reports on fitusiran (Safety/Pharmacovigilance; requires human review)"*
  - Congress abstract for existing trial: *"Suggested — Review congress/publication development: ISTH 2026 abstract for FRONTIER4 vs previous disclosures (Medical Communications; requires human review)"*

**FR-2.6.2: Traceability & Sources**
- Every insight SHALL include a traceable evidence chain: source URL, published date, exact excerpt, source credibility
- System SHALL NOT hallucinate — every claim links to a public source or synthetic demo source marked as such

### 2.7 Ask Athena (RAG Interface)

**FR-2.7.1: Conversational Search**
- System SHALL provide conversational query over saved signals using pgvector + local LLM
- Example queries: "What is the latest on mim8?", "Has anyone reported inhibitor rates on emicizumab?"

### 2.8 Stakeholder Calibration Loop (HITL)

**FR-2.8.1: Feedback Submission**
- System SHALL provide an endpoint for stakeholders to submit feedback on signal routing accuracy:
  - `POST /api/v1/feedback` — body: `{signal_id, role, rating (1-5), reason, user_id}`
- System SHALL store feedback in the `stakeholder_feedback` table (append-only, WORM audit)

**FR-2.8.2: Feedback Summary**
- System SHALL provide `GET /api/v1/feedback/summary` — aggregated accuracy, per-role ratings, trend

**FR-2.8.3: Weight Recalibration (expanded scope)**
- System SHALL provide `POST /api/v1/calibrate` — triggers `StakeholderCalibrationService.recalibrate(role)`
- Recalibration SHALL update `scoring_weights` table and persist a calibration history row (audit)
- **Stakeholders SHALL be able to influence: priority · routing · action · watch rules · relevance criteria** (not only priority). A stakeholder comment such as *"Monitor this competitor trial specifically for upcoming congress disclosures"* SHALL produce a visible AFTER state: changed priority, changed primary/secondary functions, changed action, and a created WATCH rule
- **Mandatory demo requirement:** the UI SHALL show a BEFORE/AFTER comparison. Example:
  - BEFORE: Priority = Medium · Routing = Medical Affairs · Action = Monitor
  - FEEDBACK: "Monitor this competitor trial specifically for upcoming congress disclosures"
  - AFTER: Priority = High · Primary = Medical Affairs · Secondary = Medical Communications · Action = Monitor + prepare internal review · **Watch = upcoming congress disclosures**

**FR-2.8.4: Simulated Stakeholder Personas (Hackathon Demo)**
- System SHALL seed simulated persona feedback during the demo so calibration is demonstrable
- Personas (primary): Medical Affairs Lead (haemophilia), Regulatory Affairs Specialist, Safety / Pharmacovigilance Officer, Market Access Manager, Medical Communications Lead, Leadership / GBS Executive
- Personas (extended): Commercial Strategist, R&D Scientist (optional routing)
- Calibration loop SHALL be visible in the UI (e.g., "Weights recalibrated 3x this month — latest by Regulatory persona")

**FR-2.8.5: Confidence Score Display**
- Role routing SHALL display the feedback-informed confidence (e.g., "Regulatory 92% — up from 88% after calibration")

---

## **3. NON-FUNCTIONAL REQUIREMENTS**

### 3.1 Performance
- Signal fetch: < 3 minutes for full multi-source run
- Signal processing: < 60 seconds per 100 signals (batch summarizer, CPU)
- Cold start (no cache): < 3 seconds
- Cached start: < 500 ms
- Ask Athena response: < 30 seconds (local inference; Gemma 3 4B Q4 on CPU — auto-falls back to BART per FR-2.2.3B if the latency budget is exceeded)
- System SHALL handle 1,000 signals without degradation

### 3.2 Security & Compliance
- System SHALL run a **dedicated PII/PHI detection and redaction layer** before persistence (spaCy NER contributes to entity detection but is NOT claimed as a guaranteed scrubber); when detection confidence is insufficient, content SHALL be rejected or quarantined and NOT persisted
- System SHALL support CORS with configurable allowlist (`CORS_ORIGINS`)
- All external API calls SHALL be HTTPS with credentials via `.env` (never in code)
- No secrets SHALL be committed to the repository (validate `.env` is gitignored)
- System SHALL maintain an append-only/WORM `audit_log` **inspired by electronic-record traceability principles** (engineering design analogy). **MetaRadar does NOT claim 21 CFR Part 11 or GxP regulatory compliance**, and is not validated for regulated production use

### 3.3 Availability & Reliability
- Data sources SHALL be treated as unreliable; **target: graceful degradation during tested connector/model failures** (verified by failure-injection tests) — resilience is an acceptance target, not an untested guarantee
- Fallback to synthetic demo dataset SHALL always be available offline
- tenacity + httpx retry: 3 retries (2s, 4s, 8s) with exponential backoff

### 3.4 Data Protection & Responsible AI
- System SHALL ingest only **public** or **synthetic** data — no private/patient-identifiable data
- AI outputs SHALL be clearly labeled as AI-generated; no automated clinical decisions
- Guardrail statement SHALL appear in docs and UI: *"MetaRadar ingests only public API and synthetic demo data, no confidential or private data, fully CDA-compliant."*
- System SHALL be labeled **INTERNAL DECISION SUPPORT ONLY** and MUST NOT: provide treatment recommendations; make medical conclusions; claim product superiority without appropriate evidence; make unsupported competitor comparisons; determine safety causality; replace expert review; or autonomously execute business actions.
- For safety / regulatory / high-impact signals: **AI suggests → human reviews → human decides.**

### 3.5 Model-Agnostic Local AI (with optional gated hosted reasoning)
- All AI models SHALL default to **locally hosted** inference; hosted reasoning (xAI Grok) is OPTIONAL and gated by `LLM_PROVIDER` + the external-LLM privacy gate (FR-2.2.3C/2.2.3D); OpenAI/Claude are NOT used
- Model names SHALL be configurable via environment variables (never hard-coded)
- **Canonical model table (Master Plan §13.8):**

| Role | Default | Alternative |
|---|---|---|
| Reasoning / Four Questions / Athena | Gemma 3 4B local | Grok API |
| Degraded factual summary | BART-large-CNN | — |
| Batch summarization | BART-large-CNN | — |
| NLI | BART-MNLI | — |
| NER | spaCy | — |
| Embeddings | MiniLM | — |

BART is NEVER listed as a reasoning model.

---

## **4. INTERFACE REQUIREMENTS**

### 4.1 API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/signals` | List signals with filters |
| GET | `/api/v1/signals/{id}` | Signal detail with evidence chain |
| GET | `/api/v1/entities` | Tracked entities + tag counts |
| GET | `/api/v1/confluences` | Active confluence alerts |
| GET | `/api/v1/lifecycles` | Lifecycle timelines per entity (FR-2.3A.2) |
| GET | `/api/v1/lifecycles/{entity}` | Single entity timeline + expected next (FR-2.3A.2) |
| GET | `/api/v1/contradictions` | Red-team contradiction alerts (FR-2.3B.3) |
| GET | `/api/v1/missing-signals` | Missing-signal warnings (FR-2.3C.2) |
| GET | `/api/v1/watchlist` | Watch rules + status (FR-2.3C.1A) |
| POST | `/api/v1/watchlist` | Create a watch rule (source_event → expected next event → window → function) |
| GET | `/api/v1/trends` | Signal volume/trend over time |
| GET | `/api/v1/dashboard` | Four-panel summary payload |
| GET | `/api/v1/search` | Keyword/semantic search (Ask Athena) |
| GET | `/api/v1/health` | Service health check |
| POST | `/api/v1/ingest/manual` | Manually trigger ingestion |
| POST | `/api/v1/feedback` | Submit stakeholder feedback (FR-2.8.1) |
| GET | `/api/v1/feedback/summary` | Feedback summary (FR-2.8.2) |
| POST | `/api/v1/calibrate` | Trigger weight recalibration (FR-2.8.3) |

### 4.2 Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | postgres://metaradar:metaradar@db:5432/metaradar |
| `REDIS_URL` | Redis connection | redis://redis:6379 |
| `NEWSAPI_KEY` | NewsAPI key | (empty) |
| `REDDIT_CLIENT_ID/SECRET` | Reddit API creds | (empty) |
| `SPACY_MODEL` | spaCy NER model | en_core_sci_md |
| `LOCAL_LLM_MODEL` | Reasoning/generation LLM (synthesis, briefs, Ask Athena) | google/gemma-3-4b-it |
| `LOCAL_LLM_TASK` | Pipeline task for the reasoning LLM | text-generation |
| `LLM_PROVIDER` | Reasoning provider mode (local/xai/auto) | local |
| `XAI_API_KEY` | xAI/Grok API key (only when LLM_PROVIDER=xai/auto) | (empty) |
| `XAI_MODEL` | xAI/Grok model ID | (configured model) |
| `XAI_TIMEOUT` | Grok request timeout (seconds) | 30 |
| `SUMMARIZER_MODEL` | Fast batch summarizer (also degraded factual fallback) | facebook/bart-large-cnn |
| `SUMMARIZER_TASK` | Pipeline task for the batch summarizer | summarization |
| `NLI_MODEL` | Zero-shot NLI for classification + red-team contradiction | facebook/bart-large-mnli |
| `CONTRADICTION_WINDOW_DAYS` | Red-team rolling entailment window | 90 |
| `MISSING_SIGNAL_MIN_LAG` | Minimum silence before missing-signal alert | 120 |
| `EMBEDDING_MODEL` | Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| `CORS_ORIGINS` | CORS allowlist | http://localhost:3000 |

### 4.3 Database Schema
- `signals` — id, title, source, source_url, published_at, summary, entities, signal_type (11 canonical incl. congress/publication), signal_subtype (incl. congress/publication subtypes), disease, patient_type, company, asset, asset_type, priority, impacted_functions, **development_id, event_date, source_id**, evidence_level (fact/interpretation/speculation), evidence_sufficient, quality_score, embedding, **domain fields (v4.0): factor (fviii/fix/unknown), inhibitor_status (with/without/mixed/unknown), population (adult/adolescent/child/unknown), therapy_modality (canonical 10-value), evidence_maturity (very_high/high/medium_high/medium/lower), source_authority**, **clinical evidence JSONB (nullable): trial_id, trial_phase, study_design, comparator, primary_endpoint, secondary_endpoints, abr, bleeding_outcome, joint_or_target_joint_outcome, patient_reported_outcome, quality_of_life_outcome, treatment_burden, follow_up_duration, sample_size, safety_findings, effect_size, confidence_interval, p_value, interim_or_final**, **access fields (JSONB, nullable): country, jurisdiction, effective_date, expiry_or_review_date, coverage_status, restrictions, prior_authorisation, specialist_centre_requirements, intended_vs_actual_access**, **model_metadata (JSONB, FR-2.2.3F): provider, model, mode (reasoning/degraded_factual), fallback_from, fallback_reason, prompt_template_id, config_hash, temperature, generated_at**
- `signal_routing` — id, signal_id, **primary_function, secondary_functions (JSONB), function_relevance_scores (JSONB), routing_reason, suggested_action**, created_at (one row per signal; FR-2.5.1)
- `action_recommendations` — id, signal_id, action (controlled vocabulary), reason, relevant_function, evidence, confidence, human_review_required, created_at
- `watch_items` — id, watch_id, **source_event_id, expected_event_type, monitoring_window, responsible_function, status (watching/new_evidence_detected/no_new_evidence/watch_expired/human_review_required)**, created_at, resolved_at (stakeholder-defined watch rules; FR-2.3C.1A)
- `missing_signal_watch_items` — id, entity, missing_event, days_since_last_signal, confidence, status (watch/resolved), created_at
- `watchlists` — id, user_id, entity_id, created_at (entity-focus / watchlist feature)
- `digests` — id, role/function, week_start, week_end, items JSONB, created_at
- `signal_types` — type, label, description, confidence_threshold
- `entities` — id, name, type, metadata (from haemophilia ontology)
- `signal_entities` — signal_id, entity_id
- `stakeholder_feedback` — id, signal_id, role, rating, reason, user_id, created_at (WORM)
- `scoring_weights` — role, signal_type, weight, version, updated_by, updated_at
- `calibration_history` — id, role, old_weights, new_weights, trigger_reason, created_at
- `confluences` — id, entities, pattern_name, signals, created_at, severity, **development_id** (link decision: new development vs new evidence)
- `lifecycle_chains` — id, entity, modality, indication, current_state, expected_next, created_at, updated_at
- `lifecycle_events` — id, chain_id, **development_id, signal_id, event_type, event_date, source_id, state**, ordered_date, created_at
- `contradictions` — id, entity, claim_a, claim_b, contradiction_score, red_team_note, status, detected_at
- `missing_signal_rules` — id, pattern, expected_sequence JSONB, max_lag_days, alert_message (B.Pharm-authored)
- `missing_signal_alerts` — id, entity, missing_event, days_since_last_signal, confidence, status, created_at
- `audit_log` — append-only (WORM)

---

## **5. USAGE SCENARIOS (HAEMOPHILIA THEMED)**

### 5.1 Core Scenario: Hemgenix 3-Year Durability Data at ASH
1. ASH 2026 abstract: "Hemgenix 3-year Factor IX expression data shows sustained efficacy"
2. System ingests via PubMed + congress repository + NewsAPI
3. NER extracts: `Hemgenix`, `CSL Behring`, `gene therapy`, `Haemophilia B`
4. Classified: `gene_therapy_milestone` + `congress_publication`
5. Confluence: ≥ 3 signals within 48h → confluence alert (pattern: `gene_therapy_milestone_parade`)
6. Role routing: Medical Affairs 91%, R&D 78%, Commercial 65%
7. Q4 action: *"Suggested — Medical Affairs to brief Haemophilia team on gene therapy durability data vs concizumab/mim8 prophylaxis positioning"*

### 5.2 Scenario: mim8 Phase 3 Readout
1. NewsAPI: "Novo Nordisk mim8 Phase 3 in haemophilia A meets primary endpoint"
2. NER extracts: `mim8`, `Novo Nordisk`, `Haemophilia A`, `Phase 3`
3. Classified: `competitive_pipeline_move`
4. Lifecycle: `results_in` state advanced; expected next = regulatory submission
5. Role routing: Commercial 85%, R&D 88%, Medical Affairs 80%
6. Q4 action: *"Suggested — Commercial to assess emicizumab response and update positioning documents"*

### 5.3 Scenario: Contradiction on Hemgenix Durability
1. ASH abstract claims "sustained 3-year Factor IX efficacy" (PubMed, Dec)
2. Real-world cohort paper reports "declining Factor IX expression in subset" (PubMed, Jan)
3. NLI entailment scan scores the pair `contradiction = 0.81`
4. Red-team note attached: "newest evidence may overturn earlier durability claim — human review required"
5. Q3 routing: Medical Affairs 90% (contradiction flag on signal card)
6. Q4 action: *"Suggested — Medical Affairs to reconcile durability claims before next HTA engagement"*

### 5.4 Scenario: Missing-Signal on Roctavian Submission
1. Roctavian label update signal lands in July (regulatory_milestone)
2. Lifecycle expects next = "next-generation data publication" within 365d
3. No signal for 150 days → missing-signal alert (confidence 0.7)
4. Q3 routing: Regulatory 88%, Commercial 75%
5. Q4 action: *"Suggested — Regulatory to check for silent label/safety developments on Roctavian"*

### 5.5 Scenario: Congress Abstract for an Existing Trial (NEW EVIDENCE, not new card)
1. FRONTIER4 (denecimig, Novo Nordisk) interim data signal exists on ClinicalTrials.gov (development_id = dev-fr4)
2. ISTH 2026 congress abstract for FRONTIER4 is ingested (congress / congress_abstract)
3. Confluence matches `development_id` → abstract links into dev-fr4 evidence chain; lifecycle appends event (event_type=congress_abstract, event_date, source_id) — NO new unrelated card
4. Q3 routing: Medical Affairs 91% · Medical Communications 82% · Regulatory 64% with routing reason
5. Q4 action: *"Suggested — Review congress/publication development: ISTH 2026 abstract for FRONTIER4 vs previous disclosures (Medical Communications; requires human review)"*

### 5.6 Scenario: Stakeholder-Defined Watch-for-Next
1. Stakeholder feedback on a competitor Phase III trial: *"Monitor this competitor trial for future congress disclosures"*
2. System creates a WATCH rule: source_event=trial update → expected_event_type=congress disclosure → window=180d → responsible function=Medical Affairs
3. Status = `watching`; wording: "Watch for upcoming congress disclosures · Expected/possible next evidence · Not observed yet"
4. A congress abstract for the trial arrives → linked to existing development → status flips to `new_evidence_detected` → Medical Affairs + Medical Communications notified
5. Control: if nothing arrives in the window → *"No subsequent congress evidence observed during the configured monitoring window."* (never claims the event did not occur)

---

## **6. ACCEPTANCE CRITERIA & MVP DEMO SCRIPT**

### 6.1 Acceptance Criteria
| ID | Criterion |
|----|-----------|
| AC-1 | System ingests from ≥ 3 live public sources + synthetic fallback offline |
| AC-2 | System correctly extracts haemophilia entities (emicizumab, mim8, concizumab, Hemgenix, etc.) |
| AC-3 | System classifies signals into the 7 haemophilia types with ≥ 85% accuracy |
| AC-4 | Four-Question dashboard renders (Q1-Q4) with live data within 3s cold |
| AC-5 | Role routing shows badges + confidence for ≥ 90% of signals |
| AC-6 | Confluence alert fires on ≥ 3 converging signals within 48h (synthetic seeded) |
| AC-6A | Lifecycle tracker chains ≥ 3 mim8 signals into one timeline with correct state transitions |
| AC-6B | Red-Team engine flags a seeded contradiction (efficacy vs waning) with both evidence chains |
| AC-6C | Missing-Signal detector flags an expected-but-silent readout with growing confidence |
| AC-7 | Stakeholder calibration: persona submits feedback → weights recalibrate → confidence updates |
| AC-8 | Ask Athena answers ≥ 2 demo queries with cited evidence |
| AC-9 | 100% of high-priority signal cards carry Q1–Q4 + evidence + confidence + source + timestamp + F-I-S label |
| AC-10 | ≥85% classification accuracy (disease / patient type / signal type / priority / function) with precision, recall, confusion matrix |
| AC-11 | Top-signal discovery ≤ 5 minutes on a 100-signal weekly batch |
| AC-12 | Evidence-sufficiency gate: insufficient evidence → "Insufficient evidence to support an interpretation", never fabrication |
| AC-13 | Weekly digest generates function-filtered variants for the six primary functions |
| AC-14 | Stakeholder calibration demo shows a visible BEFORE/AFTER change (priority, function routing, and/or action) |
| AC-15 | Congress and publication are first-class signal types with subtypes; a congress abstract for an existing trial links into that development chain (NEW EVIDENCE), not a new card |
| AC-16 | Every high-priority signal carries routing_reason + primary/secondary functions + per-function relevance scores (explainable routing) |
| AC-17 | Watch-for-Next: stakeholder-defined watch rule created → status transitions → new evidence linked to existing development → functions notified; absence returns the "no subsequent congress evidence" wording |
| AC-18 | Domain classification: disease/factor/inhibitor_status/population/modality fields populated on ≥85% of signals; "haemophilia" alone → `unknown`, never guessed |
| AC-19 | Evidence maturity labels present on every high-priority card (VERY HIGH→LOWER hierarchy); company announcement never labeled as independently verified evidence |
| AC-20 | Access tracked separately from approval: approval card does NOT infer reimbursement/actual access; access subtypes (8) supported; jurisdiction recorded on access signals |
| AC-21 | Red-Team evidence-check suite A–S: seeded cases (e.g., causality error, denominator blindness, population mismatch, approval≠access) flagged with governing rule; 7 deterministic evaluation cases (Master Plan §12.11) pass |
| AC-22 | Routing follows the six primary functions: Medical Affairs / Regulatory / Safety-PV / Market Access / Medical Communications / Leadership (extended stakeholders never replace them); every signal has primary + secondary + relevance scores + routing_reason |
| AC-23 | Provider fallback chain (FR-2.2.3B/C): Gemma unavailable → Grok used in xai/auto mode; Gemma + Grok unavailable → BART degraded factual output correctly labeled in the UI ("AI reasoning unavailable — showing source-grounded factual summary") |
| AC-24 | External-LLM privacy gate (FR-2.2.3D): PII/PHI or confidential content → external call blocked; falls back to local Gemma / BART degraded / source-only display |
| AC-25 | Grok structured-output validation (FR-2.2.3E) + model metadata (FR-2.2.3F): schema-invalid or semantically invalid response (fabricated entity, unknown source ID) rejected/retried/fallback; every output carries provider/model/fallback metadata |

### 6.2 MVP Demo Script (15 minutes)
1. Open dashboard → Q1 feed shows live haemophilia signals (synthetic + live)
2. Click "Hemgenix 3-year durability" → Q2 relevance, confluence badge, competitive context
3. Show Q3 role badges with confidence scores
4. Show Q4 suggested actions ("Suggested — requires human review")
5. "Ask Athena": "Summarise mim8 latest data" → cited answer
6. Stakeholder calibration demo: submit Regulatory persona feedback → weights update → confidence changes visible
7. Lifecycle demo: open mim8 timeline → current state `results_in`, expected next event shown
8. Red-Team demo: show seeded contradiction (ASH durability vs real-world waning) with both evidence chains
9. Missing-Signal demo: show flagged silence on a tracked entity with growing confidence
10. Domain-classification demo (v4.0): expand a signal card → DOMAIN row (Disease: Haemophilia B · Factor: FIX · Inhibitor: Without · Population: Adult · Modality: AAV gene therapy) and evidence-maturity label (MEDIUM/HIGH — congress, preliminary, not regulatory); show a bare-"haemophilia" signal resolving to `unknown` (never guessed)
11. Evidence-context demo (v4.0): show Q5 evidence strength, Q6 uncertainty/contradiction, Q7 watch-next panels + Red-Team evidence-check flags (e.g., H short-follow-up vs durability) on the same card
12. Access-separation demo (v4.0): show an approval signal NOT implying reimbursement, and an `ACCESS_REIMBURSEMENT_EVENT`/restricted-reimbursement card routed to Market Access with jurisdiction recorded (approval ≠ reimbursement ≠ availability ≠ access)

---

## **7. APPENDICES**

### 7.1 Glossary Additions (Haemophilia)
- **Concizumab (Alhemo):** Novo Nordisk anti-TFPI antibody for Haemophilia A/B with/without inhibitors
- **Mim8:** Novo Nordisk next-gen bispecific; Phase 3; aims to improve on emicizumab
- **Emicizumab (Hemlibra):** Roche bispecific; standard non-factor care in Haemophilia A
- **Fitusiran:** Sanofi RNAi antithrombin knockdown; approved 2023
- **Hemgenix:** CSL Behring/UniQure gene therapy for Haemophilia B; approved 2022
- **Roctavian:** BioMarin gene therapy for Haemophilia A; approved 2023
- **Inhibitor:** Neutralizing antibody to factor replacement (~30% severe Haemophilia A)
- **Anti-TFPI:** Blocks Tissue Factor Pathway Inhibitor to promote thrombin generation

