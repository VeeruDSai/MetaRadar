# MetaRadar: UI Design Document

**Project:** MetaRadar - Real-Time Haemophilia Competitive Intelligence Radar  
**Version:** 2.1  
**Date:** August 2026  
**Design Framework:** shadcn/ui + TailwindCSS 4  
**Scope Note:** Revised for Novo Nordisk GBS Hackathon 2026 kickoff — replaced Signal Feed + Trend layout with the **Four-Question Panel layout (Q1–Q4)**, added stakeholder review widget (HITL calibration), and haemophilia-themed examples (v2.0); extended with the **Five Advanced Analyses** UI — lifecycle timeline, red-team contradiction panel, and missing-signal warnings (v2.1). **v3.2 (Aug 13, 2026):** integrated the B.Pharm domain research UI (Master Plan v4.0 §12) — domain metadata row (disease/factor/inhibitor/population/modality), evidence-maturity label, evidence-context panels (Q5–Q7), Red-Team evidence-check flags, "WHY THIS ROUTING", and "WATCH FOR NEXT" on the signal card; advanced clinical-evidence fields remain expandable so the default card is never overloaded.

> [!IMPORTANT]
> **HISTORICAL REFERENCE DOCUMENT**  
> *Note: This document is preserved for historical context and architectural evolution. The sole canonical and authoritative master specification for MetaRadar is [METARADAR_MASTER_PLAN_v3.0.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/METARADAR_MASTER_PLAN_v3.0.md).*

---

## **1. DESIGN SYSTEM**

### 1.1 Design Principles

1. **Information Hierarchy:** Signals ranked by relevance at the top
2. **Minimal Cognitive Load:** One role = one view (no option paralysis)
3. **Progressive Disclosure:** Hide details until needed (expand signal cards)
4. **Real-Time Awareness:** Visual indicators of data freshness
5. **Accessibility First:** WCAG 2.1 AA (keyboard nav, color contrast, screen readers)
6. **Mobile-First:** Responsive by default (desktop > tablet > mobile)
7. **Confluence First:** Strategic alerts (converging stories) surface above raw signal feeds
8. **Total Traceability:** Every insight shows its evidence chain — source → URL → excerpt (regulatory-grade)
9. **Grounded Answers:** Ask Athena never invents; insufficient signals produce a clear "insufficient" response
10. **Four-Question Clarity:** Every signal card answers Q1→Q4 (What changed / Why it matters / Which function / What action) with role-routing confidence badges
11. **Human-in-the-Loop:** Stakeholders rate routing accuracy inline; weights recalibrate and confidence badges update (HITL calibration loop)
12. **Lifecycle Awareness (v2.1):** Every development shows its place in a chronological state machine (results_in → next: submission) — an analyst always knows "where is this, what's next"
13. **Devil's-Advocate Transparency (v2.1):** Contradicting claims are surfaced with both evidence chains and a red-team note — MetaRadar shows uncertainty, never hides it
14. **Silence Is a Signal (v2.1):** Expected-but-absent milestones render as missing-signal warnings with growing confidence — the dashboard surfaces what did *not* happen
15. **Five-to-Four Visual Convergence:** The UI visually presents five underlying intelligence mechanisms (Confluence, Lifecycle, Red-Team Contradiction, Missing-Signal, Stakeholder HITL) feeding directly into the four decision panels (Q1-Q4).
16. **Fact/Interpretation/Speculation Transparency (v3.0):** Every intelligence output carries a visible F-I-S label; speculation is never presented as fact; insufficient evidence renders "Insufficient evidence to support an interpretation."
17. **Internal Decision Support Only (v3.0):** The UI never implies clinical, regulatory, or safety decisions are being made autonomously; every suggested action is a suggestion requiring human review.
18. **Relevance-Based Routing (v3.1):** *"Not every signal needs to go to everyone."* The UI shows primary/secondary function routing with a routing reason — never a bare broadcast. Congress and publication signals render a Development Connection block (Development · Event · Relationship · Related evidence) so judges see Confluence/Lifecycle working. Watch-for-Next rules render on the Missing-Signals page with explicit statuses.

### 1.2 Color Palette

```
PRIMARY (Signal importance)
├─ Red (#EF4444):        High priority / Urgent signals
├─ Orange (#F97316):     Medium priority
├─ Green (#22C55E):      Positive signals (clinical success)
└─ Blue (#3B82F6):       Neutral information

SEMANTIC (Health)
├─ Success (Green):      Data loaded, API available
├─ Warning (Orange):     Cache used, degraded mode
├─ Error (Red):          API failed, data stale
└─ Info (Blue):          FYI: cached since 2h ago

NEUTRAL
├─ Text Primary:         #1F2937 (dark gray)
├─ Text Secondary:       #6B7280 (medium gray)
├─ Background Primary:   #FFFFFF
├─ Background Secondary: #F9FAFB (light gray)
└─ Border:               #E5E7EB

DARK MODE (Optional)
├─ Background:           #0F172A
├─ Text:                 #F1F5F9
└─ Border:               #334155
```

### 1.3 Typography

```
Font Family: Inter (system-ui fallback)

Scale:
├─ Display:     48px / 3.2rem  (h1, page title)
├─ Heading 1:   36px / 2.25rem (section headers)
├─ Heading 2:   28px / 1.75rem (subsections)
├─ Heading 3:   20px / 1.25rem (card titles)
├─ Body:        16px / 1rem    (default, paragraphs)
├─ Small:       14px / 0.875rem (labels, captions)
└─ Tiny:        12px / 0.75rem  (timestamps, badges)

Weight:
├─ Regular:     400 (body text)
├─ Medium:      500 (labels, highlights)
├─ Semibold:    600 (headings, emphasis)
└─ Bold:        700 (strong emphasis)

Line Height:
├─ Headings:    1.2
├─ Body:        1.5
└─ Small:       1.4
```

### 1.4 Spacing Scale (8px base)

```
0:   0px      (no space)
1:   8px      (xs: gaps between elements)
2:   16px     (sm: component padding)
3:   24px     (md: section padding)
4:   32px     (lg: large sections)
5:   40px     (xl: between major sections)
6:   48px     (2xl: page-level gaps)

Usage:
─ Card padding: 2 (16px)
─ Component gap: 1 (8px)
─ Section margin: 4 (32px)
```

### 1.5 Shadow Hierarchy

```
Elevations (for depth perception):

Flat:
  box-shadow: none

Raised:
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05)

Floating:
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1)

Modal/Overlay:
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1)

Usage:
─ Cards:      Raised
─ Hoverable elements: Floating on hover
─ Modals:     Modal
```

---

## **2. LAYOUT WIREFRAMES**

### 2.1 Main Dashboard Layout — Four-Question Panels

The dashboard is re-organized around the Four-Question Framework (Q1→Q4). Each panel answers one question; a single signal card in Q1 unfolds across Q2→Q4. Background tints per panel: Q1 `#F0F4FF` (blue) · Q2 `#FFF4E6` (orange) · Q3 `#F0FFF4` (green) · Q4 `#FFF0F0` (red).

