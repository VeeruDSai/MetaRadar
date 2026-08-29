# MetaRadar 5-Minute Hackathon Demo Script

**Novo Nordisk GBS Hackathon 2026 — Problem Statement #3: Rare Disease Competitive Intelligence Radar**  
*Pilot Domain: Haemophilia A & B*

---

## Presentation Overview

| Time | Stage | Persona | Core Value Proposition Demonstrated |
| --- | --- | --- | --- |
| **0:00 - 0:45** | **The Hook & Login** | *Public / Any* | From inbox noise to actionable intelligence; 3D-tilt Persona Selector. |
| **0:45 - 1:45** | **Functional Surveillance & Escalation** | **Dr. Elena Vance** *(Medical Affairs)* | Scoped RBAC queue, Four-Question Brief, and Cross-Functional Approval Request. |
| **1:45 - 2:45** | **Executive Governance & Decision Steer** | **Alex Mercer** *(Leadership)* | Dashboard alert banner, `/functions` approval queue, and one-click strategic directive. |
| **2:45 - 3:45** | **Unique Intelligence Mechanisms** | **Alex Mercer** *(Leadership)* | Confluence alerts, Red-Team contradictions, and Missing Signal lag tracking. |
| **3:45 - 4:30** | **Athena Evidence Reasoning** | *Any* | Natural language synthesis with vector-grounded citations and confidence telemetry. |
| **4:30 - 5:00** | **Architecture & Responsible AI** | **System Administrator** | 10-node LangGraph pipeline, offline Gemma/Grok fallback, and immutable audit logs. |

---

## Step-by-Step Timestamped Walkthrough

### ⏱ 0:00 – 0:45 | The Hook & Persona Login

**Visual:** Navigate to `http://localhost:3000/login`.

**Presenter Script:**
> "Good morning, judges. In competitive intelligence, pharma teams don't suffer from a lack of information — they drown in it. A typical Medical Affairs or Regulatory lead receives dozens of trial updates and press alerts every week. But a simple LLM summary is not enough: teams need to know **what changed**, **why it matters**, **who should act**, and **how to steer decisions across functions**."
>
> "MetaRadar is our answer: an autonomous, evidence-grounded intelligence radar built specifically for rare disease. Notice our dedicated login portal: each role has distinct responsibilities, permissions, and calibration profiles."

**Action:**
1. Hover over the **Dr. Elena Vance (Medical Affairs)** pill. Observe the 3D-tilt holographic `ProfileCard` tracking the cursor with role responsibilities and active focus.
2. Click **Dr. Elena Vance**. The credentials auto-fill (`elena.vance@metaradar.internal`).
3. Click **Sign In to MetaRadar**.

---

### ⏱ 0:45 – 1:45 | Medical Affairs: Scoped Intelligence & Escalation

**Visual:** Redirected to `http://localhost:3000/dashboard` then click **Signals** (`/signals`).

**Presenter Script:**
> "We are now logged in as Dr. Elena Vance in Medical Affairs. Notice that the signal feed is automatically scoped to Medical Affairs priorities: trial readouts, efficacy endpoints, and clinical safety alerts."
>
> "Look at this high-priority signal: a Phase III competitor readout on NXT007. MetaRadar does not dump raw text; it formats every signal into our **Four-Question Decision Framework**:"
> 1. **What Changed?** Grounded factual extract with direct source provenance.
> 2. **Why It Matters?** Clinical significance and competitive positioning.
> 3. **Who Should Act?** Routed to Medical Affairs with a priority score of 90/100.
> 4. **Suggested Action?** Prepare scientific briefing for advisory boards.

**Action:**
1. Click **Request Leadership Approval** on the signal card.
2. In the modal, explain:
   - Escalation Urgency: Select **Critical (Immediate Steer)**.
   - Strategic Rationale: Type `"Immediate executive steer needed on competitor Phase III bleeding rate readout before next week's EHA advisory board."`
3. Click **Submit Approval Request**. Observe the live transition to **"Awaiting Executive Leadership Approval"** with an amber glowing indicator.

---

### ⏱ 1:45 – 2:45 | Executive Leadership: Portfolio Governance & Sign-Off

**Visual:** Click the top-right role badge, log out, and select **Alex Mercer (Leadership)** (`Leader2026!`).

**Presenter Script:**
> "Now let's switch hats to Alex Mercer, Executive Leadership. As leadership, Alex needs a macro view of portfolio threats without getting bogged down in low-level noise."
>
> "Immediately on the Dashboard, an alert banner appears: **'Cross-Functional Escalation Awaiting Executive Steer'**. Teams from Medical Affairs have escalated an urgent decision."

