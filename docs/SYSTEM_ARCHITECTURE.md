# MetaRadar Technical System Architecture (v5.1.0)

**Autonomous Near-Real-Time Competitive Intelligence Radar for Rare Diseases**  
*Pilot Implementation: Haemophilia A & Haemophilia B*

---

## 1. High-Level System Architecture

MetaRadar employs a modern, decoupled microservices architecture designed for high-throughput biomedical signal ingestion, truthful extraction, and low-latency decision intelligence.

```mermaid
flowchart TB
    subgraph ExternalSources ["Authoritative & Discovery External Feeds"]
        CT["ClinicalTrials.gov API v2"]
        PM["PubMed / Europe PMC"]
        FDA["FDA Drugs@FDA / Recalls"]
        EMA["EMA Regulatory Dossiers"]
        NEWS["Biopharma News / RSS"]
    end

    subgraph IngestionLayer ["Bronze Layer: Autonomous Ingestion"]
        SCHED["Async Scheduler (scheduler.py)"]
        CONN["Connector Registry & Circuit Breakers"]
        RAW_DB[("PostgreSQL: raw_documents")]
    end

    subgraph IntelligencePipeline ["Silver Layer: 10-Node LangGraph Engine"]
        LG1["1. Ingestion Gate"]
        LG2["2. Entity & Ontology Normalizer"]
        LG3["3. Deduplication (SHA-256)"]
        LG4["4. Four-Question Brief Synthesizer"]
        LG5["5. 4-Factor Deterministic Scoring"]
        LG6["6. 48h Confluence Evaluator"]
        LG7["7. Red-Team Contradiction Engine"]
        LG8["8. Missing Signal FSM Tracker"]
        LG9["9. Asset Lifecycle Progression"]
        LG10["10. Stakeholder Relevance Router"]
    end

    subgraph InferenceLayer ["Biomedical Reasoning & Embeddings"]
        GGUF["Local Gemma-3 4B GGUF (llama-cpp-python)"]
        GROK["xAI Grok / OpenAI API (Optional Fallback)"]
        BART["BART-Large-MNLI (Zero-Shot Classifier)"]
        EMBED["SentenceTransformers (all-MiniLM-L6-v2)"]
    end

    subgraph DataPersistence ["Gold Layer: Enterprise Persistence"]
        PG_SIG[("PostgreSQL: signals & developments")]
        PG_VEC[("PGVector: 384d semantic embeddings")]
        PG_AUDIT[("PostgreSQL: audit_log (Immutable Trigger)")]
        PG_APP[("PostgreSQL: approval_requests")]
        REDIS[("Redis: Cache & Distributed Locks")]
    end

    subgraph ApplicationLayer ["FastAPI Backend (Port 8000)"]
        API_SIG["/api/v1/signals & queues"]
        API_APP["/api/v1/signals/.../approval"]
        API_ATHENA["/api/v1/athena (RAG Copilot)"]
        API_AUTH["/api/v1/auth (RBAC & CSRF)"]
        API_OPS["/api/v1/sources & /observability"]
    end

    subgraph PresentationLayer ["Next.js 16 Frontend (Port 3000)"]
        UI_AUTH["3D-Tilt Login (/login)"]
        UI_DASH["Executive Dashboard (/dashboard)"]
        UI_SIG["Scoped Signal Explorer (/signals)"]
        UI_FUNC["Cross-Functional Workspace (/functions)"]
        UI_INTEL["Confluence, Red-Team, Athena (/intelligence)"]
    end

    ExternalSources --> SCHED
    SCHED --> CONN
    CONN --> RAW_DB
    RAW_DB --> LG1
    LG1 --> LG2 --> LG3 --> LG4 --> LG5 --> LG6 --> LG7 --> LG8 --> LG9 --> LG10

    LG2 -.-> BART
    LG4 -.-> GGUF
    LG4 -.-> GROK
    LG5 -.-> EMBED

    LG10 --> PG_SIG
    LG10 --> PG_VEC
    LG10 --> PG_AUDIT
    LG10 --> PG_APP

    PG_SIG --> ApplicationLayer
    PG_VEC --> API_ATHENA
    PG_AUDIT --> API_OPS
    PG_APP --> API_APP

    ApplicationLayer <==> PresentationLayer
```

---

## 2. 10-Node LangGraph Intelligence Pipeline

Each ingested document is processed as an immutable state graph through 10 specialized intelligence nodes:

```mermaid
stateDiagram-v2
    [*] --> IngestionValidation: Raw Document
    IngestionValidation --> EntityExtraction: Valid Disease & Modality
    IngestionValidation --> Dropped: Off-Target Filter

    EntityExtraction --> DeduplicationCheck: Extracted Assets & Targets
    DeduplicationCheck --> BriefSynthesis: Unique Fingerprint
    DeduplicationCheck --> MergeUpdate: Existing Fingerprint Found

    BriefSynthesis --> PriorityScoring: [FACT], [INTERPRETATION], [SPECULATION]
    PriorityScoring --> ConfluenceEvaluation: Novelty + Clinical + Regulatory + Recency
    ConfluenceEvaluation --> ContradictionAnalysis: 48h Multi-Source Linkage
    ContradictionAnalysis --> MissingSignalTracking: Counter-Claims Evaluated
    MissingSignalTracking --> LifecycleProgression: Milestone Status
    LifecycleProgression --> StakeholderRouting: Phase Updated
    StakeholderRouting --> [*]: Signal Emitted to Scoped Queues
```

### Pipeline Node Responsibilities