```
┌─────────────────────────────────────────────────────────────────┐
│ MetaRadar  ≡  Medical Affairs    👤 John Smith  🔔 ⚙️           │  Header
├─────────────┬─────────────────────────────────────────────────────┤
│             │ [Date Range] [Entity Filter] [Search] [Ask Athena]  │  Controls
│  SIDEBAR    │                                                       │
│  ─────────  │ ┌──────────────────────────────────────────────────┐ │
│ • Overview  │ │  🔴 CRITICAL — Hemgenix 3yr Durability @ ASH     │ │
│ • Q2 Panel  │ │  ASH abstract + CSL press release + patient      │ │
│ • Confluence│ │  forum → 3 signals in 48h                        │ │
│   Alerts    │ │  [View Evidence] [Dismiss]                       │ │ Confluence
│ • Lifecycles│ ├──────────────────────────────────────────────────┤ │  Alerts
│ • Red-Team  │ │  🟠 HIGH — mim8 Phase 3 readout (5 sigs)         │ │  Panel
│ • Missing   │ ├──────────────────────────────────────────────────┤ │
│   Signals   │ │  ⚔ CONTRADICTION — Hemgenix efficacy vs waning   │ │ Red-Team
│ • Ask Athena│ │  🕳 MISSING — mim8 submission expected 90d ago    │ │ + Missing
│ • Medical   │ └──────────────────────────────────────────────────┘ │  Alerts
│   Affairs   │                                                       │
│ • Regulatory│ ┌──────────────────────────────────────────────────┐ │
│ • Safety/PV │ │  Q1  WHAT CHANGED?      Q3  WHICH FUNCTION?      │ │
│ • Market Acc│ │  ┌────────────────────┐ ┌──────────────────────┐ │ │
│ • Med Comms │ │  │ Signal Feed        │ │ Function Routing     │ │ │
│ • Leadership│ │  │ [haemophilia tags] │ │ MedAff 92% · Reg 71% │ │ │
│             │ │  │ [⏱ lifecycle]     │ │ Safety/PV 52%        │ │ │ Four-
│             │ │  │ [⚔ contradiction] │ │ MedComms 64%         │ │ │ Question
│  Settings   │ │  │ [🕳 missing]       │ │ [feedback ⭐ widget] │ │ │ Panels
│  Logout     │ │  │                      │ │                      │ │ │ (Q1-Q4)
│             │ ├──────────────────────────┴──────────────────────┤ │ │
│             │ │ Q2  WHY DOES IT MATTER?   Q4  WHAT ACTION?      │ │ │
│             │ │  ┌────────────────────┐ ┌──────────────────────┐ │ │
│             │ │  │ Relevance breakdown│ │ AI-suggested actions │ │ │
│             │ │  │ AI explanation     │ │ "Suggested — requires│ │ │
│             │ │  │ Confluence alert   │ │  human review"       │ │ │
│             │ │  │ Lifecycle stage    │ │  (incl. missing-     │ │ │
│             │ │  │ Contradiction flags│ │  signal / red-team   │ │ │
│             │ │  │ Competitive context│ │  follow-up actions)  │ │ │
│             │ │  └────────────────────┘ └──────────────────────┘ │ │
│             │ └──────────────────────────────────────────────────┘ │
│             │                                                       │
│             │ [Show More Signals] → Load next 20                  │
│             │                                                       │
└─────────────┴─────────────────────────────────────────────────────┘
```

### 2.2 Signal Card (Detailed View)

**Collapsed:**
```
┌────────────────────────────────────────────────────────────┐
│ [▶] [High] Hemgenix 3-year Factor IX durability @ ASH      │
│     Source: CSL Behring | 2h ago | Score: 0.92            │
└────────────────────────────────────────────────────────────┘
```

**Expanded (Four-Question layout):**
```
┌────────────────────────────────────────────────────────────┐
│ [▼] [High] Hemgenix 3-year Factor IX expression data shows │
│     sustained efficacy at ASH 2026                        │
│     Source: CSL Behring | 2h ago | Score: 0.92            │
│     Evidence: FACT · Disease: Haemophilia B · Patient:     │
│     Without inhibitors · Company: CSL Behring · Asset:     │
│     Hemgenix · Signal: congress · Priority: HIGH           │
│     ▸ DOMAIN (v4.0): Disease: Haemophilia B · Factor: FIX  │
│       Inhibitor: Without · Population: Adult · Modality:   │
│       AAV gene therapy · Evidence maturity: MEDIUM/HIGH    │
│       (congress abstract — preliminary, not regulatory)    │
├────────────────────────────────────────────────────────────┤
│ Q1 · WHAT CHANGED?  (panel tint #F0F4FF)                   │
│ "CSL Behring/UniQure present 3-year durability for         │
│  etranacogene dezaparvovec (Hemgenix) in Haemophilia B —   │
│  sustained Factor IX expression, no new safety signals."   │
│ Entities: 🔬 gene therapy · 🏢 CSL Behring, UniQure       │
│           📋 Haemophilia B · 📊 FDA-approved (2022)        │
│ TRIAL: NCT03350945 · Phase 3 · Comparator: prophylaxis     │
│ ABR/bleeding + FIX activity + follow-up 3 yrs (nullable     │
│ clinical-evidence fields; expandable — v4.0)               │
├────────────────────────────────────────────────────────────┤
│ Q2 · WHY DOES IT MATTER?  (panel tint #FFF4E6)             │
│ Relevance: Medical Affairs 0.92 · Regulatory 0.71 ·         │
│ MedComms 0.64 · Safety/PV 0.52 · Market Access 0.38        │
│ AI: "Sustained 3-year gene-therapy durability strengthens  │
│  the curative narrative vs lifelong prophylaxis — impacts  │
│  mim8/concizumab positioning and HTA arguments."           │
│ ⚡ CONFLUENCE: gene_therapy_milestone_parade (3 signals/48h)│
│ ⏱ LIFECYCLE: Hemgenix · results_in → NEXT: durability      │
│   follow-up publication                                    │
│ ⚔ CONTRADICTION (v2.1): "sustained 3-yr efficacy" (ASH)    │
│   vs "waning expression in subset" (real-world) · score 0.81│
│   [View evidence A] [View evidence B] · Human review req.  │
│ ⚠ RED-TEAM CHECKS (v4.0): [H] short follow-up vs durability│
│   claim · [I] congress abstract = preliminary · [P] linked  │
│   to development · [B] same data ≠ new event — expandable   │
├────────────────────────────────────────────────────────────┤
│ 🔍 WHY WAS THIS FLAGGED?  (explainable priority, v3.0)     │
│ ✓ 3 independent sources in 48h (confluence)                │
│ ✓ Relevant competitor (CSL Behring · gene therapy)         │
│ ✓ Lifecycle: results_in → next: durability follow-up       │
│ ✓ Regulatory + HTA implication · Priority: 91/100          │
├────────────────────────────────────────────────────────────┤
│ Q3 · WHICH FUNCTION SHOULD REVIEW IT?  (panel tint #F0FFF4)│
│ Medical Affairs        ██████████ 0.92  (Primary)          │
│ Regulatory             ████████░░ 0.71  (Secondary)        │
│ Medical Communications ██████░░░░ 0.64  (Secondary)        │
│ Safety/PV              ████░░░░░░ 0.52  (Low)              │
│ Market Access          ███░░░░░░░ 0.38  (Low)              │
│ Leadership             ██░░░░░░░░ 0.25  (Low)              │
│ ROUTING REASON: "Clinical efficacy/safety data with         │
│  potential implications for scientific understanding and   │
│  future regulatory review." (explainable, v3.1)           │
│ WHY THIS ROUTING? (v4.0): new congress data → Medical       │
│  Affairs primary + MedComms/Regulatory secondary per the    │
│  six-function matrix (research-informed, Master Plan §12.5)│
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ⭐ Stakeholder Review (HITL calibration):              │ │
│ │ Was this routing correct?  ★★★★★ (1-5)               │ │
│ │ [Submit] — recalibrates priority/routing/action/watch  │ │
│ │ badges update next cycle                              │ │
│ └────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────┤
│ Q4 · WHAT ACTION MAY BE REQUIRED?  (panel tint #FFF0F0)    │
│ Suggested — requires human review (controlled vocabulary)  │
│  [PREPARE INTERNAL BRIEFING] Medical Affairs — gene-       │
│      therapy durability vs prophylaxis positioning         │
│      (reason · evidence: sources 1-3 · confidence 84%)     │
│  [REVIEW] Regulatory — label/durability claim consistency  │
│  [ESCALATE] Safety/PV — waning-expression subset watch     │
│  [MONITOR] Market Access — HTA budget-impact implication   │
│      (v2.1 · ⚔ contradiction flagged above)                │
├────────────────────────────────────────────────────────────┤
│ EVIDENCE CONTEXT (v4.0 — explainability support)           │
│ Q5 · HOW STRONG IS THE EVIDENCE?                           │
│  Evidence maturity: MEDIUM/HIGH (congress abstract)        │
│  Confidence: 84% · Source authority: congress archive      │
│ Q6 · WHAT IS UNCERTAIN OR CONTRADICTORY?                   │
│  ⚔ waning-expression subset vs sustained claim (0.81)      │
│  ⚠ follow-up 3 yrs — durability beyond 12m not yet proven  │
│ Q7 · WHAT SHOULD WE WATCH NEXT?                            │
│  ◉ Watch for: peer-reviewed publication / regulatory data  │
│  (monitoring — not a claim the event will occur)           │
├────────────────────────────────────────────────────────────┤
│ ⛓ Evidence Chain (traceable reasoning):                    │
│ [1] ASH 2026 Abstract · Dec → "Hemgenix 3-yr data"         │
│     https://ash.confex.com/...  (excerpt preview)          │
│ [2] CSL Behring PR · Dec → "3-year durability results"     │
│     https://cslbehring.com/...  (excerpt preview)          │
│ [3] Reddit r/Hemophilia · Dec → patient discussion         │
│     https://reddit.com/...  (excerpt preview)              │
│ Confidence: 84% (3 independent sources, 3 platforms)       │
├────────────────────────────────────────────────────────────┤
│ 🔗 DEVELOPMENT CONNECTION (congress/publication signals,   │
│    v3.1)                                                   │
│ Development: FRONTIER4 · Event: ISTH 2026 abstract         │
│ Relationship: "New evidence for existing development"     │
│   (NOT a new card — linked via development_id)             │
│ Related evidence: [ClinicalTrials.gov] [previous           │
│   publication] [congress presentation]                     │
│ WATCH FOR NEXT (v4.0): stakeholder watch rule — next       │
│   congress disclosure of this trial · status: watching     │
│   (wording: "Watch for…" — never a claim)                 │
├────────────────────────────────────────────────────────────┤
│ Original Source:                                           │
│ "Etranacogene dezaparvovec (Hemgenix) demonstrated         │
│  sustained Factor IX activity and low bleeding rates       │
│  through 3 years follow-up in Haemophilia B..."            │
│                                                            │
│ [Read Full Article →]                                     │
└────────────────────────────────────────────────────────────┘
```

