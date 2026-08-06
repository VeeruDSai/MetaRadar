# MetaRadar: UI Design Document

**Project:** MetaRadar - Real-Time Metabolic Disease Competitive Intelligence  
**Version:** 1.0  
**Date:** July 26, 2026  
**Design Framework:** shadcn/ui + TailwindCSS 4

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

### 2.1 Main Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ MetaRadar  ≡  Medical Affairs    👤 John Smith  🔔 ⚙️           │  Header
├─────────────┬─────────────────────────────────────────────────────┤
│             │                                                       │
│  SIDEBAR    │ [Date Range] [Entity Filter] [Search] [Ask Athena]  │  Controls
│  ─────────  │                                                       │
│ • Overview  │ ┌──────────────────────────────────────────────────┐ │
│ • Confluence│ │  🔴 CRITICAL — GLP-1 Safety Confluence (3 sigs)  │ │
│   Alerts    │ │  FDA study + Reddit spike + PubMed AE paper      │ │
│ • Ask Athena│ │  [View Evidence] [Dismiss]                       │ │ Confluence
│ • Medical   │ ├──────────────────────────────────────────────────┤ │  Alerts
│   Affairs   │ │  🟠 HIGH — Eli Lilly oral GLP-1 momentum (5 sigs)│ │  Panel
│ • Regulatory│ └──────────────────────────────────────────────────┘ │
│ • Commercial│                                                       │
│             │ ┌──────────────────────────────────────────────────┐ │
│             │ │  GLP-1 Signal Volume (7d)                        │ │
│  Settings   │ │  [Trend Line Chart]        ▲▼                     │ │  Trend
│  Logout     │ │  Peak: 127 signals on Jul 25                      │ │  Chart
│             │ └──────────────────────────────────────────────────┘ │
│             │                                                       │
│             │ ┌──────────────────────────────────────────────────┐ │
│             │ │ HIGH PRIORITY                                     │ │
│             │ │                                                   │ │
│             │ │ [High] Novo Nordisk Phase 2b oral GLP-1          │ │
│             │ │ Source: Reuters | 2h ago | Score: 0.92           │ │ Signal
│             │ │ ▼ Entities: semaglutide, Novo Nordisk, obesity   │ │  Card
│             │ │ Summary: "Novo's oral formulation shows 22% loss" │ │
│             │ │ [⛓ Evidence: 3 sources]                          │ │
│             │ │                                                   │ │
│             │ ├──────────────────────────────────────────────────┤ │
│             │ │ [Med] FDA: Post-marketing study required         │ │
│             │ │ Source: FDA Official | 4h ago | Score: 0.85     │ │
│             │ │ [Regulatory importance highlighted]              │ │
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
│ [▶] [High] Novo Nordisk Phase 2b oral GLP-1               │
│     Source: Reuters | 2h ago | Score: 0.92                │
└────────────────────────────────────────────────────────────┘
```

**Expanded:**
```
┌────────────────────────────────────────────────────────────┐
│ [▼] [High] Novo Nordisk Phase 2b oral GLP-1               │
│     Source: Reuters | 2h ago | Score: 0.92                │
├────────────────────────────────────────────────────────────┤
│ Summary (AI-generated):                                    │
│ "Novo Nordisk's oral semaglutide achieves 22% weight loss │
│  in Phase 2b, positioning for Q2 2027 submission."        │
├────────────────────────────────────────────────────────────┤
│ Entities:                                                  │
│ 🔬 Drug: semaglutide (GLP-1 agonist)                      │
│ 🏢 Company: Novo Nordisk                                   │
│ 📋 Indication: Obesity, Type 2 Diabetes                   │
│ 📊 Clinical Phase: Phase 2b                                │
├────────────────────────────────────────────────────────────┤
│ Role Relevance:                                            │
│ Medical Affairs:  ████████░░ 0.92  (Very Relevant)        │
│ Regulatory:       ██████░░░░ 0.68  (Somewhat Relevant)   │
│ Commercial:       ███░░░░░░░ 0.35  (Not Relevant)         │
├────────────────────────────────────────────────────────────┤
│ ⛓ Evidence Chain (traceable reasoning):                    │
│ [1] Reuters · Jul 25 → "Novo oral GLP-1 Phase 2b results"  │
│     https://reuters.com/...  (excerpt preview)             │
│ [2] ClinicalTrials.gov · Jul 24 → trial NCT-registration   │
│     https://clinicaltrials.gov/...  (excerpt preview)      │
│ [3] PubMed · Jul 23 → "Comparative efficacy oral GLP-1..."  │
│     https://pubmed.ncbi.nlm.nih.gov/...  (excerpt preview) │
│ Confidence: 84% (3 independent sources, 3 platforms)       │
├────────────────────────────────────────────────────────────┤
│ Original Source:                                           │
│ "Novo Nordisk's oral semaglutide showed sustained weight  │
│  loss with favorable safety profile in Phase 2b trial.    │
│  The company plans pivotal studies for late 2026..."      │
│                                                            │
│ [Read Full Article →]                                     │
└────────────────────────────────────────────────────────────┘
```

> **Traceability note:** Every insight (signal card, confluence alert, narrative brief) shows the full evidence chain — source name, URL, timestamp, excerpt. This is the regulatory-grade audit trail that differentiates MetaRadar from generic CI tools (Refined Architecture, Upgrade 5).
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
│ ☑ Drugs: semaglutide, tirzepatide, dulaglutide          │
│ ☐ Companies: Novo Nordisk, Eli Lilly, Pfizer            │
│ ☐ Indications: Obesity, Diabetes, CVD                   │
│                                                            │
│ Signal Type:                                              │
│ ☑ Clinical Success  ☑ Safety  ☑ Competitive  ☑ Access  │
│                                                            │
│ Search:  [🔍 "oral formulation" ]  [Clear All]           │
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
   - Navigation: Overview, Confluence Alerts, Ask Athena, Briefs, Dashboard, Settings, Help
   - Account section (user name, avatar)

3. **Main Content**
   - **Controls Bar** (fixed below header)
     - Date range selector
     - Entity filters (multi-select)
     - Search box (keyword + semantic)
     - "Ask Athena" quick-launch input
     - Apply/Reset buttons

   - **Confluence Alerts Panel** (top, collapsible)
     - Consolidated cross-source convergence alerts (CRITICAL/HIGH first)
     - Each alert: entity + signal count + expandable evidence chain
     - See §3.2 for full page

   - **Trend Visualization**
     - Line chart: Signal volume over 7 days
     - X-axis: Date
     - Y-axis: Signal count
     - Interactive: Hover shows exact values
     - Note: "Last refreshed 15 minutes ago"

   - **Signal Feed**
     - Paginated list (20 signals per page)
     - Virtual scrolling (infinite scroll)
     - Each signal shows: priority badge, title, source, time, score
     - Clickable to expand full details

4. **Footer**
   - Data freshness: "Last updated 2:15 PM • Cached"
   - API status indicators: ✓ NewsAPI, ✓ PubMed, ⚠ Twitter
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
│  ⚡ Signal Confluence — GLP-1 Ecosystem (last 48h)             │
├─────────────────────────────────────────────────────────────────┤
│ Filters: [Entity ▼] [Time Window: 48h ▼] [Alert: All ▼]        │
├─────────────────────────────────────────────────────────────────┤
│ 🔴 CRITICAL                                                    │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ GLP-1 Safety Confluence — 3 signals, 48h                 │ │
│ │ "FDA requires post-marketing study, patient complaints   │ │
│ │  trending, adverse event paper published. Potential      │ │
│ │  safety narrative forming."                              │ │
│ │ Sources: FDA.gov · Reddit r/diabetes · PubMed            │ │
│ │ Recommended action: Medical Affairs review within 24h    │ │
│ │ [View full evidence chain] [Export audit trail]          │ │
│ └───────────────────────────────────────────────────────────┘ │
│ 🟠 HIGH                                                       │
│  Eli Lilly oral GLP-1 momentum (5 signals · 48h)             │
│  Pattern: PRE-APPROVAL SURGE · stage 3/5 (FDA advisory)      │
│  Predicted next: Priority review designation                  │
│  [View full evidence chain]                                  │
│ 🟠 HIGH                                                       │
│  Semaglutide India market access (4 signals · 48h)           │
│  Generics pricing + formulary signals converging              │
├─────────────────────────────────────────────────────────────────┤
│ [Refresh] — confluence rescan runs every 2h with ingestion    │
└─────────────────────────────────────────────────────────────────┘
```

