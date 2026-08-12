# MetaRadar: Refined Architecture, GitHub Landscape Analysis & Differentiation Strategy

---

> **v2.0 (Aug 12, 2026 kickoff):** Therapy-area pivot to **Haemophilia within Rare Disease**, added the **Stakeholder Calibration Loop (HITL)** as a 7th agent and differentiator, and replaced GLP-1/obesity examples with haemophilia (emicizumab, mim8, concizumab, Hemgenix, Roctavian) throughout.

> **v2.1 (Aug 12, 2026):** Extended to the **Five Advanced Analyses** per the kickoff Executive Summary — Confluence Detection, Signal Lifecycle Tracking, Red-Team Contradiction Analysis, Missing-Signal Detection, Stakeholder Learning Loop. The LangGraph pipeline grows from 7 to **10 agents** (lifecycle, red-team, missing-signal added). Every insight passes all five analyses before reaching the brief.

> [!IMPORTANT]
> **HISTORICAL REFERENCE DOCUMENT**  
> *Note: This document is preserved for historical context and architectural evolution. The sole canonical and authoritative master specification for MetaRadar is [METARADAR_MASTER_PLAN_v3.0.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/METARADAR_MASTER_PLAN_v3.0.md).*

---

## **PART 1: EXISTING GITHUB SOLUTIONS & THEIR GAPS**

The following are the closest open-source equivalents to MetaRadar currently on GitHub. Each has been analyzed for what they do well and where they fall short—specifically for the pharma/haemophilia rare disease CI use case.

---

### **Repo 1: brightdata/competitive-intelligence**
**GitHub:** https://github.com/brightdata/competitive-intelligence  
**Stack:** FastAPI + React + Gemini API + BrightData Scraper  
**Stars:** Active (September 2025)

**What it does:**
```
Input: Competitor name + website URL
Output: SWOT analysis report

Pipeline:
Researcher Agent → Analyst Agent → Writer Agent
(scrape)           (SWOT)          (report PDF)
```

**Gaps:**

| Gap | Why It Matters for MetaRadar |
|---|---|
| **On-demand only** | User triggers one-off analysis. No real-time monitoring, no trend detection. MetaRadar needs *continuous* signal tracking. |
| **General purpose** | No pharma/haemophilia domain awareness. Treats "Roche" the same as "Slack." |
| **Single competitor focus** | One URL in → one report out. Can't track 10 competitors simultaneously across 5 signal types. |
| **No velocity/trend detection** | Doesn't care if a signal is accelerating. Just answers "what is happening now." |
| **No role-based filtering** | Report goes to everyone. No Medical Affairs vs Regulatory vs Commercial lens. |
| **Requires paid APIs** | BrightData = $15/month minimum. Gemini API has cost. Our system uses free APIs only. |
| **No persistence** | No database. Refreshing the page loses everything. |

**What we borrow:**
- Multi-agent pipeline structure (Researcher → Analyst → Writer pattern maps to our Ingestion → NLP → Synthesis agents)
- FastAPI backend structure (already in our plan)

**What we do better:**
- Continuous monitoring vs one-shot analysis
- Pharma-specific entity extraction
- Role-specific intelligence layers
- Free API stack (no BrightData, no paid Gemini)
- Signal velocity (trend acceleration detection)

---

### **Repo 2: vikas-kashyap97/Market-Intelligence-Agent**
**GitHub:** https://github.com/vikas-kashyap97/Market-Intelligence-Agent  
**Stack:** Streamlit + LangChain + Firecrawl + Plotly  
**Agents:** Reader → Analyst → Strategist → Formatter

**What it does:**
```
Input: Market/company topic (text)
Output: Strategic PDF report with charts

Pipeline:
Reader Agent:      Scrapes web + news APIs
Analyst Agent:     Identifies trends, opportunities
Strategist Agent:  Generates recommendations
Formatter Agent:   Creates Plotly visualizations + exports
```

**Gaps:**

| Gap | Why It Matters |
|---|---|
| **Streamlit UI** | Functional but not production-grade. No real-time WebSocket updates, no role auth, no multi-user support. |
| **Report-generation focus** | Produces PDFs/exports. Not a live operational dashboard pharma teams can keep open all day. |
| **No domain taxonomy** | Doesn't understand emicizumab, HTA, anti-TFPI, inhibitor development. Everything is treated as equal-weight text. |
| **LangChain dependency** | Adds ~200MB overhead + complex debugging. Abstracts too much for a hackathon. |
| **No caching layer** | Every question triggers new API calls. Rate limit burns immediately. |
| **No signal deduplication** | Same Reuters story + Bloomberg story = two separate "signals." |
| **No persistence** | Stateless. Refresh = start over. |

**What we borrow:**
- Multi-source data collection pattern (Reader agent conceptually)
- Chart-per-insight layout (Plotly-style correlation charts)
- Modular agent breakdown (each agent does one well-defined job)

**What we do better:**
- Production dashboard (not Streamlit) that multiple roles can use simultaneously
- Persistent state (PostgreSQL + Redis = session survives refresh)
- Domain-specific taxonomy built by B.Pharm team
- Deduplication (73% noise reduction)
- Caching (no rate limit burnout)

---

### **Repo 3: sunhj050623/OpenHawk**
**GitHub:** https://github.com/sunhj050623/OpenHawk  
**Stack:** Python + Docker + CLI + MCP Server  
**What it does:** AI intelligence OS tracking papers, OSS releases, market signals, policy updates

**What it does well:**
```
✓ Multi-scope tracking (papers + market + policy)
✓ LLM summaries with deduplication
✓ Multi-channel push notifications (Slack, email, Telegram)
✓ MCP server interface (AI agents can call it directly)
✓ Multilingual output (EN, KR, JP, FR, CN)
✓ Scheduled fetch + incremental updates (only fetch new)
```

**Gaps for pharma use case:**

| Gap | Why It Matters |
|---|---|
| **CLI-only interface** | No web dashboard. No visual trend charts. Pharma teams won't use a terminal. |
| **General AI/tech focus** | Tracks arXiv, GitHub releases, AI policy. No drug names, no HTA, no clinical phases. |
| **No role-based access** | Single user/single view. Not multi-tenant. |
| **No velocity scoring** | Deduplicates and summarizes but doesn't detect *accelerating* signals. |
| **No entity relationship graph** | Doesn't know that "Hemlibra" = "emicizumab" = bispecific antibody = Roche product / Novo Nordisk competitor. |
| **Push-only** | You receive alerts. Can't query: "What happened with mim8 this week?" |

**What we borrow:**
- Incremental fetch (only fetch new signals since last run = saves API quota)
- Deduplication-before-storage (not after)
- Multi-channel push pattern (Week 4 bonus: email digest for each role)

**What we do better:**
- Web dashboard with interactive charts
- Pharma entity ontology (drug → indication → company → clinical stage hierarchy)
- Query interface ("Ask Athena" lite)
- Role-based multi-user access

---

### **Repo 4: AYLIEN/news-signals**
**GitHub:** https://github.com/AYLIEN/news-signals-datasets  
**Stack:** Python (MIT licensed), RoBERTa-base + Random Forest  
**What it does:** Time series signal detection from news clusters

**What it does well:**
```
✓ Academically validated anomaly detection
✓ Text-to-time-series correlation (can predict stock movements from headlines)
✓ 50-70% anomaly detection rate at 3-8% false positive rate
✓ Zero-shot support via Llama-2-13b
✓ Dataset pipeline tooling
```

**Gaps:**

| Gap | Why It Matters |
|---|---|
| **Library, not product** | No dashboard, no API server, no frontend. Pure Python library. |
| **Academic focus** | Built for Nasdaq-100 / Wikipedia pageviews correlation. No pharma. |
| **No real-time API** | Batch processing of historical datasets. No streaming signal detection. |
| **Heavy compute** | RoBERTa-base + Random Forest needs significant memory. Not demo-laptop friendly. |