> **Traceability note:** Every insight (signal card, confluence alert, narrative brief) shows the full evidence chain — source name, URL, timestamp, excerpt. This is the regulatory-grade audit trail that differentiates MetaRadar from generic CI tools (Refined Architecture, Upgrade 5).

> **Medical Disclaimer (required per research report Section 6):** Every AI-generated summary MUST display a muted disclaimer label: *"Auto-generated by MetaRadar AI — verify clinically before use."* This is non-suppressible. Implemented as a `<DisclaimerBadge />` component rendered below every AI summary on signal cards, confluence alerts, and narrative briefs.

```tsx
// components/DisclaimerBadge.tsx
export const DisclaimerBadge = () => (
  <p className="text-xs text-gray-400 mt-1 italic">
    ⚠ Auto-generated by MetaRadar AI — verify clinically before use.
  </p>
);
```
```

### 2.3 Filter/Search Interface

```
┌──────────────────────────────────────────────────────────┐
│ Control Bar                                               │
├──────────────────────────────────────────────────────────┤
│                                                            │
│ Date Range:                Entity:                        │
│ [Last 24h] [Last 7d] [Last 30d] [Custom ▼]              │
│                                                            │
│ Entity Filter:                                            │
│ ☑ Drugs: emicizumab, mim8, concizumab, fitusiran          │
│ ☐ Companies: Roche, Novo Nordisk, Sanofi, Pfizer, CSL     │
│ ☐ Indications: Haemophilia A, Haemophilia B, Inhibitors   │
│ ☐ Modalities: Gene therapy, Bispecific, Anti-TFPI, RNAi   │
│                                                            │
│ Signal Type:                                              │
│ ☑ Gene Therapy  ☑ Non-Factor  ☑ Inhibitor  ☑ Regulatory  │
│ ☑ Congress/Publication  ☑ Patient Access  ☑ Pipeline     │
│                                                            │
│ Search:  [🔍 "gene therapy durability" ]  [Clear All]     │
│                                                            │
│ [Apply] [Reset]                                           │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

---

## **3. PAGE SPECIFICATIONS**

### 3.1 Dashboard Page (`/dashboard`)

**URL:** `/dashboard?role=medical_affairs`

**Components:**
1. **Header** (sticky)
   - Logo + app name
   - Current role display
   - User menu (profile, settings, logout)
   - Notification badge (unread count)

2. **Sidebar** (fixed, collapsible on mobile)
   - Role switcher (if user has multiple roles)
   - Navigation: Overview, Confluence Alerts, Lifecycles, Red-Team Contradictions, Missing Signals, Ask Athena, Briefs, Dashboard, Settings, Help
   - Account section (user name, avatar)