**Notes:**
- Alert level color-coding: 🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM / ⚪ LOW
- Each alert links to its full evidence chain (traceable reasoning)
- Temporal pattern tag shows current + predicted stage (e.g., "PRE-APPROVAL SURGE, stage 3/5")

### 3.3 Ask Athena Page (`/athena`)

Natural-language query interface (Week 4 RAG feature). Judging hook: "we don't just browse intelligence — we ask questions."

```
┌─────────────────────────────────────────────────────────────────┐
│  Ask Athena                                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 🔍 What is Eli Lilly doing with oral GLP-1?              │  │
│  └───────────────────────────────────────────────────────────┘  │
│  [Ask]  (role-scoped: Medical Affairs)                          │
├─────────────────────────────────────────────────────────────────┤
│  Answer (grounded in 4 signals, last 7 days):                    │
│  "Eli Lilly's oral GLP-1 program is advancing: Phase 3        │
│   registration filed (ClinicalTrials.gov), orforglipron       │
│   expected FDA approval 2027, HCP forum discussion rising.    │
│   No comparative efficacy data published this week."          │
│  Confidence: 82% · based on 4 supporting signals                │
├─────────────────────────────────────────────────────────────────┤
│  Supporting signals:                                             │
│  [1] ClinicalTrials.gov — orforglipron Phase 3 registered       │
│  [2] Reuters — Lilly investor call mentions oral timeline       │
│  [3] PubMed — comparator oral vs injectable GLP-1              │
└─────────────────────────────────────────────────────────────────┘
```