**What we borrow:**
- Anomaly detection methodology (our velocity scoring is inspired by AYLIEN's pattern)
- Rolling window trend analysis (7-day windows, same as AYLIEN's window approach)
- Confidence scoring for signal alerts (not binary yes/no, but probability)

**What we do better:**
- Real-time dashboard (not batch pipeline)
- Pharma-specific signal categories
- Lightweight models (BART summarizer, spaCy NER, simple scoring — no RoBERTa needed)

---

### **Repo 5: ClinicalTrials.gov Intelligence Dashboard (GitHub Topics)**
**Stack:** Python + OpenAI + Streamlit  
**Source:** Found in github.com/topics/clinicaltrials-gov  
**What it does:** Real-time clinical trial intelligence dashboard using ClinicalTrials.gov API

**What it does well:**
```
✓ Surfaces competitive trial landscape for any indication
✓ Enrollment signals and protocol patterns
✓ LLM-generated summaries of trial changes
✓ Governance layer for clinical teams
✓ Real-world evidence integration
```

**Gaps:**

| Gap | Why It Matters |
|---|---|
| **Single-source only** | Only ClinicalTrials.gov. No news, no social, no regulatory. Misses 80% of signal types. |
| **Streamlit UI** | Not production-grade for multi-role deployment. |
| **No velocity detection** | Shows trial status but not *acceleration* of enrollment/activity. |
| **No cross-signal confluence** | Doesn't connect: "Roche emicizumab head-to-head + FDA advisory + patient forum spike = high alert." |

**What we borrow:**
- ClinicalTrials.gov API as our 6th data source (add in Week 4)
- Trial landscape visualization (add competitive pipeline chart alongside trend chart)

**What we do better:**
- Cross-source signal confluence (ClinicalTrials + News + Social = multiplied alert)
- Haemophilia rare disease specific taxonomy
- Multi-role operational dashboard

---

## **GAP SUMMARY TABLE: Open Source vs MetaRadar**

| Feature | brightdata/CI | Market-Intel-Agent | OpenHawk | news-signals | ClinicalTrials Dash | **MetaRadar** |
|---|---|---|---|---|---|---|
| Real-time dashboard | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Multi-source ingestion | ✓ (scraping) | ✓ (3 sources) | ✓ (papers/OSS) | ❌ | ❌ (1 source) | ✅ (6 sources) |
| Pharma/haemophilia domain | ❌ | ❌ | ❌ | ❌ | Partial | ✅ |
| Velocity/trend detection | ❌ | ❌ | ❌ | ✓ (academic) | ❌ | ✅ |
| Role-based access | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Signal deduplication | ❌ | ❌ | ✓ | ✓ | ❌ | ✅ |
| Persistent storage | ❌ | ❌ | ✓ (SQLite) | ❌ | ❌ | ✅ (Postgres + Redis) |
| Cross-signal confluence | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Free API stack | ❌ | ❌ | ✓ | ✓ | ✓ | ✅ |
| Multi-user support | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Entity ontology/taxonomy | ❌ | ❌ | ❌ | ❌ | Partial | ✅ |
| Conversational query | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (Ask Athena) |

**Conclusion: No existing open-source tool addresses the haemophilia rare disease pharma CI use case with real-time monitoring, multi-role access, Four-Question framing, and cross-signal confluence. MetaRadar is not a marginal improvement—it's a category that doesn't exist in open source yet.**

---

## **PART 2: WHAT MAKES THE CURRENT PLAN "BASIC" & HOW TO ELEVATE IT**

### **Problem Areas in Current Plan**

**1. Plain Pipeline Thinking**
The current plan describes: Fetch → Extract → Score → Display.
This is a data pipeline, not an intelligence platform.
Real competitive intelligence requires *reasoning*, not just retrieval.

**2. No Signal Relationship Model**
Currently, 800 signals float independently. There's no concept of:
- "These 4 signals are all about the same competitor move"
- "This ASH abstract + this press release + this patient forum spike = one emerging story"
- "Roche's emicizumab head-to-head data will affect mim8's positioning"

**3. No Competitive Narrative Synthesis**
Current plan delivers raw signals with summaries. It doesn't answer:
- "What is happening with mim8 this month?"
- "What changed in the haemophilia treatment landscape this week?"
- "Should Novo Nordisk be worried about Hemgenix 3-year durability data vs prophylaxis?"

**4. Scoring is Static**
Current scoring: `source_credibility * 0.7 + keyword_match * 0.3`
This is a fixed formula. No learning, no context, no adaptation.

**5. No Stakeholder Feedback Loop (HITL)**
No mechanism for Novo Nordisk functions to tell the system whether routing was right. A Regulatory Affairs analyst who constantly gets clinical-only signals has no way to fix it. Routing never improves → trust decays → analysts revert to manual inbox scanning.

**6. No Traceable Reasoning**
Current plan: Signal appears with a score. User doesn't know *why* it's important.
Regulatory teams especially need: "This FDA guideline change matters because it affects X, Y, Z."

**7. No Signal Lifecycle View**
Signals are isolated readouts. No one can answer "where is mim8 in its lifecycle, and what is the expected next event?" Each readout, submission, and label update floats separately.

**8. No Contradiction / Red-Team Check**
The system repeats claims as facts. A congress abstract reporting durable efficacy and a real-world cohort reporting waning effect both appear as equal-weight signals — no mechanism flags that they contradict each other, so an analyst can quote a now-disputed result.

**9. No Missing-Signal Detection**
The system only reacts to what appears. It never flags what *should* have appeared: a Phase 3 readout promised for Q1 with 3 months of silence is invisible — yet that silence is exactly the early-warning a Medical Affairs or Regulatory team needs.

---

## **PART 3: THE REFINED ARCHITECTURE**

### **Core Concept Upgrade: From "Signal Feed" to "Intelligence Layer"**

```
OLD MENTAL MODEL:
  News Article → NLP → Score → Dashboard
  (Raw information with a number attached)

NEW MENTAL MODEL:
  Multi-source signals
         ↓
  Entity Relationship Graph
  (Hemlibra → emicizumab → bispecific antibody → Roche → Haemophilia A competitor)
         ↓
  THE FIVE ADVANCED ANALYSES
  1. Signal Confluence Engine
     (When ASH abstract + CSL press release + r/Hemophilia fire on same entity = converging story)
  2. Signal Lifecycle Tracker
     (Where is this development? announced → in_trial → results_in → under_review → ... what is NEXT?)
  3. Red-Team Contradiction Engine
     (Does a newer signal CONTRADICT an older claim? Both evidence chains shown, human review required)
  4. Missing-Signal Detector
     (What SHOULD have happened but didn't? Silence = stalled submission / missed endpoint)
  5. Stakeholder Learning Loop (HITL)
     (Persona feedback recalibrates role-scoring weights → routing confidence improves)
         ↓
  Narrative Synthesis Agent
  ("Hemgenix 3-year durability strengthening: 3 convergent signals in 48h, one contradiction flagged")
         ↓
  Function-Specific Intelligence Brief
  (Medical Affairs: clinical · Regulatory: labeling · Safety/PV: watch ·
   Market Access: HTA · Medical Communications: FAQ · Leadership: escalation)
         ↓
  Stakeholder Calibration Agent (HITL)
  (Persona feedback recalibrates role-scoring weights → routing confidence improves)
```

---

### **Upgrade 1: Multi-Agent Orchestration (Replace Simple Pipeline)**

Replace the monolithic pipeline with specialized autonomous agents coordinated by LangGraph.

```python
# Before (Basic pipeline):
async def process():
    raw = await fetch()
    entities = await extract(raw)
    scored = await score(entities)
    return scored

# After (Multi-agent with LangGraph):
from langgraph.graph import StateGraph

class IntelligenceState(TypedDict):
    raw_signals: list[dict]
    validated_signals: list[dict]
    extracted_entities: list[dict]
    scored_signals: list[dict]
    confluent_stories: list[dict]
    lifecycle_chains: list[dict]          # Analysis 2
    contradictions: list[dict]            # Analysis 3
    missing_signal_alerts: list[dict]     # Analysis 4
    role_briefs: dict[str, list]
    calibration_weights: dict[str, float]   # Analysis 5 (HITL)

# Define agents
def ingestion_agent(state: IntelligenceState):
    """Fetches from 6 APIs in parallel, deduplicates"""
    signals = asyncio.gather(
        newsapi_fetcher.run(),
        pubmed_fetcher.run(),
        clinicaltrials_fetcher.run(),
        reddit_fetcher.run(),
        fda_fetcher.run(),
        congress_fetcher.run()          # ASH / ISTH / WFH / EHA abstracts
    )
    return {"raw_signals": signals}

def validation_agent(state: IntelligenceState):
    """Quality scoring, dedup, language detection"""
    validated = [sig for sig in state['raw_signals'] 
                 if quality_score(sig) > 0.5]
    return {"validated_signals": validated}

def nlp_agent(state: IntelligenceState):
    """spaCy NER + BART summarization (batch)"""
    ...

def confluence_agent(state: IntelligenceState):
    """Detects when multiple signal types converge on same entity (Analysis 1)"""
    ...

def lifecycle_agent(state: IntelligenceState):        # NEW v2.1
    """Assigns signals to lifecycle chains + advances state machine (Analysis 2)"""
    ...

def red_team_agent(state: IntelligenceState):         # NEW v2.1
    """NLI entailment contradiction scan + devil's-advocate review (Analysis 3)"""
    ...

def missing_signal_agent(state: IntelligenceState):   # NEW v2.1
    """Expected-event detector; silence = early-warning (Analysis 4)"""
    ...

def synthesis_agent(state: IntelligenceState):
    """Generates intelligence narratives (the key differentiator)"""
    ...

def brief_agent(state: IntelligenceState):
    """Formats role-specific dashboard content (Four-Question)"""
    ...

def calibration_agent(state: IntelligenceState):
    """HITL: applies stakeholder_feedback → recalibrates role weights (Analysis 5)"""
    ...

# Wire agents into graph
graph = StateGraph(IntelligenceState)
graph.add_node("ingest", ingestion_agent)
graph.add_node("validate", validation_agent)
graph.add_node("nlp", nlp_agent)
graph.add_node("confluence", confluence_agent)
graph.add_node("lifecycle", lifecycle_agent)          # NEW v2.1
graph.add_node("red_team", red_team_agent)            # NEW v2.1
graph.add_node("missing_signal", missing_signal_agent)  # NEW v2.1
graph.add_node("synthesize", synthesis_agent)
graph.add_node("brief", brief_agent)
graph.add_node("calibrate", calibration_agent)

graph.add_edge("ingest", "validate")
graph.add_edge("validate", "nlp")
graph.add_edge("nlp", "confluence")
graph.add_edge("confluence", "lifecycle")
graph.add_edge("lifecycle", "red_team")
graph.add_edge("red_team", "missing_signal")
graph.add_edge("missing_signal", "synthesize")
graph.add_edge("synthesize", "brief")
graph.add_edge("brief", "calibrate")

graph.set_entry_point("ingest")
runner = graph.compile()

# Run
result = runner.invoke({})
```

**Why LangGraph over raw Python:** State management across agents is built-in. If the synthesis agent needs context from NLP agent, it's in the state dict. No global variables, no passing arguments everywhere.

---

### **Upgrade 2: Entity Relationship Graph (Pharma Ontology)**

Instead of treating signals as independent text blobs, build a lightweight graph of pharmaceutical entity relationships.

```python
# entities/pharma_ontology.py

PHARMA_ONTOLOGY = {
    "drugs": {
        "emicizumab": {
            "brand_names": ["Hemlibra"],
            "mechanism": "Bispecific antibody (Factor IXa/X bridge)",
            "manufacturer": "Roche/Genentech",
            "indications": ["haemophilia_a", "haemophilia_a_with_inhibitors"],
            "formulations": ["subcutaneous injection"],
            "competitors": ["concizumab", "fitusiran", "mim8"]
        },
        "concizumab": {
            "brand_names": ["Alhemo"],
            "mechanism": "Anti-TFPI monoclonal antibody",
            "manufacturer": "Novo Nordisk",
            "indications": ["haemophilia_a", "haemophilia_b", "with/without inhibitors"],
            "formulations": ["subcutaneous injection"],
            "competitors": ["emicizumab", "fitusiran", "marstacimab"]
        },
        "mim8": {
            "brand_names": ["Investigational"],
            "mechanism": "Next-generation bispecific antibody",
            "manufacturer": "Novo Nordisk",
            "indications": ["haemophilia_a", "haemophilia_b"],
            "formulations": ["subcutaneous injection"],
            "competitors": ["emicizumab"],
            "status": "Phase 3"
        },
        "etranacogene_dezaparvovec": {
            "brand_names": ["Hemgenix"],
            "mechanism": "AAV5-based gene therapy (Factor IX)",
            "manufacturer": "CSL Behring/UniQure",
            "indications": ["haemophilia_b"],
            "formulations": ["single IV infusion"],
            "competitors": ["valoctocogene_roxaparvovec"],
            "status": "FDA approved November 2022"
        },
        "valoctocogene_roxaparvovec": {
            "brand_names": ["Roctavian"],
            "mechanism": "AAV5-based gene therapy (Factor VIII)",
            "manufacturer": "BioMarin",
            "indications": ["haemophilia_a_without_inhibitors"],
            "formulations": ["single IV infusion"],
            "competitors": ["emicizumab", "mim8"],
            "status": "FDA approved June 2023"
        },
    },
    "companies": {
        "Novo Nordisk Rare Disease": {
            "portfolio": ["concizumab", "mim8", "esparin_egidiama"],
            "pipeline_focus": ["haemophilia_a", "haemophilia_b", "rare bleeding disorders"],
            "key_competitors": ["Roche", "Sanofi", "Pfizer", "BioMarin", "CSL Behring", "Takeda"],
        },
    },
    "indications": {
        "haemophilia_a": {
            "description": "Factor VIII deficiency (~200,000 patients globally)",
            "treatment_paradigm": "Factor replacement → EHL factors → bispecific (emicizumab/mim8) → gene therapy (Roctavian)",
            "key_complication": "Inhibitor development in ~30% of severe cases",
        },
        "haemophilia_b": {
            "description": "Factor IX deficiency (Christmas disease, ~50,000 patients)",
            "treatment_paradigm": "Factor replacement → EHL factors → gene therapy (Hemgenix)",
        }
    }
}

# Usage: enrich extracted entities with ontology context
def enrich_signal(signal: dict, entities: dict) -> dict:
    for drug in entities.get("drugs", []):
        if drug in PHARMA_ONTOLOGY["drugs"]:
            signal["context"]["drug_class"] = PHARMA_ONTOLOGY["drugs"][drug]["mechanism"]
            signal["context"]["competitors"] = PHARMA_ONTOLOGY["drugs"][drug]["competitors"]
            signal["context"]["manufacturer"] = PHARMA_ONTOLOGY["drugs"][drug]["manufacturer"]
    return signal
```

**Why this matters:**
- When "Hemlibra" appears in a Reddit post, the system knows it's emicizumab + Roche + Novo competitor
- When "mim8" or "concizumab" appears, system flags it as a Novo Nordisk own-asset signal (own-pipeline awareness)
- When "Hemgenix" appears, system knows it's a gene-therapy competitive threat to prophylaxis
- Zero additional API calls. Just a local dictionary lookup.
- B.Pharm team owns and maintains this ontology (their biggest contribution)

---

### **Upgrade 3: Signal Confluence Engine (The Core Differentiator)**

This is what no existing open-source tool does. When multiple independent sources fire on the same entity within a time window, the importance multiplies.

```python
# services/confluence_engine.py

class SignalConfluenceEngine:
    """
    Detects when multiple independent signal types
    converge on the same pharmaceutical entity.
    
    Example:
      - ASH 2026: Hemgenix 3-year durability abstract (congress signal)
      - CSL Behring: press release on 3-yr Factor IX data (competitive signal)
      - Reddit: r/Hemophilia patient discussion (patient/social signal)
      
    Confluence: All 3 fire on Hemgenix in 48 hours
    = Single high-priority "GENE THERAPY MILESTONE" alert
    """
    
    SIGNAL_TYPES = ["gene_therapy", "non_factor", "regulatory",
                    "congress", "patient_access", "pipeline", "inhibitor"]
    
    CONFLUENCE_MATRIX = {
        # If these signal types converge = this alert level
        frozenset(["regulatory", "clinical", "social"]): "CRITICAL",
        frozenset(["clinical", "competitive"]): "HIGH",
        frozenset(["regulatory", "competitive"]): "HIGH",
        frozenset(["social", "clinical"]): "MEDIUM",
        frozenset(["competitive"]): "LOW",
    }
    
    def detect_confluence(
        self,
        signals: list[dict],
        entity: str,
        time_window_hours: int = 48
    ) -> dict:
        """
        Find all signals about `entity` in last `time_window_hours`.
        If signal types from multiple categories appear = confluence event.
        """
        
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        
        # Filter signals for this entity in time window
        entity_signals = [
            sig for sig in signals
            if entity in sig.get("entities", {}).get("all", [])
            and sig["timestamp"] > cutoff
        ]
        
        if len(entity_signals) < 2:
            return None  # Not enough for confluence
        
        # Identify which signal types are present
        signal_types_present = set(sig["signal_type"] for sig in entity_signals)
        
        # Check confluence matrix
        best_match = None
        for pattern, alert_level in self.CONFLUENCE_MATRIX.items():
            if pattern.issubset(signal_types_present):
                best_match = (pattern, alert_level)
                break
        
        if not best_match:
            return None
        
        return {
            "entity": entity,
            "alert_level": best_match[1],
            "signal_count": len(entity_signals),
            "signal_types_present": list(signal_types_present),
            "time_window_hours": time_window_hours,
            "constituent_signals": entity_signals,
            "story_summary": await self._synthesize_story(entity_signals),
        }
    
    async def _synthesize_story(self, signals: list[dict]) -> str:
        """
        Uses local BART model to synthesize a narrative from 
        multiple converging signals.
        
        Input:  3 separate signal summaries about Hemgenix durability
        Output: "Gene-therapy durability signals converging: ASH 3-yr data,
                 CSL press release, patient forum discussion."
        """
        combined = " ".join([sig["summary"] for sig in signals])
        
        summary = self.summarizer(
            f"Synthesize these related pharmaceutical signals into one executive sentence: {combined}",
            max_length=60,
            min_length=20,
        )
        return summary[0]["summary_text"]
```

**Demo Power:** Instead of showing 800 signals, MetaRadar shows:
```
🔴 CRITICAL - Hemgenix 3-year Durability Confluence (3 signals, 48h)
   "ASH abstract + CSL press release + patient forum discussion.
    Gene-therapy durability narrative strengthening."
   
   Sources: ASH 2026 | CSL Behring | Reddit r/Hemophilia
   Recommended action: Medical Affairs review within 24h
```

---

### **Upgrade 4: Temporal Pattern Recognition (Predictive Layer)**

Rather than just showing what's happening, detect *which stage* a competitive development is in.

```python
# services/temporal_patterns.py

COMPETITIVE_TIMELINE_PATTERNS = {
    "gene_therapy_milestone_parade": {
        "description": "Signal pattern preceding a gene-therapy durability/approval milestone",
        "stages": [
            {"stage": "Phase 3 gene-therapy data published", "weeks_before_milestone": "12-24"},
            {"stage": "Congress abstract accepted (ASH/ISTH/WFH)", "weeks_before_milestone": "4-8"},
            {"stage": "Company press release + investor call", "weeks_before_milestone": "2-4"},
            {"stage": "Patient forum activity spike", "weeks_before_milestone": "0-2"},
        ],
        "alert_message": "Gene-therapy milestone following converging signal trajectory"
    },
    "competitive_regulatory_filing": {
        "description": "Signal pattern preceding a competitor regulatory submission",
        "stages": [
            {"stage": "Phase 3 endpoint met (press release)", "weeks_before_filing": "8-16"},
            {"stage": "HTA/EMA/FDA meetings announced", "weeks_before_filing": "4-8"},
            {"stage": "Congress data + analyst commentary", "weeks_before_filing": "2-4"},
            {"stage": "Submission announced", "weeks_before_filing": "0-2"},
        ],
        "alert_message": "Competitor regulatory filing trajectory detected"
    },
    "inhibitor_safety_wave": {
        "description": "Signal pattern preceding a safety concern on inhibitor/thrombosis",
        "stages": [
            {"stage": "Case reports in literature", "weeks_before": "4-8"},
            {"stage": "Patient/HCP forum reports", "weeks_before": "2-4"},
            {"stage": "Regulator safety communication", "weeks_before": "0-2"},
        ],
        "alert_message": "Inhibitor/safety pattern detected"
    }
}

def match_signal_to_pattern(recent_signals: list[dict], entity: str) -> dict:
    """
    Checks if current signal pattern for `entity`
    matches any known historical patterns.
    Returns: pattern name + current stage + predicted next stage
    """
    
    current_signal_types = set(
        sig["signal_type"] for sig in recent_signals
        if entity in str(sig.get("entities", {}))
    )
    
    for pattern_name, pattern in COMPETITIVE_TIMELINE_PATTERNS.items():
        # Simplified: check if key stage signals are present
        if "gene_therapy" in current_signal_types and "congress" in current_signal_types:
            return {
                "pattern": pattern_name,
                "current_stage": pattern["stages"][1],
                "next_predicted_stage": pattern["stages"][2],
                "confidence": 0.72,
                "alert": pattern["alert_message"],
                "entity": entity
            }
    
    return None
```

**B.Pharm contribution:** They define which signal patterns matter clinically.
They know: "Phase 3 gene-therapy result + ASH abstract = next congress cycle is the durability moment."
This is domain knowledge that can't come from a CS team alone.

---

### **Upgrade 5: Traceable Reasoning (Explainable Intelligence)**

Every intelligence output must be fully traceable: which source → which signal → why it matters.

```python
class TraceableInsight:
    """
    Every insight in MetaRadar has a complete audit trail.
    Required for pharma regulatory-grade intelligence.
    """
    
    def __init__(self):
        self.evidence_chain = []
    
    def add_source(self, signal: dict):
        self.evidence_chain.append({
            "signal_id": signal["id"],
            "source": signal["source"],           # "Reuters"
            "original_url": signal["url"],         # "https://reuters.com/..."
            "published_at": signal["timestamp"],   # "2026-07-25T14:30:00Z"
            "original_text_snippet": signal["text"][:200],
            "extracted_entity": signal["entities"],
        })
    
    def generate_traceable_insight(self) -> dict:
        insight_text = synthesize_from_evidence(self.evidence_chain)
        
        return {
            "insight": insight_text,
            "confidence_score": calculate_confidence(self.evidence_chain),
            "source_count": len(self.evidence_chain),
            "sources": [
                {
                    "name": e["source"],
                    "url": e["original_url"],
                    "excerpt": e["original_text_snippet"]
                }
                for e in self.evidence_chain
            ],
            "reasoning": f"Insight derived from {len(self.evidence_chain)} independent sources "
                        f"across {len(set(e['source'] for e in self.evidence_chain))} platforms. "
                        f"Confidence {calculate_confidence(self.evidence_chain):.0%}."
        }
```

**Dashboard Display:**
```
Insight:
"Hemgenix gene-therapy durability narrative strengthening—3 independent signals this week"

Sources (click to verify):
  [1] ASH 2026 Dec → "Hemgenix 3-yr Factor IX durability"
  [2] CSL Behring Dec → "3-year durability results announced"
  [3] Reddit r/Hemophilia Dec → "patient discussion on gene therapy durability"

Reasoning: Derived from 3 independent sources across 3 platforms. Confidence: 84%.
```

---

### **Upgrade 6: Competitive Narrative Synthesis (LLM Layer)**

The final layer: Take all signals about a competitor/topic and synthesize them into a 3-sentence executive brief. Every brief is labeled **FACT / INTERPRETATION / SPECULATION**; when evidence is insufficient the system returns *"Insufficient evidence to support an interpretation."*

```python
# services/narrative_synthesizer.py

SYNTHESIS_PROMPTS = {
    "weekly_competitive_brief": """
You are a senior pharmaceutical competitive intelligence analyst.
Given the following signals from the past 7 days about {entity}:

{signals_json}

Write a 3-sentence executive brief that:
1. States what happened (factual, cite source counts)
2. Explains why it matters for a haemophilia treatment landscape leader
3. Suggests one concrete action for the relevant team

Format:
WHAT HAPPENED: ...
WHY IT MATTERS: ...
RECOMMENDED ACTION: ...

Be specific, not generic. Do not speculate beyond the evidence.
""",

    "confluence_alert": """
You are a pharmaceutical intelligence analyst.
The following signals are converging on the same topic in 48 hours:

{signals_json}

Write a 2-sentence alert that:
1. Names what is converging (entity + pattern)
2. States the business implication

Keep it under 50 words. Medical Affairs audience.
"""
}

async def synthesize_narrative(entity: str, signals: list[dict], prompt_type: str) -> str:
    """
    Uses local BART model (or optional GPT-4 call) to synthesize
    a role-specific intelligence narrative.
    """
    
    prompt = SYNTHESIS_PROMPTS[prompt_type].format(
        entity=entity,
        signals_json=json.dumps([
            {
                "source": s["source"],
                "summary": s["summary"],
                "type": s["signal_type"],
                "date": s["timestamp"]
            }
            for s in signals
        ], indent=2)
    )
    
    # Use local model (free, no API)
    result = narrative_model(prompt, max_length=150, min_length=50)
    return result[0]["generated_text"]
```

---

### **Upgrade 7: Query Interface ("Ask Athena" Lite)**

Instead of just browsing a dashboard, let users ask questions in natural language.

```python
# services/query_engine.py
# ⚠️ NOTE: The earlier version of this file used WeaviateClient.
# Weaviate has been REPLACED by pgvector (PostgreSQL extension).
# This implementation uses pgvector for semantic search + pg_trgm for keyword search.
# See: Architecture decision in PART 4 — "Replace Weaviate with pgvector"

import asyncpg
from sentence_transformers import SentenceTransformer
import os

_embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

class AthenaQueryEngine:
    """
    Natural language query interface over signal database.
    Uses RAG: Retrieve relevant signals (pgvector hybrid search) → Generate answer
    """

    def __init__(self, db_pool: asyncpg.Pool, llm_pipeline):
        self.db = db_pool
        self.llm = llm_pipeline  # model-agnostic: loaded from LOCAL_LLM_MODEL env var

    async def query(self, question: str, role: str) -> dict:
        """
        Question: "What is the latest on mim8?"
        Role: "medical_affairs"
        """

        # Step 1: Embed the question (local model, no API call)
        q_embedding = _embedder.encode(question).tolist()

        # Step 2: Hybrid search — pgvector (semantic) + pg_trgm (keyword)
        # alpha=0.6 semantic + 0.4 keyword (same weighting as before)
        relevant_signals = await self.db.fetch("""
            WITH semantic AS (
                SELECT id, title, summary, source, published_at,
                       (embedding <=> $1::vector) AS semantic_dist,
                       (role_relevance->>$2)::FLOAT AS role_score
                FROM signals
                WHERE status = 'active'
                  AND (role_relevance->>$2)::FLOAT > 0.5
                ORDER BY embedding <=> $1::vector
                LIMIT 10
            ),
            keyword AS (
                SELECT id, title, summary, source, published_at,
                       similarity(title || ' ' || summary, $3) AS kw_score,
                       (role_relevance->>$2)::FLOAT AS role_score
                FROM signals
                WHERE status = 'active'
                  AND (title || ' ' || summary) %% $3
                  AND (role_relevance->>$2)::FLOAT > 0.5
                ORDER BY kw_score DESC
                LIMIT 10
            )
            SELECT DISTINCT ON (s.id)
                s.id, s.title, s.summary, s.source, s.published_at
            FROM signals s
            WHERE s.id IN (SELECT id FROM semantic UNION SELECT id FROM keyword)
            ORDER BY s.id, s.published_at DESC
            LIMIT 5
        """, q_embedding, role, question)

        # Step 3: Hallucination guard — if no signals, refuse gracefully
        if not relevant_signals:
            return {
                "question": question,
                "answer": "Insufficient signals in last 7 days to answer this question.",
                "supporting_signals": [],
                "signal_count_used": 0,
                "confidence": 0.0
            }

        # Step 4: Generate answer grounded in retrieved signals (model-agnostic)
        context = "\n".join([s["summary"] for s in relevant_signals if s["summary"]])
        answer_prompt = (
            f"Based only on these recent signals:\n{context}\n\n"
            f"Answer this question for a {role} professional: {question}\n\n"
            "If the signals don't contain enough information, say "
            "'Insufficient signals in last 7 days.' Be factual and cite signals."
        )

        # LOCAL_LLM_MODEL env var controls which model runs here
        # Default: facebook/bart-large-cnn | Alternatives: Gemma, Mistral, Phi-3, etc.
        result = self.llm(answer_prompt, max_length=200, truncation=True)
        answer_text = result[0].get("generated_text") or result[0].get("summary_text", "")

        return {
            "question": question,
            "answer": answer_text,
            "supporting_signals": [dict(s) for s in relevant_signals[:3]],
            "signal_count_used": len(relevant_signals),
            "confidence": calculate_retrieval_confidence(relevant_signals)
        }
```


---

### **Upgrade 8: Signal Lifecycle Tracker (Analysis 2 of the Five) — NEW v2.1**

Signals are stitched into chronological state machines per development, so an analyst always knows where a development is and what happens next.

```python
# services/lifecycle_tracker.py
LIFECYCLE_STATES = [
    "announced", "in_trial", "interim_result", "final_result",
    "congress_publication", "regulatory_development", "approved",
    "post_market", "discontinued",
]

class SignalLifecycleTracker:
    """Stitch isolated signals into one timeline per development.

    Example (mim8):
      2024-05 announced → Phase 3 initiation
      2026-01 results_in → Phase 3 primary endpoint met
      2026-03 under_review → FDA/EMA submission expected
      NEXT EXPECTED: submission announced
    """

    def advance(self, signal, entity) -> dict:
        chain = self.get_or_create_chain(entity)     # entity + modality + indication
        # Every event records event_type · event_date · development_id · source_id
        chain.events.append({
            **signal,
            "event_type": signal["signal_type"],   # congress_abstract | oral_presentation |
                                                    # poster | publication | regulatory_development ...
            "event_date": signal.get("event_date") or signal["published_at"],
            "development_id": chain.id,
            "source_id": signal["source_id"],
        })
        chain.current_state = self._infer_state(signal)   # B.Pharm-validated rules
        chain.expected_next = self._expected_next(chain)
        # NEW DEVELOPMENT vs NEW EVIDENCE ABOUT EXISTING DEVELOPMENT:
        # a matching development_id means the congress/publication signal APPENDS to
        # this chain (one development), never spawning an unrelated intelligence card.
        return {"chain": chain, "state": chain.current_state,
                "expected_next": chain.expected_next,
                "link_decision": "new_evidence_existing_development"
                                if chain.events else "new_development"}

    def timeline(self, entity) -> list[dict]:
        """Chronological, temporally-linked events for the entity."""
        return sorted(self.chains[entity].events, key=lambda e: e["event_date"])
```

**Why this matters:** "Results are in" is only useful if you also know "submission is expected next" and can detect when that next step silently doesn't arrive. A trial → congress abstract → oral presentation → poster → publication chain (e.g., FRONTIER4/denecimig at ISTH 2026) stays ONE development because every event carries `development_id`.

---

### **Upgrade 9: Red-Team Contradiction Engine (Analysis 3 of the Five) — NEW v2.1**

A devil's-advocate layer that flags when a newer signal contradicts an older claim about the same entity. Uses the *same* local zero-shot NLI model (`facebook/bart-large-mnli`) already used for signal classification — zero extra model download, still free and local.

```python
# services/red_team_engine.py
from transformers import pipeline
from itertools import combinations

_nli = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

async def detect_contradictions(signals, entity, window_days=90) -> list[dict]:
    entity_signals = [s for s in signals if entity in s.get("entities", {}).get("all", [])]
    out = []
    for a, b in combinations(entity_signals, 2):
        if (b["published_at"] - a["published_at"]).days > window_days:
            continue
        result = _nli(a["summary"], candidate_labels=["entailment", "contradiction", "neutral"])
        if result["labels"][0] == "contradiction" and result["scores"][0] > 0.6:
            out.append({
                "entity": entity,
                "claim_a": {"text": a["summary"], "source": a["source"], "url": a["url"], "date": a["published_at"]},
                "claim_b": {"text": b["summary"], "source": b["source"], "url": b["url"], "date": b["published_at"]},
                "contradiction_score": result["scores"][0],
                "red_team_note": "Devil's-advocate: newest evidence may overturn earlier claim — human review required",
            })
    return out
```

**Red-team review prompt (narrative layer):**
```
"You are a red-team reviewer for a pharma CI team. Given the evidence for {entity},
list every point where the evidence could be misleading, incomplete, or contested.
Flag any source whose claim is not corroborated by a second independent source."
```

**Demo:** MetaRadar surfaces `⚔ CONTRADICTION — "sustained efficacy" (ASH) vs "waning effect" (real-world cohort)` with both evidence chains shown and a red-team note requiring human review.

---

### **Upgrade 10: Missing-Signal Detector (Analysis 4 of the Five) — NEW v2.1**

Absence of a signal is itself a signal. Event-progression state machines flag expected-but-absent milestones with confidence that grows with silence.

```python
# services/missing_signal_detector.py
MISSING_SIGNAL_RULES = {
    "gene_therapy_durability": {
        "expected_sequence": [
            {"event": "Phase 3 primary endpoint met", "max_lag_days": 120},
            {"event": "FDA/EMA submission announced", "max_lag_days": 270},
            {"event": "PDUFA/CHMP decision", "max_lag_days": 180},
        ],
        "alert": "gene-therapy approval trajectory has stalled — expected next event overdue",
    },
    "phase3_readout_followup": {
        "expected_sequence": [
            {"event": "Phase 3 readout published", "max_lag_days": 0},
            {"event": "regulatory submission announced", "max_lag_days": 180},
            {"event": "congress data presentation", "max_lag_days": 365},
        ],
        "alert": "readout published but no submission/congress follow-up in expected window",
    },
}

async def detect_missing_signals(lifecycles: list[dict]) -> list[dict]:
    for lc in lifecycles:
        rule = MISSING_SIGNAL_RULES.get(lc["pattern"])
        expected = rule["expected_sequence"][lc["stage_index"]]
        days = (now - lc["last_event_date"]).days
        if days > expected["max_lag_days"]:
            yield {
                "entity": lc["entity"],
                "missing_event": expected["event"],
                "days_since_last_signal": days,
                "max_lag_days": expected["max_lag_days"],
                "confidence": min(0.95, 0.4 + days * 0.02),   # confidence-by-silence
                "alert": rule["alert"],
            }
```

**Guardrail:** Missing-signal alerts only fire after the configured `max_lag_days` window, and confidence grows with silence — the false-positive discipline that judges score on Feasibility.

**Demo:** `🕳 WATCH — mim8 submission announced expected 90d ago (last signal: Jan 2026)` — MetaRadar flags the silence as a monitoring signal (a WATCH item, not a claim that the event will happen); human review required.

**Watch-for-Next (stakeholder-defined watch rules, v3.1):** a stakeholder can request *"monitor this competitor Phase III programme for subsequent congress disclosures."* The detector stores a WATCH RULE — `source_event → expected_event_type (e.g., congress_disclosure) → monitoring_window_days → responsible_function → status` — with statuses `watching / new_evidence_detected / no_new_evidence / watch_expired / human_review_required`. When a matching congress signal is ingested, it links into the existing development (confluence/lifecycle), the watch flips to `new_evidence_detected`, and the responsible functions are notified. If nothing appears in the window: *"No subsequent congress evidence observed during the configured monitoring window."* — absence is NEVER presented as proof that no activity occurred; wording is limited to "Watch for… / Expected/possible next evidence / Not observed yet". This extends the existing missing-signal mechanism (no separate watch engine).

```python
# services/watch_service.py (extends missing_signal_detector.py)
WATCH_STATUSES = ["watching", "new_evidence_detected", "no_new_evidence",
                  "watch_expired", "human_review_required"]

async def create_watch_rule(source_event_id, expected_event_type,
                            monitoring_window_days, responsible_function) -> dict:
    # e.g. source_event_id=competitor Phase III update, expected_event_type=congress_disclosure
    return {"status": "watching",
            "message": "Watch for upcoming congress disclosures · "
                       "Expected/possible next evidence · Not observed yet"}

async def on_new_signal(signal):
    for watch in active_watches(expected_event_type=signal["signal_type"]):
        if signal["development_id"] == watch.source_event.development_id:
            watch.status = "new_evidence_detected"      # linked into same development
            notify(watch.responsible_function)          # Medical Affairs + Medical Communications
```


---

## **PART 4: REFINED TECH STACK (FINAL VERSION)**

```
AGENT ORCHESTRATION:
├─ LangGraph (state-machine-style multi-agent coordination)
│  └─ Replaces raw Python functions
│  └─ Each agent = one node in graph
│  └─ State flows between agents automatically

BACKEND:
├─ FastAPI + Python 3.11 (async-first)
├─ Celery + Redis (background agent tasks)
└─ APScheduler (every 2 hours fetch trigger)

NLP / AI:
├─ spaCy 3.7 en_core_sci_md (pharma NER, free, local)
├─ medspacy (optional: extends spaCy for clinical text; recommended by research report Section 2)
├─ LLM/Summarization: ANY HuggingFace-compatible model via LOCAL_LLM_MODEL env var
│   Default: facebook/bart-large-cnn (CPU-fast, seq2seq, hackathon default)
│   Swap-in examples (zero code change, config only):
│   ├─ google/gemma-2b              (better quality, ~2GB VRAM or slow CPU)
│   ├─ mistralai/Mistral-7B-Instruct (near-GPT4 quality, 4-bit quant for CPU)
│   ├─ microsoft/phi-3-mini-4k-instruct (3.8B, best quality/size ratio)
│   └─ TinyLlama/TinyLlama-1.1B-Chat (ultra-light, minimal hardware)
├─ sentence-transformers/all-MiniLM-L6-v2 (embeddings, local, 80MB)
│   ↑ Replace Weaviate's built-in vectorizer — faster, smaller
├─ Zero-shot classifier: facebook/bart-large-mnli (signal classification + RED-TEAM contradiction entailment)
└─ HTTP resilience: tenacity + httpx.AsyncClient (exponential backoff; research report Section 2)

DATA:
├─ PostgreSQL 16 + pgvector (primary + vector in one DB)
│   ↑ Replace Weaviate entirely — eliminates one Docker container
│   ├─ pgvector: 384-dim vectors, native hybrid search in PostgreSQL
│   ├─ raw_signals_bronze: raw API JSON, pre-processing (replay layer)
│   ├─ audit_log: WORM append-only compliance table (21 CFR Part 11)
│   ├─ stakeholder_feedback: append-only routing ratings (Analysis 5, HITL)
│   ├─ scoring_weights + calibration_history: calibrated role weights (HITL)
│   ├─ lifecycle_chains + lifecycle_events: state machines + event links (Analysis 2)
│   ├─ contradictions: NLI-flagged claim pairs (Analysis 3)
│   ├─ missing_signal_rules + missing_signal_alerts: expected-event detectors (Analysis 4)
│   └─ confluence_events: cross-source alerts (Analysis 1)
├─ Redis 7 (cache + rate limiting + session)
└─ Pharma Ontology JSON (local, no DB, instant lookup) — haemophilia ontology

THE FIVE ADVANCED ANALYSES (v2.1):
├─ 1. Confluence Engine      → confluence_engine.py + confluence_agent.py
├─ 2. Lifecycle Tracker      → lifecycle_tracker.py + lifecycle_agent.py
├─ 3. Red-Team Engine        → red_team_engine.py + red_team_agent.py (bart-large-mnli NLI)
├─ 4. Missing-Signal Detector→ missing_signal_detector.py + missing_signal_agent.py
└─ 5. Stakeholder Learning   → calibration_service.py + calibration_agent.py (HITL)

CALIBRATION (Analysis 5, HITL):
├─ StakeholderCalibrationService (services/calibration_service.py)
│   └─ recalibrate(role): stakeholder_feedback → scoring_weights update
├─ calibration_agent.py (10th LangGraph node, between brief and END)
├─ Endpoints: POST /api/v1/feedback · GET /api/v1/feedback/summary · POST /api/v1/calibrate
└─ Simulated personas for demo: Medical Affairs Lead · Regulatory Specialist ·
   Safety/PV Officer · Market Access Manager · Medical Communications Lead ·
   Leadership/GBS Executive (extended: Commercial Strategist, R&D Scientist)

FRONTEND:
├─ Next.js 15 (App Router + Server Components)
├─ TanStack Query v5 (server-state management)
├─ shadcn/ui + TailwindCSS 4 (components)
├─ Recharts (trend charts)
├─ Framer Motion (signal card animations, subtle)
└─ react-window (virtual scrolling for 800 signals)

DEPLOYMENT:
├─ Docker Compose (5 services: backend, frontend, postgres, redis, celery)
└─ Vercel (frontend, free) + Render (backend, free) OR single VPS

MONITORING:
├─ Loguru (structured logging, better than Python logging)
└─ FastAPI built-in /metrics endpoint
```

**Key Simplification:** Replace Weaviate with pgvector.
- One less Docker container
- pgvector is now production-grade (used by Supabase, pgai)
- Hybrid search via `pg_trgm` (keyword) + `pgvector` (semantic) = same capability
- Less complexity, faster setup, simpler stack

**Research Report Alignment (deep-research-report.md):**

| Research Report Recommendation | Implemented In |
|---|---|
| tenacity + httpx for retry logic (Section 2) | `api_fetcher.py` (Gap 2 in Doc 1, SDD Section 2.4) |
| Bronze raw data table for replay (Section 2) | `raw_signals_bronze` table in PostgreSQL schema |
| Model-agnostic LLM via env var (Section 8) | `LOCAL_LLM_MODEL` + `LOCAL_LLM_TASK` env vars |
| medspacy for pharma NER (Section 2) | Added to NLP stack (optional, drop-in spaCy extension) |
| pgvector replaces Weaviate (Section 3) | ✅ Done — entire Upgrade 7 (Ask Athena) re-implemented |
| WORM audit log / 21 CFR Part 11 (Section 6) | `audit_log` table + `ComplianceAuditLogger` service |
| PII detection before storage (Section 6) | `pii_scrubber.py` pipeline step |
| Medical accuracy disclaimer (Section 6) | `DisclaimerBadge` UI component (non-suppressible) |
| SLI/SLO targets (Section 5) | Documented in SRS Section 4.1 |



---

## **PART 5: B.PHARM TEAM CONTRIBUTION (FORMALIZED)**

This is the section that judges will find most impressive — domain-expert collaboration documented as a formal workstream.

### **Domain Knowledge Artifacts (B.Pharm Deliverables)**

**1. Signal Taxonomy v1 (Week 1) — Haemophilia**
```json
{
  "signal_types": {
    "gene_therapy_milestone": {
      "description": "Gene therapy results, durability data, approvals, setbacks",
      "keywords": ["gene therapy", "AAV", "Factor IX", "durability", "Hemgenix", "Roctavian"],
      "example": "Hemgenix 3-year Factor IX durability data presented at ASH 2026"
    },
    "non_factor_therapy_update": {
      "description": "Bispecific / anti-TFPI / RNAi therapy progress",
      "keywords": ["emicizumab", "Hemlibra", "concizumab", "mim8", "fitusiran", "marstacimab"],
      "example": "Novo Nordisk mim8 Phase 3 meets primary endpoint in Haemophilia A"
    },
    "inhibitor_development_signal": {
      "description": "Inhibitor development reports or thromboembolic risk",
      "keywords": ["inhibitor", "factor VIII inhibitor", "thrombosis", "thromboembolic"],
      "example": "Fitusiran thromboembolic event reports under review"
    },
    "regulatory_milestone": {
      "description": "FDA / EMA / HTA decisions on haemophilia therapies",
      "keywords": ["FDA approval", "CHMP", "NICE", "HTA", "reimbursement decision", "label"],
      "example": "NICE appraises emicizumab for Haemophilia A with inhibitors"
    },
    "congress_publication": {
      "description": "Data presented at ASH, ISTH, WFH, EHA",
      "keywords": ["ASH 2026", "ISTH", "WFH", "EHA", "abstract", "congress"],
      "example": "ISTH late-breaker: mim8 vs emicizumab comparator data"
    },
    "patient_access_signal": {
      "description": "Reimbursement, access barriers, advocacy positions",
      "keywords": ["WFH", "access", "reimbursement", "prior authorization", "treatment access"],
      "example": "WFH calls for expanded access to non-factor therapies"
    },
    "competitive_pipeline_move": {
      "description": "Competitor assets entering/advancing in development",
      "keywords": ["Phase 1", "Phase 2", "Phase 3", "pipeline", "first-in-human"],
      "example": "New anti-TFPI asset enters Phase 1 for Haemophilia A"
    }
  }
}
```

**2. Competitive Entity Ontology (Week 1-2)**
- Drug name → brand names → mechanism → manufacturer → competitor drugs
- B.Pharm team: builds this from pharmacology knowledge
- CSE team: loads it as JSON, uses it in entity enrichment

**3. Role-Signal Mapping (Week 2)**
- Medical Affairs: Which signal types they see first + why
- Regulatory: Which signal types they see first + why
- B.Pharm team interviews their pharma faculty (domain validation)

**4. Signal Validation Testing (Week 3)**
- B.Pharm team manually reviews 50 processed signals
- Are entity extractions correct?
- Are role assignments sensible?
- Catch false positives (e.g., "gene therapy" in a cardiac surgery article, "mim8" in an engineering context)

**4A. Lifecycle + Missing-Signal Rules (Week 3)**
- B.Pharm team authors `MISSING_SIGNAL_RULES` (expected-event sequences + `max_lag_days` per haemophilia pattern: gene therapy durability, Phase 3 readout follow-up, inhibitor safety follow-up)
- B.Pharm team validates lifecycle state transitions (does `results_in → under_review → approved` make clinical sense per drug?)
- B.Pharm team seeds expected "next event" for mim8, Hemgenix, Roctavian, fitusiran

**4B. Contradiction QA (Week 3-4)**
- B.Pharm team reviews seeded contradiction pairs (e.g., ASH "sustained durability" vs real-world "waning expression") and confirms NLI flags are clinically meaningful
- B.Pharm team defines which contradiction types are actionable for Medical Affairs vs Regulatory

**5. Demo Script Domain Narration (Week 4)**
- B.Pharm team presents the domain slides
- CSE team presents the technical architecture
- Judges see both depth: pharma knowledge + engineering quality

---

## **PART 6: REFINED PROJECT NAME & BRANDING**

**MetaRadar** is good. But consider positioning it more precisely:

**Tagline Options:**
- "MetaRadar: The Haemophilia Intelligence Radar — From Signal Noise to Treatment Strategy"
- "MetaRadar: Where Haemophilia Signals Converge into Strategy"
- "MetaRadar: From Inbox Noise to Strategic Signal in Rare Disease"
- "MetaRadar: Real-Time Haemophilia Intelligence for Every Novo Nordisk Function"

**Positioning Statement (for judges):**
> "MetaRadar is not a news aggregator. It's a pharmaceutical intelligence layer that runs **five advanced analyses** on every signal — confluence detection, signal lifecycle tracking, red-team contradiction checks, missing-signal early-warning, and a stakeholder learning loop — so Novo Nordisk functions see not just *what changed*, but *where a development sits*, *whether the evidence contradicts itself*, *what should have happened but didn't*, and *which routing the people who use it have taught the system*."

---

## **PART 7: FINAL WEEK-BY-WEEK PLAN (REFINED)**

```
WEEK 1: Foundations + Domain Architecture
CSE:
├─ Next.js 15 + FastAPI skeleton
├─ PostgreSQL + pgvector setup (single DB, simpler than Weaviate)
├─ LangGraph skeleton (4 agents, no NLP yet)
├─ Docker Compose (4 services: frontend, backend, postgres, redis)
└─ NewsAPI + PubMed integration (two working sources)

B.Pharm:
├─ Signal taxonomy document (7 haemophilia signal types, keywords, examples)
├─ Haemophilia ontology draft (emicizumab, concizumab, mim8, fitusiran, Hemgenix, Roctavian + companies + indications)
└─ Role requirement interviews (faculty, if possible)

Milestone: Working dashboard showing raw signals from 2 sources

---

WEEK 2: AI Pipeline + Entity Intelligence
CSE:
├─ spaCy NER entity extraction
├─ Pharma ontology JSON integration (enrich extracted entities)
├─ Signal classification (zero-shot with BART-MNLI)
├─ BART summarization (batch, local)
├─ Signal scoring + role-relevance mapping
├─ Celery scheduled tasks (every 2h fetch)
└─ Redis caching (L1 cache, 2h TTL)

B.Pharm:
├─ Ontology review (validate drug/company mappings)
└─ Manual signal QA (review 20 processed signals, flag errors)

Milestone: NLP pipeline working — signals have entities, summaries, role scores

---

WEEK 3: Five Advanced Analyses + Dashboard Polish
CSE:
├─ Signal Confluence Engine (Analysis 1, core differentiator) + development-link
│   decision (congress/publication → existing development_id vs new development)
├─ Signal Lifecycle Tracker (Analysis 2: state machine + event chains; events record
│   event_type · event_date · development_id · source_id)
├─ Red-Team Contradiction Engine (Analysis 3: NLI entailment on bart-large-mnli)
├─ Missing-Signal Detector (Analysis 4: expected-event state machine)
├─ Watch-for-Next (Analysis 4 extension): stakeholder watch rules → watch_items
│   (statuses: watching/new_evidence_detected/no_new_evidence/watch_expired/
│   human_review_required)
├─ Relevance-based routing (Analysis output): signal_routing table — primary/secondary
│   functions + function_relevance_scores + routing_reason (seed matrix, calibration-adjustable)
├─ Congress + Publication as first-class signal types with subtypes (participate in all five mechanisms)
├─ pgvector embeddings + hybrid search
├─ "Ask Athena" lite (RAG query interface)
├─ Dashboard: Four-Question panels (Q1-Q4) + Function filter (six functions) + analysis flags
├─ Signal cards: Expandable, traceable sources, lifecycle/contradiction/missing badges,
│   routing reason + development-connection block (Development · Event · Relationship)
├─ Framer Motion animations (subtle entrance effects)
└─ Virtual scrolling (react-window)

B.Pharm:
├─ Confluence rule validation (do the patterns make clinical sense?)
├─ Lifecycle + missing-signal rules authorship (expected-event sequences, max_lag_days)
├─ Watch-rule authorship (expected next events per pattern, e.g., competitor trial → congress disclosure)
├─ Routing matrix validation (initial routes per signal type — MA/MedComms/Regulatory/Safety/PV/Market Access)
├─ Contradiction pair QA (seeded ASH vs real-world examples)
├─ Signal taxonomy v2 (refined from Week 2 QA)
└─ Prepare domain explanation slides (2-3 slides)

Milestone: Full MVP — Dashboard + Five Advanced Analyses + Ask Athena working

---

WEEK 4: Narrative Synthesis + Stakeholder Learning + Demo Hardening
CSE:
├─ Narrative Synthesis Agent (LLM-generated intelligence briefs)
├─ Temporal pattern matching (gene therapy milestone, regulatory filing patterns)
├─ Stakeholder Learning Loop (Analysis 5, HITL): feedback endpoints + recalibrate service
│   (scope: priority · routing · action · watch rules · relevance criteria)
├─ Simulated persona feedback seeding for demo (BEFORE/AFTER incl. watch-rule creation)
├─ Error handling hardening (all fallback paths tested)
├─ Performance optimization (< 500ms cached dashboard)
├─ Unit + integration tests (60% coverage minimum, incl. lifecycle/red-team/missing-signal/calibration/watch/routing)
└─ Demo recording (backup if live internet fails)

B.Pharm:
├─ Validate narrative synthesis output (does it make clinical sense?)
├─ Validate contradiction flags + missing-signal alerts in the demo dataset
├─ Finalize demo script (domain narration)
└─ Prepare competitive landscape comparison slide (haemophilia)

Final Review:
├─ Full end-to-end test with no internet (fallback only)
├─ Load test (1000 simulated signal events)
├─ Code review + documentation
└─ Presentation rehearsal (5 min slot assumed)
```

---

## **KEY DIFFERENTIATORS SUMMARY (For Presentation Slide)**

```
What existing tools do:
✓ Aggregate signals from multiple sources
✓ Summarize individual articles
✓ Show a news feed

What MetaRadar does DIFFERENTLY — THE FIVE ADVANCED ANALYSES:

1. CONFLUENCE DETECTION
   Detects when multiple independent signal types (ASH + Press Release + Patient Forum)
   converge on the same entity in 48h → single strategic alert

2. SIGNAL LIFECYCLE TRACKING
   Stitches isolated signals into a chronological state machine per development:
   "mim8: results_in (Jan 2026) → NEXT: submission announced."
   Answers "where is this, what's next?"

3. RED-TEAM CONTRADICTION ANALYSIS
   NLI entailment (local bart-large-mnli) flags when a newer signal contradicts an older
   claim on the same entity. Both evidence chains shown; devil's-advocate note; human
   review required. MetaRadar surfaces uncertainty instead of hiding it.

4. MISSING-SIGNAL DETECTION
   Absence is a signal. Expected-but-absent milestones (silent readouts, stalled
   submissions) fire early-warning alerts with confidence that grows with silence.

5. STAKEHOLDER LEARNING LOOP (HITL)
   Novo Nordisk functions rate routing accuracy inline (⭐ 1-5); weights recalibrate via
   StakeholderCalibrationService; Q3 confidence badges visibly improve. Simulated
   personas prove it live in the demo.

PLUS — the supporting intelligence layer:
6. PHARMA ONTOLOGY
   Built by B.Pharm domain experts. Knows "Hemlibra" = "emicizumab" = Roche competitor;
   "mim8" = "concizumab" = Novo Nordisk assets. Tracks competitor relationships, not just keywords.

7. TRACEABLE INTELLIGENCE
   Every insight shows source chain (which signals → why it matters).
   Regulatory-grade audit trail.

8. FREE STACK, ZERO VENDOR LOCK-IN
   Unlike Contify ($$$) or SinglePoint ($$$):
   MetaRadar runs on free APIs + local ML models + open-source stack.
```