1. **Ingestion Validation (`ingest_node`)**: Verifies raw document payload, parses MIME types, checks canonical URLs, and records ingestion timestamp.
2. **Entity & Ontology Normalizer (`entity_node`)**: Identifies haemophilia assets (`mim8`, `concizumab`, `fitusiran`, `hemline`), gene therapy vectors (`AAV5`, `AAV-LK03`), and normalizes MeSH / MedDRA terms.
3. **Deduplication (`dedup_node`)**: Computes SHA-256 fingerprints across title, source ID, and external ID to prevent redundant reprocessing.
4. **Four-Question Brief Synthesizer (`synthesis_node`)**: Uses local Gemma-3 4B (or Grok) with strict prompt constraints to generate:
   - `what_changed`: Grounded empirical facts (`[FACT]`).
   - `why_it_matters`: Clinical & competitive significance (`[INTERPRETATION]`).
   - `speculation`: Strategic market hypothesis (`[SPECULATION]`).
5. **4-Factor Priority Scoring (`scoring_node`)**: Computes deterministic weighted score (0–100) based on:
   - Novelty (0.30) + Clinical Impact (0.35) + Regulatory Urgency (0.20) + Source Recency (0.15).
6. **Confluence Evaluator (`confluence_node`)**: Analyzes temporal proximity (48h window) across multiple independent sources to elevate corroborating signals.
7. **Red-Team Contradiction Engine (`contradiction_node`)**: Cross-references clinical endpoints, safety warnings, and adverse events against established registry baselines.
8. **Missing Signal FSM Tracker (`missing_signal_node`)**: Monitors expected milestone deadlines (e.g. promised Phase III readout) and flags overdue variances.
9. **Asset Lifecycle Progression (`lifecycle_node`)**: Maps trial transitions (Phase I $\to$ Phase II $\to$ Phase III $\to$ BLA $\to$ Market) on competitive asset timelines.
10. **Stakeholder Relevance Router (`routing_node`)**: Routes signals to 6 canonical functional queues based on domain calibration profiles.

---

## 3. Cross-Functional RBAC & Approval State Machine

MetaRadar enforces strict Role-Based Access Control and an executive escalation workflow:

```mermaid
stateDiagram-v2
    [*] --> UNREVIEWED: Signal Ingested & Routed

    state FunctionalLead {
        UNREVIEWED --> IN_REVIEW: Lead Opens Signal
        IN_REVIEW --> REVIEWED: Routine Acknowledgment
        IN_REVIEW --> ACTION_REQUIRED: Tactical Action Assigned
        ACTION_REQUIRED --> ACTIONED: Action Executed
        IN_REVIEW --> DISMISSED: Deemed Non-Critical
        
        IN_REVIEW --> PENDING: Escalate to Leadership
        ACTION_REQUIRED --> PENDING: Escalate to Leadership
    }

    state ExecutiveLeadership {
        PENDING --> APPROVED: Executive Authorizes Steer
        PENDING --> REJECTED: Returned with Guidance Note
        
        APPROVED --> ACTIONED: Directive Implemented
        REJECTED --> IN_REVIEW: Re-evaluating
    }
```

### RBAC Permission Matrix

| Capability | Medical Affairs | Regulatory | Safety | Market Access | Comms | Leadership | Admin |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| View Scoped Signal Queue | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View All Cross-Functional Signals | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Request Leadership Approval | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| Resolve Pending Approvals | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Athena Biomedical Q&A | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Recalibrate Scoring Weights | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Trigger Manual Ingestion Sync | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| View Immutable Audit Logs | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## 4. Real-Time Semantic Search & Athena Reasoning

```mermaid
sequenceDiagram
    autonumber
    actor User as Stakeholder (Elena / Alex)
    participant UI as Next.js Frontend
    participant API as FastAPI /api/v1/athena
    participant VEC as PostgreSQL (PGVector)
    participant LLM as Local Gemma-3 / xAI Grok
    participant AUDIT as PostgreSQL (AuditLog)

    User->>UI: Types: "Compare Mim8 vs Hemlibra Phase III endpoints"
    UI->>API: POST /api/v1/athena { prompt }
    API->>API: Generate 384d embedding via all-MiniLM-L6-v2
    API->>VEC: Cosine Distance Search <=> embedding (Limit 10, Score > 0.70)
    VEC-->>API: Return Top-K Grounded Signal Evidence Items
    API->>LLM: Prompt with [STRICT_GROUNDING] + Evidence Context
    LLM-->>API: Synthesized Response with [FACT] / [INTERPRETATION] + Citations
    API->>AUDIT: Append ATHENA_QUERY audit entry
    API-->>UI: Return { answer, confidence, citations, model_metadata }
    UI-->>User: Render Interactive Briefing with Verified Badges
```

---

## 5. Security, Immutability & Responsible AI

1. **Zero-Hallucination Tripartite Gating**: Every synthesized text is split into `[FACT]` (verifiable quote/datum), `[INTERPRETATION]` (clinical significance), and `[SPECULATION]` (future hypothesis).
2. **Cryptographically Sealed Audit Logs**: `audit_log` records are guarded by a PostgreSQL database trigger (`block_audit_log_mutation`) and SQLAlchemy event listeners preventing any `UPDATE` or `DELETE` operations.
3. **Session & CSRF Protection**: Double-submit cookie pattern (`metaradar_csrf`) with `SameSite=Lax` and `HttpOnly` session authentication tokens.
4. **Air-Gapped Offline Resilience**: Operates 100% locally using quantized `gemma-3-4b-it-Q4_K_M.gguf` without external API dependencies.