**Action:**
1. Click **Review Approvals Queue** (or navigate to `/functions`).
2. Point out the **Executive Leadership Approval Queue** at the top of the workspace.
3. Show the pending request from Dr. Elena Vance with timestamp, priority, and original rationale.
4. In the directive box, type: `"Authorized. Coordinate with Comms & Market Access on comparative value deck."`
5. Click **Approve Decision**.
6. The request resolves instantly, appends an immutable record to the audit log, and notifies downstream functional queues.

---

### ⏱ 2:45 – 3:45 | Unique Intelligence Mechanisms

**Visual:** Navigate through the sidebar intelligence views: **Confluence**, **Red-Team**, and **Missing Signals**.

**Presenter Script:**
> "What truly sets MetaRadar apart from generic RAG or search tools are our three purpose-built intelligence mechanisms:"
>
> 1. **Confluence Alerts (`/confluence`):** MetaRadar doesn't treat events in isolation. When a ClinicalTrials.gov update converges with an EMA regulatory filing within a 48-hour window, the engine automatically synthesizes a unified **Multi-Source Confluence Story**.
> 2. **Red-Team Contradiction Engine (`/red-team`):** Competitive claims are often contested. Our red-team engine actively searches for conflicting trial endpoints, safety alerts, or adverse event variances (e.g., thrombotic microangiopathy in non-factor therapies) and flags them before executive decisions are made.
> 3. **Missing Signals & Lag Tracker (`/missing-signals`):** Sometimes the most critical signal is what *didn't* happen. If a competitor misses a promised Q3 trial readout or EMA filing window, MetaRadar flags a **Missing Milestone Alert**."

---

### ⏱ 3:45 – 4:30 | Athena: Vector-Grounded Natural Language Assistant

**Visual:** Navigate to **Search & Athena** (`/intelligence`).

**Presenter Script:**
> "When executives need on-the-fly answers, they ask **Athena**, our biomedical reasoning copilot."
>
> "Athena is connected directly to our PGVector embedding store (384-dimensional `all-MiniLM-L6-v2`) and local Gemma-3 LLM (with Grok API support). Notice how every response includes:"
> - **Fact-Checked Citations:** Direct hyperlinks to PubMed, ClinicalTrials.gov, and FDA dossiers.
> - **Confidence Score:** e.g., 94% evidence-grounded.
> - **Model Provenance:** Showing whether local Gemma or Grok reasoning was used, with zero hallucination guarantee.

**Action:**
1. Click the suggested prompt: *"What is the competitive impact of Mim8 versus Hemlibra?"*
2. Watch the real-time reasoning response generate with citations and structured bullet points.

---

### ⏱ 4:30 – 5:00 | Architecture, Truthfulness & Responsible AI

**Visual:** Navigate to **Sources & Health** (`/sources`) or **Activity Log** (`/observability`).

**Presenter Script:**
> "Under the hood, MetaRadar is engineered for enterprise pharmaceutical standards:"
> - **10-Node LangGraph Pipeline:** Automated ingestion, biomedical NER, ontology normalization, confluence evaluation, and 6-role routing.
> - **Truthful Operational Health:** Zero-record responses on valid endpoints are honestly reported as `NO_NEW_DATA` rather than misleadingly marked degraded.
> - **100% Offline Capability:** Operates fully air-gapped with local quantized GGUF models (`gemma-3-4b-it`) or cloud APIs (`xAI Grok`).
> - **Immutable Audit Trail:** All approval resolutions, status transitions, and user actions are cryptographically sealed in PostgreSQL with non-updatable triggers.
>
> "MetaRadar turns scattered biomedical data into clear, defensible, cross-functional strategic advantage. Thank you, and we look forward to your questions!"

---

## Hackathon Evaluation Criteria Checklist

- [x] **Problem Understanding & Novelty**: Rare disease focus (Haemophilia A/B), multi-source confluence detection, and missing signal lag tracking.
- [x] **Technical Depth & Architecture**: 10-node LangGraph orchestration, PGVector similarity search, and Next.js 16 frontend.
- [x] **User Experience & Execution**: 3D-tilt persona selector, role-scoped feeds, and instant approval workflow.
- [x] **Safety & Responsible AI**: `[FACT]`/`[INTERPRETATION]`/`[SPECULATION]` tagging, zero-hallucination citations, and immutable audit logs.
- [x] **Cross-Functional Business Value**: Scoped workflows for all 6 stakeholder roles + Executive Leadership sign-off.
