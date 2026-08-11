# MetaRadar: Software Requirements Specification (SRS)

**Project:** MetaRadar - Real-Time Haemophilia Competitive Intelligence Radar  
**Version:** 2.0  
**Date:** August 2026  
**Organization:** MS Ramaiah Institute of Technology (MSRIT)  
**Hackathon:** Novo Nordisk GBS Hackathon 2026  
**Problem Statement:** #3 - From Inbox Noise to Strategic Signal | Pilot Area: Haemophilia within Rare Disease

---

## **1. INTRODUCTION**

### 1.1 Purpose
MetaRadar detects early market signals and paradigm shifts in the **haemophilia treatment landscape within Rare Disease** (Haemophilia A and Haemophilia B — from IV factor replacement to subcutaneous bispecific antibodies like emicizumab, concizumab, and mim8, and single-administration gene therapies like Hemgenix and Roctavian) by converting fragmented public signals into role-specific intelligence for Novo Nordisk teams, formatted in a **Four-Question Framework**:
- **Q1 WHAT CHANGED?** — Signal detection (new trial results, regulatory decisions, competitor announcements, congress presentations, publication releases, patient access changes)
- **Q2 WHY DOES IT MATTER?** — Clinical/commercial significance scoring for Novo Nordisk's Haemophilia portfolio (concizumab, mim8)
- **Q3 WHICH NOVO NORDISK FUNCTION SHOULD REVIEW IT?** — Role-based routing (Medical Affairs / Regulatory / Market Access / Commercial / R&D)
- **Q4 WHAT INTERNAL ACTION MAY BE REQUIRED?** — AI-suggested actions (human review required)

### 1.2 Scope
**MVP Scope (Weeks 1-4):**
- 5 Business Roles: Medical Affairs, Regulatory, Market Access, Commercial, R&D
- Therapy Area: **Haemophilia within Rare Disease (Haemophilia A + Haemophilia B)**
- Scope includes: current and emerging treatment approaches, competitor activity, regulatory changes, trial milestones, congress updates, publications, patient/access narratives, future pipeline developments (emerging competitor assets)
- Multi-Source Public Ingestion: PubMed Central, NewsAPI, ClinicalTrials.gov, FDA OpenFDA, EMA RSS, Reddit PRAW, Congress Abstract archives (ASH, ISTH, WFH, EHA), 500-signal synthetic demo fallback
- 7-Agent LangGraph Pipeline: Ingestion Agent → Validation Agent → NLP Agent → Signal Confluence Agent → Narrative Synthesis Agent → Brief Agent → **Stakeholder Calibration Agent**
- Core Features: Entity extraction, B.Pharm Haemophilia ontology, Signal Confluence Detection, Four-Question UX, **Stakeholder Calibration Loop (HITL)**, Ask Athena RAG conversational search

### 1.3 Definitions & Acronyms
- **Signal:** Any piece of public information (article, clinical trial result, regulatory filing, patient forum post) relevant to haemophilia CI
- **Entity:** Named drug, company, trial phase, mechanism, or indication (e.g., emicizumab, mim8, concizumab, Hemgenix, Roctavian)
- **Role:** Functional team (Medical Affairs, Regulatory, Market Access, Commercial, R&D)
- **Four-Question Framework:** Panel 1 (What changed?), Panel 2 (Why does it matter?), Panel 3 (Which function?), Panel 4 (What action may be required?)
- **Stakeholder Calibration Loop:** HITL feedback process recalibrating function scoring weights based on simulated or real persona ratings
- **Confluence:** Detection that multiple independent signal types converge on the same haemophilia entity within 48h → elevated alert
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
- System SHALL fetch signals from PubMed, NewsAPI, ClinicalTrials.gov, FDA OpenFDA, EMA RSS, Reddit PRAW, and Congress abstract repositories using haemophilia query terms
- System SHALL support async parallel fetching
- System SHALL implement rate limiting per source (500/day for NewsAPI)
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

**FR-2.2.2: Signal Classification**
- System SHALL classify each signal into one of the haemophilia taxonomy:
  - `gene_therapy_milestone` — gene therapy trial results, approvals, or setbacks
  - `non_factor_therapy_update` — bispecific antibodies, anti-TFPI, RNAi therapies (emicizumab, concizumab, fitusiran, mim8)
  - `inhibitor_development_signal` — inhibitor development reports (critical safety/clinical signal)
  - `regulatory_milestone` — FDA, EMA, NICE or other HTA body decisions
  - `congress_publication` — data presentations at ASH, ISTH, WFH, EHA
  - `patient_access_signal` — reimbursement decisions, access restrictions, advocacy positions
  - `competitive_pipeline_move` — competitor assets entering clinical development or phase changes