**Behavior:**
- Empty/hallucination guard: if insufficient signals → `"Insufficient signals in last 7 days"` (never make things up)
- Every answer cites supporting signals + retrieval confidence
- Answers are role-scoped (Medical Affairs cannot see Commercial-only queries)

### 3.4 Narrative Briefs View (`/briefs`)

```
┌─────────────────────────────────────────────────────────────────┐
│  Weekly Intelligence Brief — Eli Lilly (Medical Affairs)  [Export]│
├─────────────────────────────────────────────────────────────────┤
│ 🟠 WHAT HAPPENED: 5 independent signals this week (2 clinical, │
│    1 regulatory, 2 social) detail Lilly's oral GLP-1 momentum │
│ 🎯 WHY IT MATTERS: oral formulation directly threatens Novo's │
│    oral semaglutide share; historically Lilly wins head-to-head│
│ ✅ RECOMMENDED ACTION: Medical Affairs should review the Phase │
│    3 registration package before the August advisory committee │
├─────────────────────────────────────────────────────────────────┤
│ Source counts: 5 · Confidence: 84% · Full evidence chain ↓      │
└─────────────────────────────────────────────────────────────────┘
```

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
│ ☑ Semaglutide                   │  Searchable
│ ☑ GLP-1                         │  Checkboxes
│ ☐ Tirzepatide                   │  Scrollable
│ ☐ Dulaglutide                   │  
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
⏱ PRE-APPROVAL SURGE · Stage 3/5    (shows current position in competitive timeline)
⏱ ACCESS CRISIS · Stage 2/3
```

**Evidence Chain Indicator**
```
⛓ Evidence: 3 sources     Click to expand source → URL → excerpt audit trail
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
⚠ Twitter      Yellow warning, "Slow (last: 5m ago)"
✗ Reddit       Red error, "Connection failed"
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
   FDA.gov      ──▶ ● ──────────────────┐
   Reddit       ──▶ ● ──▶ ● ────────────┤
   PubMed       ──────────────────── ▶  ●  ← CONVERGENCE
   NewsAPI      ──▶ ● ──────────────────┘        (GLP-1 safety)
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
          semaglutide
      GLP-1       Eli Lilly
    obesity               Novo Nordisk
  Phase2b      diabetes        efficacy
     clinical        weight-loss
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
│ Entity: [semaglutide │
│         ▼]          │
│ [Search...]         │
├─────────────────────┤
│ ┌─────────────────┐ │
│ │ Trend Chart     │ │
│ │ (smaller, full  │ │
│ │  width)         │ │
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
│ Date: [▼] Entity: [semaglutide ▼] Search:[▼]│
│                                              │
│ ┌────────────────────────────────────────┐   │
│ │   Trend Chart (70% width)              │   │
│ │   ▲ 150 signals                        │   │
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
- `TemporalPatternTag` — "PRE-APPROVAL SURGE · Stage 3/5" indicator
- `NarrativeBriefCard` — WHAT / WHY / ACTION executive brief
- `OntologyTag` — resolves brand → molecule → company (Wegovy → semaglutide → Novo Nordisk)

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