3. **Main Content — Four-Question Panels**
   - **Controls Bar** (fixed below header)
     - Date range selector
     - Entity filters (multi-select, haemophilia ontology)
     - Search box (keyword + semantic)
     - "Ask Athena" quick-launch input
     - Apply/Reset buttons

   - **Confluence Alerts Panel** (top, collapsible)
     - Consolidated cross-source convergence alerts (CRITICAL/HIGH first)
     - Each alert: entity + signal count + expandable evidence chain
     - See §3.2 for full page

   - **Analysis Panels (v2.1)** — collapsible strip between Confluence and the Q-grid:
     - **Lifecycle (⏱):** active development timelines — entity, current state, expected next event
     - **Red-Team (⚔):** contradiction alerts with both evidence chains + red-team note
     - **Missing Signals (🕳):** expected-but-absent milestones with confidence-by-silence

   - **Four-Question Panel Grid** (2×2)
     - **Q1 WHAT CHANGED?** (#F0F4FF) — Signal feed with signal-type badges, haemophilia entity tags, and analysis flags (⏱ lifecycle · ⚔ contradiction · 🕳 missing)
     - **Q2 WHY DOES IT MATTER?** (#FFF4E6) — Relevance breakdown, AI explanation, confluence alert, lifecycle stage, contradiction flags, competitive context
     - **Q3 WHICH FUNCTION SHOULD REVIEW IT?** (#F0FFF4) — Role-routing badges with confidence scores + inline stakeholder feedback widget (★ 1-5)
     - **Q4 WHAT ACTION MAY BE REQUIRED?** (#FFF0F0) — AI-suggested action bullets prefaced "Suggested — requires human review" (incl. red-team reconciliation + missing-signal follow-ups)
   - **Haemophilia Signal Volume (7d)** line chart
     - X-axis: Date, Y-axis: Signal count, grouped by signal type
     - Note: "Haemophilia gene therapy signal volume (7d)" chart label
     - Interactive: Hover shows exact values

4. **Footer**
   - Data freshness: "Last updated 2:15 PM • Cached"
   - API status indicators: ✓ NewsAPI, ✓ PubMed, ⚠ Reddit
   - Calibration status: "Weights recalibrated 3x this month — latest by Regulatory persona"
   - Help link

**Performance Targets:**
- Initial load: < 500ms (cached) / < 3s (cold)
- Interaction (scroll, filter): < 100ms
- Signal expansion: < 200ms

**Responsive Breakpoints:**
```
Mobile (< 768px):
├─ Sidebar: Collapsed/hamburger menu
├─ Chart: Full width, touch-friendly
└─ Cards: Full width stack

Tablet (768px - 1024px):
├─ Sidebar: 200px fixed
├─ Chart: 70% width
└─ Cards: 2-column grid

Desktop (> 1024px):
├─ Sidebar: 250px fixed
├─ Chart: 100% width
└─ Cards: Single column (full width)
```

### 3.2 Confluence Alerts Page (`/confluence`)

The Signal Confluence Engine output — MetaRadar's core differentiator. Instead of 800 isolated signals, judges see converging stories → strategic alerts.

**URL:** `/confluence?role=medical_affairs`

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ⚡ Signal Confluence — Haemophilia Gene Therapy (last 48h)     │
├─────────────────────────────────────────────────────────────────┤
│ Filters: [Entity ▼] [Time Window: 48h ▼] [Alert: All ▼]        │
├─────────────────────────────────────────────────────────────────┤
│ 🔴 CRITICAL                                                    │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Hemgenix 3-year Durability — 3 signals, 48h              │ │
│ │ "ASH abstract + CSL Behring press release + r/Hemophilia│ │
│ │  patient discussion all fire on sustained FIX expression.│ │
│ │  Gene-therapy durability narrative strengthening."       │ │
│ │ Pattern: GENE_THERAPY_MILESTONE_PARADE · stage 3/4       │ │
│ │ Sources: ASH 2026 · CSL Behring · Reddit r/Hemophilia    │ │
│ │ Recommended action: Medical Affairs review within 24h    │ │
│ │ [View full evidence chain] [Export audit trail]          │ │
│ └───────────────────────────────────────────────────────────┘ │
│ 🟠 HIGH                                                       │
│  mim8 Phase 3 readout (5 signals · 48h)                      │
│  Pattern: COMPETITIVE_REGULATORY_FILING · stage 2/4          │
│  Predicted next: sBLA filing vs emicizumab                   │
│  [View full evidence chain]                                  │
│ 🟠 HIGH                                                       │
│  Fitusiran inhibitor safety wave (2 signals · 24h)           │
│  Pattern: INHIBITOR_SAFETY_WAVE                             │
├─────────────────────────────────────────────────────────────────┤
│ [Refresh] — confluence rescan runs every 2h with ingestion    │
└─────────────────────────────────────────────────────────────────┘
```

**Notes:**
- Alert level color-coding: 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM / ⚪ LOW
- Each alert links to its full evidence chain (traceable reasoning)
- Temporal pattern tag shows current + predicted stage (e.g., "PRE-APPROVAL SURGE, stage 3/5")
- **`[Export Audit Trail]` button is required on every confluence alert** (research report Section 2 / FR-2.7.3): exports the full source chain + evidence + user actions as a structured JSON or CSV for regulatory review
- **`<DisclaimerBadge />`** rendered below every AI-generated story summary: *"Auto-generated by MetaRadar AI — verify clinically before use"*

### 3.2A Lifecycle Timelines Page (`/lifecycles`)

Analysis 2 (Signal Lifecycle Tracking) output. Each tracked development renders as a chronological state machine — the answer to "where is this development, and what's next?"

**URL:** `/lifecycles?role=medical_affairs`

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ⏱ Development Lifecycles (haemophilia)                         │
├─────────────────────────────────────────────────────────────────┤
│ Filters: [Entity ▼] [State: All ▼] [Modality ▼]                │
├─────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ mim8 · Novo Nordisk · Bispecific · Haemophilia A          │ │
│ │ ┌──────┬──────────┬──────────────┬─────────────┐         │ │
│ │ │ 2024 │  2025    │  2026-01     │  NEXT ▶     │         │ │
│ │ │announced        │results_in    │ submission  │         │ │
│ │ │Phase 3          │endpoint met  │ announced   │         │ │
│ │ └──────┴──────────┴──────────────┴─────────────┘         │ │
│ │ State: RESULTS_IN (validated by 4 signals)                │ │
│ │ Expected next: regulatory submission announced            │ │
│ │ [View full timeline] [Export audit trail]                 │ │
│ └───────────────────────────────────────────────────────────┘ │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Hemgenix · CSL Behring · Gene therapy · Haemophilia B    │ │
│ │ ⚔ Contradiction attached: sustained vs waning durability │ │
│ │ State: RESULTS_IN · Next: durability follow-up           │ │
│ └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2B Red-Team Contradictions Page (`/red-team`)

Analysis 3 (Red-Team Contradiction Analysis) output. Contradicting claims surface with BOTH evidence chains and a devil's-advocate note.

**URL:** `/red-team?role=medical_affairs`

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────────┐
│  ⚔ Red-Team Contradiction Analysis (rolling 90d window)        │
├─────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ ⚔ CONTRADICTION — Hemgenix durability (score 0.81)        │ │
│ │ ┌─ CLAIM A ─────────────────┐ ┌─ CLAIM B ──────────────┐ │ │
│ │ │ "Sustained 3-year Factor  │ │ "Declining Factor IX   │ │ │
│ │ │  IX expression"           │ │  expression in subset" │ │ │
│ │ │ ASH 2026 abstract         │ │ Real-world cohort,     │ │ │
│ │ │ Dec 2025 · [url]          │ │ Jan 2026 · [url]       │ │ │
│ │ └───────────────────────────┘ └────────────────────────┘ │ │
│ │ 🧠 Red-team note: "Newest evidence may overturn earlier  │ │
│ │   durability claim. Requires human review before use in  │ │
│ │   HTA engagement."                                       │ │
│ │ [Reconcile] [Dismiss] [Export both evidence chains]      │ │
│ └───────────────────────────────────────────────────────────┘ │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ ⚔ CONTRADICTION — fitusiran thrombosis (score 0.72)      │ │
│ │  ...                                                     │ │
│ └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2C Missing Signals Page (`/missing-signals`)

Analysis 4 (Missing-Signal Detection) output. Silence is surfaced as intelligence — with confidence that grows the longer the silence lasts.

**URL:** `/missing-signals?role=regulatory`

**Wireframe:**
```
┌─────────────────────────────────────────────────────────────────┐
│  🕳 Missing-Signal Detection (expected-but-absent events)       │
├─────────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ 🕳 MISSING — Roctavian next-generation data publication   │ │
│ │ Last signal: Jul 2026 (label update) · Silence: 150 days  │ │
│ │ Expected within: 180 days · Confidence: 0.70 (growing)    │ │
│ │ ████████████████░░░░░░  confidence-by-silence meter       │ │
│ │ [Verify against other sources] [Dismiss as expected]      │ │
│ └───────────────────────────────────────────────────────────┘ │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ 🕳 MISSING — mim8 regulatory submission announcement      │ │
│ │ Last signal: Jan 2026 (readout) · Silence: 95 days        │ │
│ │ Expected within: 180 days · Confidence: 0.66              │ │
│ └───────────────────────────────────────────────────────────┘ │
│ Note: false-positive discipline — alerts only after the       │
│ configured max_lag window; confidence grows with silence.     │
│                                                               │
│ 👁 WATCH-FOR-NEXT (stakeholder-defined watch rules, v3.1)    │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ WATCH #fr4 · Competitor Phase III → upcoming congress     │ │
│ │ disclosures · Window: 180d · Responsible: Medical Affairs │ │
│ │ Status: ● WATCHING — "Watch for upcoming congress         │ │
│ │   disclosures · Expected/possible next evidence · Not     │ │
│ │   observed yet"                                           │ │
│ │ [Create watch rule] [Extend window] [Mark human review]   │ │
│ └───────────────────────────────────────────────────────────┘ │
│ Statuses: watching · new_evidence_detected · no_new_evidence │
│ · watch_expired · human_review_required. Absence wording:    │
│ "No subsequent congress evidence observed during the         │
│ configured monitoring window." (never proof nothing happened)│
└─────────────────────────────────────────────────────────────────┘
```


### 3.3 Ask Athena Page (`/athena`)

Natural-language query interface (Week 4 RAG feature). Judging hook: "we don't just browse intelligence — we ask questions."

```
┌─────────────────────────────────────────────────────────────────┐
│  Ask Athena                                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 🔍 What is the latest on mim8?                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│  [Ask]  (function-scoped: Medical Affairs)                      │
├─────────────────────────────────────────────────────────────────┤
│  Answer (grounded in 4 signals, last 7 days):                    │
│  "Novo Nordisk's mim8 Phase 3 programme in Haemophilia A       │
│   met its primary endpoint; analysts expect submission vs      │
│   emicizumab positioning. No new safety signals reported.      │
│   Durability beyond 12 months not yet published."              │
│  Confidence: 82% · based on 4 supporting signals                │
├─────────────────────────────────────────────────────────────────┤
│  Supporting signals:                                             │
│  [1] ClinicalTrials.gov — mim8 Phase 3 (HA) registered         │
│  [2] Reuters — Novo Nordisk press release on readout           │
│  [3] PubMed — mim8 vs emicizumab comparator data               │
│  [4] Reddit r/Hemophilia — HCP/patient reaction                │
└─────────────────────────────────────────────────────────────────┘
```

**Behavior (v3.0):**
- Required answer schema: **Answer · Evidence · Sources · Confidence · Relevant entities · Lifecycle context · Contradicting evidence (if present)**
- Empty/hallucination guard: if evidence is insufficient → `"Insufficient evidence to support an interpretation."` (never make things up)
- Every answer carries an F-I-S label and cites supporting signals + retrieval confidence
- Answers are function-scoped (e.g., Medical Affairs cannot see queries scoped to another function)

### 3.4 Narrative Briefs View (`/briefs`)

```
┌─────────────────────────────────────────────────────────────────┐
│  Weekly Intelligence Brief — Hemgenix (Medical Affairs)  [Export]│
├─────────────────────────────────────────────────────────────────┤
│ 🟠 WHAT HAPPENED: 5 independent signals this week (2 clinical, │
│    1 regulatory, 2 patient_access) detail Hemgenix 3-yr data  │
│ 🎯 WHY IT MATTERS: sustained gene-therapy durability threatens │
│    lifelong prophylaxis model; affects mim8/concizumab messaging│
│ ✅ RECOMMENDED ACTION: Medical Affairs should review the 3-yr  │
│    durability evidence before the next HTA engagement          │
├─────────────────────────────────────────────────────────────────┤
│ Source counts: 5 · Confidence: 84% · Full evidence chain ↓      │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4A Weekly Intelligence Digest (`/digest`)

Function-filtered weekly digest reusing the SAME intelligence pipeline (no second architecture). Top developments first, ranked by explainable priority; each item is a mini Four-Question card.

```
┌─────────────────────────────────────────────────────────────────┐
│  Weekly Haemophilia Intelligence Digest — [Function tabs:        │
│  Medical Affairs | Regulatory | Safety/PV | Market Access |     │
│  Medical Communications | Leadership]        [Export MD/PDF/JSON]│
├─────────────────────────────────────────────────────────────────┤
│  1. Hemgenix 3-yr durability @ ASH (FACT · conf 84%)           │
│     WHAT CHANGED: ...   WHY IT MATTERS: ...                     │
│     FUNCTION: Medical Affairs (primary) · Regulatory            │
│     ACTION: Prepare internal briefing · EVIDENCE: [1][2][3]     │
│  2. mim8 submission silence (WATCH · conf 0.66)                │
│     ...                                                         │
└─────────────────────────────────────────────────────────────────┘
```

**Behavior:** each digest item includes What changed · Why it matters · Function · Suggested action (controlled vocabulary) · Evidence · Confidence · F-I-S label. Role/filter tabs produce the Medical Affairs Digest, Regulatory Digest, Safety Digest, etc. from the same generated content.

### 3.5 Authentication Pages

**Login Page (`/login`)**
```
┌────────────────────────────────────┐
│                                    │
│       METARADAR INTELLIGENCE        │
│                                    │
│    "From Inbox Noise to Signal"   │
│                                    │
│  ┌──────────────────────────────┐  │
│  │ Email:    [_____________]    │  │
│  │ Password: [_____________]    │  │
│  │                              │  │
│  │ [Sign In] [Forgot Password?] │  │
│  └──────────────────────────────┘  │
│                                    │
│  Built for Novo Nordisk Teams      │
│                                    │
└────────────────────────────────────┘
```

---

## **4. INTERACTIVE ELEMENTS**

### 4.1 Buttons

**Primary Button** (CTA, main actions)
```
┌──────────────────┐
│    Apply Filter  │  Background: #3B82F6 (blue)
└──────────────────┘  Text: white
                      Hover: #2563EB (darker blue)
                      Padding: 8px 16px
```

**Secondary Button** (Less important)
```
┌──────────────────┐
│    Cancel        │  Background: #E5E7EB (light gray)
└──────────────────┘  Text: #1F2937 (dark gray)
                      Hover: #D1D5DB
                      Padding: 8px 16px
```

**Danger Button** (Destructive)
```
┌──────────────────┐
│    Delete All    │  Background: #EF4444 (red)
└──────────────────┘  Text: white
                      Hover: #DC2626
                      Padding: 8px 16px
```

### 4.2 Form Inputs

**Text Input**
```
Email: [____________________]     Placeholder: "your@email.com"
       ↑                          Focus: Blue border, shadow
    Label

Password: [__________________]    Type: password (masked)
          ↑                       Show/hide icon on right
       Label
```

**Multi-Select Dropdown**
```
Entity Filter: ▼
┌─────────────────────────────────┐
│ ☑ Emicizumab                    │  Searchable
│ ☑ Mim8                          │  Checkboxes
│ ☐ Concizumab (Alhemo)           │  Scrollable
│ ☐ Fitusiran                    │  
│ ☐ Hemgenix                     │  
│ ☐ Roctavian                    │  
│ [Search entities...]            │
└─────────────────────────────────┘
```

**Date Range Picker**
```
Date Range: [Last 7d ▼]
┌──────────────────────────────┐
│ Last 24h                      │
│ Last 7d        ← Selected     │
│ Last 30d                      │
│ Last 3 months                 │
│ Last year                     │
│ Custom:  [From] [To]          │
└──────────────────────────────┘
```

### 4.3 Status Indicators

**Priority Badges**
```
[High]     Red background, white text
[Medium]   Orange background, white text
[Low]      Gray background, dark text
```

**Confluence Alert Badges (Intelligence Layer)**
```
🔴 CRITICAL   Dark red background, white text — 3+ signal types converged
🟠 HIGH       Orange background, white text — 2 signal types, high impact
🟡 MEDIUM     Yellow background, dark text — 2 signal types, moderate impact
⚪ LOW        Gray background, dark text — single signal type cluster
```

**Temporal Pattern Indicator**
```
⏱ GENE_THERAPY_MILESTONE_PARADE · Stage 3/4    (shows current position in competitive timeline)
⏱ COMPETITIVE_REGULATORY_FILING · Stage 2/4
⏱ INHIBITOR_SAFETY_WAVE · Stage 1/3
```

**Lifecycle State Indicator (v2.1)**
```
⏱ RESULTS_IN → NEXT: submission announced    (green pulse = active development)
⏱ UNDER_REVIEW · 4 signals · mim8
⏱ DISCONTINUED · greyed out
```

**Red-Team Contradiction Badge (v2.1)**
```
⚔ CONTRADICTION · score 0.81    (purple #7C3AED, two evidence chains shown)
```

**Missing-Signal Badge (v2.1)**
```
🕳 MISSING · expected 150d ago · conf 0.70   (amber, with confidence-by-silence meter)
```

**Evidence Chain Indicator**
```
⛓ Evidence: 3 sources     Click to expand source → URL → excerpt audit trail
```

**F-I-S Label (v3.0)**
```
FACT (green)          — directly supported by reliable source evidence
INTERPRETATION (blue) — reasoned interpretation, always labeled as AI interpretation
SPECULATION (amber)   — early/uncertain signal, never presented as fact
INSUFFICIENT          — "Insufficient evidence to support an interpretation." + human review
```

**Action Vocabulary Chip (v3.0)**
```
[MONITOR] [REVIEW] [PREPARE INTERNAL BRIEFING] [PREPARE SCIENTIFIC FAQ]
[ESCALATE] [REQUEST STAKEHOLDER REVIEW] [NO IMMEDIATE ACTION]
Each chip: action + reason + relevant function + evidence + confidence + human review
```

**Data Freshness Indicators**
```
✓ Live        Green checkmark (data < 5 min old)
◐ Recent      Yellow icon (data < 2h old)
⚠ Cached      Orange icon (data 2-24h old)
✗ Stale       Red X (data > 24h old)
```

**API Status (Footer)**
```
✓ NewsAPI      Green indicator, "Connected"
⚠ Reddit       Yellow warning, "Slow (last: 5m ago)"
✗ ClinicalTrials.gov   Red error, "Connection failed"
```

### 4.4 Modals & Dialogs

**Confirmation Dialog**
```
┌──────────────────────────────────────┐
│ ⚠ Clear Cache?                       │  Title
├──────────────────────────────────────┤
│                                      │
│ Are you sure? This will refresh      │  Body
│ all signals from APIs (may take      │
│ up to 2 minutes).                    │
│                                      │
├──────────────────────────────────────┤
│      [Cancel]     [Clear Cache]      │  Buttons
│       (secondary)    (primary)        │
└──────────────────────────────────────┘
```

---

## **5. VISUALIZATIONS**

### 5.1 Trend Chart (Recharts)

**Line Chart: Signal Volume over 7 Days**

```
Signal Count
     │
 150 │     ╱╲
     │    ╱  ╲      ╱
 100 │   ╱    ╲    ╱╲
     │  ╱      ╲  ╱  ╲____
  50 │ ╱        ╲╱         
     │
     └──────────────────────── Days
     Jul21  Jul22  Jul23  Jul24  Jul25
```

**Configuration:**
```typescript
<LineChart data={data} width={800} height={300}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="date" />
  <YAxis />
  <Tooltip 
    contentStyle={{ background: "white", border: "1px solid #ccc" }}
    formatter={(value) => [`${value} signals`, "Count"]}
  />
  <Legend />
  <Line 
    type="monotone" 
    dataKey="count" 
    stroke="#3B82F6" 
    strokeWidth={2}
  />
</LineChart>
```

### 5.2 Confluence Diagram (Intelligence Layer)

**Visualization: Signals converging on an entity over time**

```
                           48h window
   ASH 2026       ──▶ ● ──────────────────┐
   Reddit         ──▶ ● ──▶ ● ────────────┤
   CSL Behring    ──────────────────── ▶  ●  ← CONVERGENCE
   ClinicalTrials ──▶ ● ──────────────────┘        (Hemgenix 3-yr)
                                        │
                              🔴 CRITICAL alert
```

**Configuration:**
```typescript
// Each source is a separate colored line/timeline
// Circles = individual signals (color = signal_type)
// A "convergence marker" appears where ≥ 2 types meet within 48h
// Click marker → opens confluence alert with full evidence chain
```

**Alternative (for dashboard):** Compact "Confluence Feed" list — each item shows alert level badge, entity, signal count, and expandable evidence chain (see §3.2).

### 5.3 Relevance Bars (Horizontal Bar Chart)

**Per-Role Relevance Score Visualization**

```
Medical Affairs:  ████████░░ 0.92  (92%)
Regulatory:       ██████░░░░ 0.68  (68%)
Commercial:       ███░░░░░░░ 0.35  (35%)

Color Scale:
  0.00-0.33: Red (#EF4444)
  0.34-0.66: Orange (#F97316)
  0.67-1.00: Green (#22C55E)
```

### 5.4 Entity Tag Cloud (Optional Week 4)

**Most Mentioned Terms**

```
          emicizumab
      mim8       Hemgenix
    concizumab           Roche
  gene-therapy      inhibitor     bispecific
     factor-IX        bleeding-rate
```

---

## **6. ACCESSIBILITY REQUIREMENTS**

### 6.1 Keyboard Navigation

```
Tab:        Focus next element
Shift+Tab:  Focus previous element
Enter:      Click focused button / expand signal
Space:      Toggle checkbox/radio
Escape:     Close modal/menu
```

### 6.2 Screen Reader Support

```
- All images have alt text
- Buttons have aria-label
- Form fields have associated labels
- Charts have table fallback (for screen readers)
- Modals: aria-modal="true", focus trap

Example:
<button aria-label="Apply filters">
  Apply Filter
</button>
```

### 6.3 Color Contrast (WCAG AA)

```
All text must have minimum 4.5:1 contrast ratio

Examples:
✓ Black on white:      21:1    (good)
✓ #1F2937 on white:    15:1    (good)
✗ Gray on white:       2.5:1   (bad)
```

### 6.4 Responsive Text

```
Font size adjustable:   zoom 200% works
No horizontal scroll:   Reflow text at all viewport widths
Touch targets:          Minimum 44x44px (not 16px buttons)
Motion:                 Prefers-reduced-motion respected
```

---

## **7. DARK MODE (Optional)

**Toggle in Settings**

```
Settings:
  ☐ Dark Mode

If enabled:
├─ Background: #0F172A
├─ Text: #F1F5F9
├─ Cards: #1E293B
├─ Borders: #334155
└─ Primary color: #60A5FA (lighter blue)
```

---

## **8. ERROR & EMPTY STATES**

### 8.1 Error State

```
┌────────────────────────────────────┐
│ ❌ Failed to load signals           │  Error banner
├────────────────────────────────────┤
│                                    │
│ Sorry, we couldn't fetch the       │
│ latest signals. Using cached data  │
│ from 2 hours ago.                  │
│                                    │
│ [Retry] [Dismiss]                  │
│                                    │
│ (showing cached data below)         │
│                                    │
└────────────────────────────────────┘
```

### 8.2 Empty State

```
┌────────────────────────────────────┐
│                                    │
│           📭 No Signals             │
│                                    │
│   No signals found for             │
│   "Medical Affairs" in last 24h    │
│                                    │
│   Try:                             │
│   • Expand date range              │
│   • Remove entity filters          │
│   • Clear search                   │
│                                    │
│ [Adjust Filters]                   │
│                                    │
└────────────────────────────────────┘
```

**Empty State — No Confluence Alerts:**
```
┌────────────────────────────────────┐
│ ⚡ No convergence detected          │
│                                    │
│   No cross-source confluence in    │
│   the last 48h for your role.      │
│                                    │
│   Signals are still being tracked  │
│   — alerts appear automatically    │
│   when 2+ signal types converge.   │
│                                    │
│ [View raw signal feed]             │
└────────────────────────────────────┘
```

**Empty State — Ask Athena (hallucination guard):**
```
┌────────────────────────────────────┐
│  Question: "What is ...?"          │
│                                    │
│  "Insufficient signals in last     │
│   7 days to answer this."          │
│                                    │
│  Try:                              │
│  • Expand the time window          │
│  • Ask about a different entity    │
└────────────────────────────────────┘
```

### 8.3 Loading State

```
┌────────────────────────────────────┐
│ Loading signals...                  │  Progress indicator
│ ████░░░░░░░░░░░░░░░░░ 22%         │  Estimated time: 5s
└────────────────────────────────────┘

Skeleton loaders for card list:
┌───────────────────┐
│ ███████░░░░░░░░░░░│  Placeholder
│ ███░░░░░░░░░░░░░░░│  Cards
│ ████████░░░░░░░░░░│
└───────────────────┘
```

---

## **9. RESPONSIVE DESIGN SAMPLES**

### 9.1 Mobile Layout (< 768px)

```
┌─────────────────────┐
│ ☰ MetaRadar    🔔 👤│  Hamburger menu
├─────────────────────┤
│ Date: [Last 7d ▼]   │
│ Entity: [emicizumab │
│         ▼]          │
│ [Search...]         │
├─────────────────────┤
│ ┌─────────────────┐ │
│ │ Q1-Q4 Panels    │ │
│ │ (2×2 stack,     │ │
│ │  full width)    │ │
│ └─────────────────┘ │
├─────────────────────┤
│ ┌─────────────────┐ │
│ │ [High] Signal 1 │ │
│ │ Score: 0.92     │ │
│ └─────────────────┘ │
│ ┌─────────────────┐ │
│ │ [Med] Signal 2  │ │
│ │ Score: 0.68     │ │
│ └─────────────────┘ │
└─────────────────────┘
```

### 9.2 Tablet Layout (768px - 1024px)

```
┌──────────────────────────────────────────────┐
│ MetaRadar    [Medical Affairs]    🔔 👤     │
├──────────────────────────────────────────────┤
│                                              │
│ Date: [▼] Entity: [emicizumab ▼] Search:[▼]                │
│                                              │
│ ┌────────────────────────────────────────┐   │
│ │   Q1-Q4 Panels (2×2)                   │   │
│ │   Q1 Feed │ Q3 Role badges             │   │
│ │   Q2 Why  │ Q4 Actions                 │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ ┌────────────────────────────────────────┐   │
│ │   Haemophilia Signal Volume (7d)       │   │
│ │   ▲ 150 signals (gene therapy ↑)      │   │
│ │   │      ╱╲                            │   │
│ │   │     ╱  ╲                           │   │
│ │   └─────────────────────────────────   │   │
│ └────────────────────────────────────────┘   │
│                                              │
│ ┌──────────────────────┐ ┌──────────────────┐│
│ │ [High] Signal 1      │ │ [High] Signal 2  ││
│ │ Score: 0.92          │ │ Score: 0.88      ││
│ └──────────────────────┘ └──────────────────┘│
│ ┌──────────────────────┐ ┌──────────────────┐│
│ │ [Med] Signal 3       │ │ [Med] Signal 4   ││
│ │ Score: 0.68          │ │ Score: 0.65      ││
│ └──────────────────────┘ └──────────────────┘│
│                                              │
└──────────────────────────────────────────────┘
```

---

## **10. ANIMATION & TRANSITIONS**

### 10.1 Entrance Animations

```css
Signal cards fade in on load:
animation: fadeIn 0.3s ease-in-out;

Trend chart draws animation:
animation: slideUp 0.5s ease-out;
```

### 10.2 Interactions

```
Button hover:  0.2s transition to darker color
Menu slide in: 0.3s ease-out from left
Modal fade:    0.2s opacity transition
```

### 10.3 Prefers-Reduced-Motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## **11. COMPONENT LIBRARY (shadcn/ui)**

**Used Components:**
- Button
- Card
- Input
- Select (Multi-select dropdown)
- DatePicker
- Badge (Priority tags + Confluence alert levels)
- Tabs (Role switcher)
- AlertDialog (Confirmation)
- Skeleton (Loading states)
- Tooltip (Hover info)
- Accordion (Expandable evidence chain)
- Timeline (Temporal pattern stages)
- Progress (Confluence confidence / pattern stage progress)

**MetaRadar-specific components (custom):**
- `ConfluenceAlertCard` — alert level badge + entity + signal count + evidence chain
- `EvidenceChain` — collapsible source → URL → excerpt audit trail
- `AthenaQueryBar` — natural-language input + grounded answer + supporting signals
- `TemporalPatternTag` — "GENE_THERAPY_MILESTONE_PARADE · Stage 3/4" indicator
- `NarrativeBriefCard` — WHAT / WHY / ACTION executive brief
- `OntologyTag` — resolves brand → molecule → company (Hemlibra → emicizumab → Roche)
- `StakeholderFeedbackWidget` (NEW v2.0) — inline ★ 1-5 rating on Q3 role badges; posts to `POST /api/v1/feedback`, shows "routing confidence updated after calibration"
- `QuestionPanel` (NEW v2.0) — the four-question wrapper with panel tint (`#F0F4FF`/`#FFF4E6`/`#F0FFF4`/`#FFF0F0`) and Q1-Q4 headers
- `LifecycleTimeline` (NEW v2.1) — chronological state machine per development (entity, current state, expected next); renders `GET /api/v1/lifecycles`
- `ContradictionPanel` (NEW v2.1) — dual evidence chain display (claim A vs claim B) + red-team note; renders `GET /api/v1/contradictions`
- `MissingSignalCard` (NEW v2.1) — expected-but-absent event + confidence-by-silence meter; renders `GET /api/v1/missing-signals`
- `ConfidenceBySilenceMeter` (NEW v2.1) — visual meter that grows with days of silence (0.4 → 0.95)
- `RoutingBadges` (NEW v3.1) — primary + secondary function badges with per-function relevance scores AND the routing reason line (explainable routing; renders `GET /api/v1/signals/{id}` routing block)
- `DevelopmentLinkCard` (NEW v3.1) — congress/publication connection block: Development · Event · Relationship ("New evidence for existing development") · Related evidence links
- `WatchRuleCard` (NEW v3.1) — stakeholder-defined watch: source event → expected next event → window → responsible function → status (watching / new_evidence_detected / no_new_evidence / watch_expired / human_review_required); renders `GET /api/v1/watchlist`

**Installation:**
```bash
npx shadcn-ui@latest add button card input select badge
npx shadcn-ui@latest add alert-dialog tabs skeleton tooltip
npx shadcn-ui@latest add accordion timeline progress
```

---

## **12. DESIGN TOKENS**

**TailwindCSS Config:**
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    colors: {
      primary: '#3B82F6',
      secondary: '#10B981',
      danger: '#EF4444',
      warning: '#F97316',
    },
    spacing: {
      0: '0px',
      1: '8px',
      2: '16px',
      3: '24px',
      4: '32px',
    },
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
    },
  },
};
```

---

## **13. REVISION HISTORY**

| Version | Date | Changes |
|---|---|---|
| 1.0 | 2026-07-26 | Initial MVP wireframes |
| 1.1 | 2026-07-28 | Aligned with Refined Architecture: added Confluence Alerts page (§3.2), Ask Athena page (§3.3), Narrative Briefs view (§3.4), traceable evidence chain on signal cards (§2.2), confluence diagram viz (§5.2), confluence/pattern/evidence badges (§4.3), custom intelligence components (§11) |
| 2.0 | 2026-08-12 | Novo Nordisk kickoff revision: Four-Question panel layout (Q1–Q4) replaces Signal Feed + Trend (§2.1, §3.1, §15); stakeholder review widget on Q3 role badges (HITL calibration); haemophilia entity filters + signal types (§2.3); "Haemophilia gene therapy signal volume (7d)" chart; haemophilia-themed examples throughout |
| 2.1 | 2026-08-12 | Five Advanced Analyses UI: lifecycle timeline page (§3.2A) + state badges; red-team contradiction page (§3.2B) + dual-evidence panel; missing-signal page (§3.2C) + confidence-by-silence meter; analysis strip on dashboard (§3.1); analysis flags on Q1 feed and Q2/Q4 panels (§2.2, §15); design principles 12-14 |

---

## **14. DESIGN REVIEW CHECKLIST**

Before handoff to development:

- [ ] All wireframes approved by stakeholders
- [ ] Accessibility audit passed (WCAG AA)
- [ ] Responsive breakpoints tested
- [ ] Color contrast verified (4.5:1 minimum)
- [ ] Interaction patterns documented
- [ ] Component library mapped to designs
- [ ] Dark mode variant defined
- [ ] Error states for all API calls
- [ ] Empty states for all views (incl. "No confluence alerts", "Insufficient signals" for Athena)
- [ ] Loading states with skeleton loaders
- [ ] Performance guidelines documented
- [ ] Animations respect prefers-reduced-motion
- [ ] Confluence alert levels color-coded and distinguishable (not just red/orange)
- [ ] Evidence chain accessible from every insight (traceable reasoning)
- [ ] Temporal pattern stages rendered as visual timeline
- [ ] "Ask Athena" hallucination guard state tested ("Insufficient signals in last 7 days")
- [ ] Four-Question panels (Q1–Q4) color-coded (#F0F4FF/#FFF4E6/#F0FFF4/#FFF0F0) and distinguishable (NEW v2.0)
- [ ] Stakeholder feedback widget renders on Q3 panel and posts to `/api/v1/feedback` (NEW v2.0)
- [ ] Q4 action bullets prefaced "Suggested — requires human review" (NEW v2.0)
- [ ] Calibration status visible in footer (e.g., "Weights recalibrated 3x this month") (NEW v2.0)

---

## **15. FOUR-QUESTION DISPLAY SPECIFICATIONS (NEW v2.0)**

The Four-Question Framework is the primary dashboard paradigm. Every signal card renders the four questions as a horizontal stepper / stacked panels. Panel background tints visually separate the questions.

### 15.1 Panel Colors (per question)

| Panel | Question | Hex | Purpose |
|---|---|---|---|
| Q1 | WHAT CHANGED? | `#F0F4FF` | Blue — live signal feed, signal-type badges, entity tags |
| Q2 | WHY DOES IT MATTER? | `#FFF4E6` | Orange — relevance breakdown, AI explanation, confluence alert, competitive context |
| Q3 | WHICH FUNCTION SHOULD REVIEW IT? | `#F0FFF4` | Green — role-routing badges with confidence scores + stakeholder feedback widget |
| Q4 | WHAT ACTION MAY BE REQUIRED? | `#FFF0F0` | Red — AI-suggested action bullets prefaced *"Suggested — requires human review"* |

### 15.2 Q3 Role Badge Component

```tsx
// components/RoleBadge.tsx — Q3 panel
export const RoleBadge = ({ role, confidence }: { role: Role; confidence: number }) => (
  <span className="inline-flex items-center gap-1 rounded-full bg-green-50 px-2 py-0.5 text-xs font-medium text-green-800 ring-1 ring-green-200">
    {roleLabel[role]}
    <span className="text-green-600">{Math.round(confidence * 100)}%</span>
    {/* post-calibration uplift indicator, e.g. "▲ +4 after calibration" */}
  </span>
);
```

### 15.3 Stakeholder Feedback Widget (Q3)

Inline on the Q3 panel of every signal card. Posted to `POST /api/v1/feedback` (`{signal_id, role, rating, reason, user_id}`). After N feedback rows for a role, `POST /api/v1/calibrate` is triggered; confidence badges show the updated score on the next dashboard load.

**Mandatory demo requirement (v3.0):** the UI MUST render a visible BEFORE/AFTER comparison for at least one signal:
```
BEFORE:  Priority = 78 · Function = Regulatory · Action = Review
FEEDBACK: Regulatory persona corrects → "Safety/PV is the primary function"
AFTER:   Priority = 84 · Function = Safety/PV · Action = Escalate
Changed: function routing + action + relevance score
```
The feedback must visibly change priority, function routing, action, relevance score, or explanation logic — a feedback form alone is not sufficient.

**Watch-for-Next calibration demo (v3.1):** a stakeholder comment such as *"Monitor this competitor trial specifically for upcoming congress disclosures"* MUST produce a visible watch-rule change alongside the routing change:
```
BEFORE:  Priority = Medium · Routing = Medical Affairs · Action = Monitor · (no watch)
FEEDBACK: "Monitor this competitor trial for future congress disclosures"
AFTER:   Priority = High · Primary = Medical Affairs · Secondary = Medical Communications
         Action = Monitor + prepare internal review · WATCH = upcoming congress disclosures
Changed: priority + routing + action + watch rule created (status = watching)
```
The watch rule then appears on the Missing-Signals page (§3.2C) and flips to `new_evidence_detected` when the next congress signal links into the same development.

```tsx
// components/StakeholderFeedbackWidget.tsx
export const StakeholderFeedbackWidget = ({ signalId, role }) => {
  const [rating, setRating] = useState(0);
  const [reason, setReason] = useState("");
  return (
    <div className="rounded-lg border border-green-200 bg-green-50 p-2 text-xs">
      <p className="font-medium text-green-800">⭐ Stakeholder review — was this routing correct?</p>
      <div className="flex gap-1 py-1">{Array.from({ length: 5 }, (_, i) => (
        <button key={i} onClick={() => setRating(i + 1)} aria-label={`${i + 1} star`} className="text-lg">
          {i < rating ? "★" : "☆"}
        </button>
      ))}</div>
      <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Optional: why?" className="w-full rounded border border-green-300 p-1" />
      <button onClick={() => submitFeedback(signalId, role, rating, reason)} className="mt-1 rounded bg-green-600 px-2 py-0.5 text-white">
        Submit (recalibrates weights)
      </button>
    </div>
  );
};
```

### 15.4 Q4 Action Suggestion Component

Every Q4 bullet is prefaced by the fixed label *"Suggested — requires human review"*. Actions are non-committal (checkboxes, no implied approval). Grouped by target function.

### 15.5 Responsive Behavior

- Desktop (>1024px): 2×2 grid — Q1+Q3 left column, Q2+Q4 right column
- Tablet (768–1024px): single column, panels stacked Q1→Q4
- Mobile (<768px): panels collapse; Q1 feed first, others behind a "Why it matters / Action" expander