**FR-2.2.3: Text Summarization (Model-Agnostic)**
- System SHALL generate 1-line (< 50 character) summary of each signal
- Summarization SHALL use a **locally-hosted, configurable model** — no external API calls
- The model is selected via the `LOCAL_LLM_MODEL` environment variable; the system MUST NOT hard-code any specific model name
- Default (hackathon/CPU): `facebook/bart-large-cnn` (seq2seq summarization)
- Supported alternatives (swap via config, zero code change): `google/gemma-2b`, `mistralai/Mistral-7B-Instruct`, `microsoft/phi-3-mini-4k-instruct`, `TinyLlama/TinyLlama-1.1B-Chat`, or any HuggingFace-compatible sequence-to-sequence or text-generation model
- Summary SHALL preserve key entities and metrics
- Every AI-generated summary SHALL carry a disclaimer: *"Auto-generated — verify clinically before use"*

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
      "status": "EU approved 2023, Phase 3 completion"
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
      "brand_names": ["Alhemo"],
      "mechanism": "RNAi (antithrombin inhibitor, subcutaneous)",
      "manufacturer": "Sanofi",
      "indications": ["Haemophilia A and B", "with/without inhibitors"],
      "formulations": ["subcutaneous injection"],
      "competitors": ["emicizumab", "concizumab"],
      "status": "FDA approved 2023"
    },
    "marstacimab": {
      "brand_names": ["Investigational"],
      "mechanism": "Anti-TFPI monoclonal antibody",
      "manufacturer": "Pfizer",
      "indications": ["Haemophilia A and B", "without inhibitors"],
      "formulations": ["subcutaneous injection"],
      "competitors": ["concizumab"],
      "status": "Phase 3"
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

### 2.3 Signal Confluence Detection

**FR-2.3.1: Confluence Pattern Matching**
- System SHALL detect confluence using the configured `HAEMOPHILIA_CONFLUENCE_PATTERNS`
- Pattern: multiple independent signals (≥ 3) mentioning the same haemophilia entity within a 48-hour window → confluence alert

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

### 2.4 Four-Question Dashboard

**FR-2.4.1: Four-Question UI Layout**
- System SHALL present intelligence in 4 panels:
  - **Q1 WHAT CHANGED?** — Signal Feed (real-time, signal type badges, entity tags)
  - **Q2 WHY DOES IT MATTER?** — Relevance breakdown, AI explanation, confluence alert, competitive context
  - **Q3 WHICH FUNCTION SHOULD REVIEW IT?** — Role-routing badges with confidence scores
  - **Q4 WHAT ACTION MAY BE REQUIRED?** — AI-suggested action bullets prefaced *"Suggested — requires human review"*

**FR-2.4.2: Role-Specific Views**
- System SHALL display a role badge for each signal (Q3)
- System SHALL display function-specific insight panel per role:
  - Medical Affairs: clinical evidence context, KOL opinion, congress data
  - Regulatory: filing/review context, approval timelines, label updates
  - Market Access: HTA/reimbursement context, access barriers, patient impact
  - Commercial: market share context, competitor positioning, pricing signals
  - R&D: mechanistic context, pipeline implications, trial design signals

**FR-2.4.3: Filtering & Search**
- System SHALL support filtering by role, signal type, entity, date range, source, and confluence status
- System SHALL support keyword search across signals

### 2.5 Role-Based Routing (Q3)

**FR-2.5.1: Automatic Role Routing**
- System SHALL score each signal against all 5 Novo Nordisk roles using a weighted scoring matrix
- Weights SHALL be dynamically recalibrated by the Stakeholder Calibration Loop (FR-2.8)
- System SHALL display role assignment with confidence score (e.g., `Regulatory 92% · Medical Affairs 84%`)

**Role Scoring Matrix (initial weights):**
| Role | Clinical Trial Signal | Regulatory Signal | Congress Publication | Patient Access Signal | Pipeline Signal |
|------|----------------------|-------------------|----------------------|----------------------|-----------------|
| Medical Affairs | 0.9 | 0.4 | 0.8 | 0.4 | 0.6 |
| Regulatory | 0.3 | 0.95 | 0.3 | 0.2 | 0.5 |
| Market Access | 0.3 | 0.5 | 0.4 | 0.9 | 0.3 |
| Commercial | 0.4 | 0.4 | 0.6 | 0.7 | 0.8 |
| R&D | 0.7 | 0.3 | 0.5 | 0.2 | 0.85 |

### 2.6 Brief Generation (Q4)

**FR-2.6.1: Action Suggestion Generation**
- System SHALL generate action suggestions per signal, prefaced with *"Suggested — requires human review"*
- Examples:
  - Regulatory signal on competitor: *"Suggested — review mim8 label change for haemophilia B alignment"*
  - Gene therapy durability data: *"Suggested — Medical Affairs to draft response on factor vs gene therapy durability"*
  - Market access blocker: *"Suggested — Market Access to re-run HTA budget impact model with new inhibitor data"*

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

**FR-2.8.3: Weight Recalibration**
- System SHALL provide `POST /api/v1/calibrate` — triggers `StakeholderCalibrationService.recalibrate(role)`
- Recalibration SHALL update `scoring_weights` table and persist a calibration history row (audit)

**FR-2.8.4: Simulated Stakeholder Personas (Hackathon Demo)**
- System SHALL seed simulated persona feedback during the demo so calibration is demonstrable
- Personas: Medical Affairs Lead (haemophilia), Regulatory Affairs Specialist, Market Access Manager
- Calibration loop SHALL be visible in the UI (e.g., "Weights recalibrated 3x this month — latest by Regulatory persona")

**FR-2.8.5: Confidence Score Display**
- Role routing SHALL display the feedback-informed confidence (e.g., "Regulatory 92% — up from 88% after calibration")

---

## **3. NON-FUNCTIONAL REQUIREMENTS**

### 3.1 Performance
- Signal fetch: < 3 minutes for full multi-source run
- Signal processing: < 60 seconds per 100 signals (BART, CPU)
- Cold start (no cache): < 3 seconds
- Cached start: < 500 ms
- Ask Athena response: < 30 seconds (local inference)
- System SHALL handle 1,000 signals without degradation

### 3.2 Security & Compliance
- System SHALL redact PII/PHI before persistence (spaCy-based PII scrubber)
- System SHALL support CORS with configurable allowlist (`CORS_ORIGINS`)
- All external API calls SHALL be HTTPS with credentials via `.env` (never in code)
- No secrets SHALL be committed to the repository (validate `.env` is gitignored)
- System SHALL maintain append-only `audit_log` (WORM) compliant with GxP / 21 CFR Part 11 for traceability

### 3.3 Availability & Reliability
- Data sources SHALL be treated as unreliable; system SHALL never crash on source failure
- Fallback to synthetic demo dataset SHALL always be available offline
- tenacity + httpx retry: 3 retries (2s, 4s, 8s) with exponential backoff

### 3.4 Data Protection & Responsible AI
- System SHALL ingest only **public** or **synthetic** data — no private/patient-identifiable data
- AI outputs SHALL be clearly labeled as AI-generated; no automated clinical decisions
- Guardrail statement SHALL appear in docs and UI: *"MetaRadar ingests only public API and synthetic demo data, no confidential or private data, fully CDA-compliant."*

### 3.5 Model-Agnostic Local AI
- All AI models SHALL be locally hosted (no external inference APIs)
- Model names SHALL be configurable via environment variables (never hard-coded)
- Default models: spaCy `en_core_sci_md`, BART `facebook/bart-large-cnn` (summarization), zero-shot classifier, MiniLM embeddings

---

## **4. INTERFACE REQUIREMENTS**

### 4.1 API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/signals` | List signals with filters |
| GET | `/api/v1/signals/{id}` | Signal detail with evidence chain |
| GET | `/api/v1/entities` | Tracked entities + tag counts |
| GET | `/api/v1/confluences` | Active confluence alerts |
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
| `LOCAL_LLM_MODEL` | Local summarization/QA model | facebook/bart-large-cnn |
| `EMBEDDING_MODEL` | Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| `CORS_ORIGINS` | CORS allowlist | http://localhost:3000 |

### 4.3 Database Schema
- `signals` — id, title, source, source_url, published_at, summary, entities, signal_type, quality_score, embedding
- `signal_types` — type, label, description, confidence_threshold
- `entities` — id, name, type, metadata (from haemophilia ontology)
- `signal_entities` — signal_id, entity_id
- `stakeholder_feedback` — id, signal_id, role, rating, reason, user_id, created_at (WORM)
- `scoring_weights` — role, signal_type, weight, version, updated_by, updated_at
- `calibration_history` — id, role, old_weights, new_weights, trigger_reason, created_at
- `confluences` — id, entities, pattern_name, signals, created_at, severity
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
4. Role routing: Commercial 85%, R&D 88%, Medical Affairs 80%
5. Q4 action: *"Suggested — Commercial to assess emicizumab response and update positioning documents"*

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
| AC-7 | Stakeholder calibration: persona submits feedback → weights recalibrate → confidence updates |
| AC-8 | Ask Athena answers ≥ 2 demo queries with cited evidence |

### 6.2 MVP Demo Script (15 minutes)
1. Open dashboard → Q1 feed shows live haemophilia signals (synthetic + live)
2. Click "Hemgenix 3-year durability" → Q2 relevance, confluence badge, competitive context
3. Show Q3 role badges with confidence scores
4. Show Q4 suggested actions ("Suggested — requires human review")
5. "Ask Athena": "Summarise mim8 latest data" → cited answer
6. Stakeholder calibration demo: submit Regulatory persona feedback → weights update → confidence changes visible

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

