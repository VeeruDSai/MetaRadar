# Medical Affairs and Haemophilia Signal Prioritisation for MetaRadar

## What is it?

Medical Affairs (MA) is the cross-functional scientific function that helps interpret emerging evidence and translate it into medically accurate, clinically useful and compliant actions. In a haemophilia-focused intelligence system such as MetaRadar, Medical Affairs should not simply receive a stream of articles. It should help determine whether a new signal could change the understanding of efficacy, safety, treatment strategy, patient outcomes, clinical development or scientific communication.

For MetaRadar, a haemophilia signal is any new piece of information that may affect the understanding or development of haemophilia treatments or patient care. Signals can come from:

- ClinicalTrials.gov trial records and updates
- Peer-reviewed publications
- Regulatory decisions, labels, safety communications and assessment reports from FDA/EMA
- Congresses such as ISTH, WFH and EHA
- Official company clinical-development announcements
- Guidelines and consensus statements
- Real-world evidence and patient-outcome studies

The key Medical Affairs question is:

> Does this information materially change what we know about a haemophilia therapy, its benefit-risk profile, the treatment landscape, patient outcomes, or the clinical-development pathway?

This is important because a single therapy can generate multiple signals over time. A trial may first appear on a registry, then produce a congress abstract, a company announcement, a full publication, a regulatory submission, a regulatory decision and later long-term follow-up. MetaRadar should connect these events instead of treating each one as an unrelated news item.

The World Federation of Hemophilia (WFH) guidelines explicitly address diagnosis and management, musculoskeletal complications, inhibitors, laboratory/genetic assessment and outcome assessment, demonstrating that haemophilia monitoring needs to go beyond a single efficacy number. [1]

## What did I find?

### 1. Clinical efficacy: bleeding outcomes are central

Annualised bleeding rate (ABR) is one of the most important outcomes used in haemophilia trials. ClinicalTrials.gov defines ABR as the annualised number of bleeding episodes per participant, and trial records can distinguish treated, untreated, spontaneous, traumatic, joint and other bleeding categories. [2]

The HAVEN 3 phase 3 trial is a useful example of why the magnitude and context of an efficacy result matter. In people with haemophilia A without inhibitors, emicizumab prophylaxis produced model-based ABRs of 1.5 and 1.3 events/year for two dosing regimens compared with 38.2 events/year with no prophylaxis; the reported reduction was 96–97%. The study also measured joint and target-joint bleeding and safety outcomes. [3]

The HAVEN 1 trial in haemophilia A with inhibitors similarly reported an ABR of 2.9 events/year with emicizumab prophylaxis versus 23.3 with no prophylaxis, an 87% reduction. Importantly, the study also found improvements in health-related quality of life and health status, while identifying thrombotic microangiopathy/thrombosis in the context of high cumulative activated prothrombin complex concentrate exposure. [4]

**MetaRadar implication:** A model should not only detect the words "positive trial" or "reduced bleeding." It should extract the actual endpoint, comparator, effect size, confidence interval/P-value when available, population, treatment regimen and safety findings.

### 2. Patient outcomes are broader than bleeding

Haemophilia affects joints, physical function, pain, daily activities and quality of life. Repeated joint bleeding can contribute to permanent joint damage. The WFH guidelines include musculoskeletal complications and outcome assessment as core elements of haemophilia management. [1]

The HAVEN 1 publication provides a concrete example: alongside bleeding outcomes, the trial assessed Haem-A-QoL and EQ-5D-5L measures and reported statistically significant benefits in health-related quality of life and health status. [4]

The EMA assessment of Alhemo (concizumab) also illustrates why patient outcomes can strengthen a signal: in its clinical evidence, the agency described improvements in pain and physical functioning alongside reductions in bleeding episodes. [5]

**MetaRadar implication:** Patient-reported outcomes (PROs), quality-of-life measures, pain, physical functioning, joint outcomes and treatment burden should be extracted as separate evidence fields rather than being buried in a general summary.

### 3. Safety can override an otherwise positive efficacy result

A clinically effective haemophilia treatment can still create a high-priority signal if an important safety issue emerges.

For example, the FDA states that Alhemo (concizumab) can increase the risk of blood clots and reports hypersensitivity reactions among safety considerations. [6] FDA's clinical review also identified thromboembolic risk as an issue reflected in the prescribing information. [7]

The HAVEN 1 experience is another example: emicizumab showed major bleeding reduction, but thrombotic microangiopathy and thrombosis occurred in participants receiving high cumulative doses of activated prothrombin complex concentrate for breakthrough bleeding. [4]

**MetaRadar implication:** Safety signals should have a strong priority modifier. A "positive efficacy" article should not automatically receive a high overall score if it also contains a serious safety concern; the safety finding may become the dominant signal.

### 4. Regulatory decisions are high-impact signals

Regulatory events can directly change the treatment landscape.

The FDA approved Roctavian (valoctocogene roxaparvovec) in 2023 as the first FDA-approved gene therapy for adults with severe haemophilia A meeting its eligibility criteria. FDA reported that the mean ABR decreased from 5.4 at baseline to 2.6 bleeds/year after treatment and highlighted the need for monitoring of liver enzymes, infusion-related reactions and other risks. [8]

The EMA's Roctavian assessment provides an additional lesson: the agency described sustained factor VIII activity, reductions in bleeding and factor replacement use, but also required additional evidence because long-term safety and effectiveness data remained limited. The product is under additional monitoring and was granted conditional authorisation. [9]

Hemgenix (etranacogene dezaparvovec) is another important gene-therapy example. EMA describes it as a treatment for adults with severe or moderately severe haemophilia B without factor IX inhibitors and notes that its conditional authorisation requires additional evidence on long-term safety and effectiveness, including durability of response. The product information was updated in July 2026. [10]

**MetaRadar implication:** Regulatory approval, rejection, withdrawal, label change, safety warning, conditional authorisation, additional monitoring and post-authorisation evidence requirements should receive very high priority because they can alter treatment availability, medical interpretation and follow-up requirements.

### 5. The treatment landscape is moving beyond factor replacement

Haemophilia treatment has expanded from traditional factor VIII/IX replacement to non-factor therapies and gene therapy.

FDA approved Alhemo (concizumab) in December 2024 for routine prophylaxis in patients aged 12 years and older with haemophilia A with FVIII inhibitors or haemophilia B with FIX inhibitors. FDA reports that the phase 3 Explorer7 study included 133 participants and that the treatment arm had an estimated 86% reduction in treated ABR compared with no prophylaxis. [6]

The FDA orphan-drug database also records a July 31, 2025 expansion of Alhemo's US approval to haemophilia A and B populations without inhibitors in the specified severity categories. [11]

EMA's Alhemo assessment similarly describes use in haemophilia A/B with inhibitors and in severe haemophilia A or moderate-to-severe haemophilia B without inhibitors. [5]

ClinicalTrials.gov also demonstrates that the development lifecycle continues after initial trials. For example, the marstacimab extension study NCT05145127 is an open-label extension evaluating long-term safety, tolerability and efficacy after phase 3 studies, with a record update posted in April 2026. [12]

**MetaRadar implication:** Treatment-class, mechanism-of-action, route, dosing frequency, indication, inhibitor status and development phase should be structured fields. A new non-factor therapy or gene-therapy result may have greater competitive and strategic relevance than another routine factor-extension study.

### 6. Congresses and publications are lifecycle signals, not isolated news

A congress presentation can be the first place where important new trial data becomes visible. The same dataset may later appear in a peer-reviewed publication or regulatory submission.

Therefore, MetaRadar should detect and link:

`Clinical trial registry → congress abstract/presentation → company update → peer-reviewed publication → regulatory submission → approval/label change → long-term follow-up`

This prevents duplicate alerts and creates a development history.

For example, ClinicalTrials.gov records contain structured information about endpoints, study phase, intervention, population and status. [2][12] A congress report that names the same trial identifier should therefore be linked to that trial rather than classified as an unrelated article.

**MetaRadar implication:** Trial IDs (e.g., NCT numbers), drug names, sponsors, investigators, mechanisms, phase, endpoints and study populations should be used as entity-linking keys.

## Why is it relevant to haemophilia?

Haemophilia is a chronic bleeding disorder in which treatment decisions depend on maintaining haemostasis while limiting treatment burden and complications. The clinical relevance of a signal can therefore be judged using several dimensions:

1. **Bleeding control:** Does the signal change ABR or clinically important bleeding outcomes?
2. **Joint/musculoskeletal outcomes:** Does it affect joint bleeding, target joints, pain or long-term joint health?
3. **Patient-centred outcomes:** Does it improve quality of life, physical functioning or treatment burden?
4. **Safety:** Does it introduce or clarify serious risks such as thrombosis, hypersensitivity, liver toxicity or other clinically meaningful adverse events?
5. **Inhibitor status:** Does it affect patients with FVIII/FIX inhibitors or change the role of bypassing/non-factor therapies?
6. **Durability:** Particularly for gene therapy, does benefit persist over time?
7. **Treatment burden:** Does the therapy change dosing frequency, route of administration or need for ongoing factor replacement?
8. **Treatment landscape:** Does it introduce a new mechanism, modality or competitor?
9. **Regulatory status:** Does it change approval, indication, label, monitoring or access?
10. **Evidence strength:** Is the signal based on a randomized phase 3 trial, observational evidence, early phase research, a conference abstract or a company claim?

These dimensions make haemophilia signal prioritisation more clinically meaningful than simply counting media mentions.

## Why does MetaRadar need this?

MetaRadar needs Medical Affairs logic because volume is not the same as importance.

A haemophilia information stream could contain:

- 100 routine publications,
- 20 conference abstracts,
- 10 company pipeline updates,
- 5 trial-status changes,
- 2 safety signals,
- 1 regulatory decision.

The single regulatory or safety signal may be more important than dozens of routine publications.

MetaRadar therefore needs to transform raw information into an actionable signal:

**Source → Extraction → Evidence validation → Clinical impact → Priority → Routing → Action → Lifecycle tracking**

### Proposed signal schema

For each haemophilia signal, MetaRadar should extract:

- Disease: haemophilia A / haemophilia B / both
- Population: adults / adolescents / children
- Severity
- Inhibitor status
- Drug/product
- Sponsor/company
- Mechanism/class
- Trial identifier
- Trial phase
- Study design
- Comparator
- Primary endpoint
- Key secondary endpoints
- ABR and other bleeding outcomes
- Joint/target-joint outcomes
- Patient-reported outcomes
- Safety findings
- Regulatory event
- Evidence source type
- Evidence maturity
- Novelty
- Competitive impact
- Potential patient impact
- Recommended function
- Priority score
- Required action
- Linked previous signals

## What signals should MetaRadar detect?

### A. Clinical-development signals

- New phase 1/2/3 haemophilia trial
- Trial start, completion, suspension, termination or early stopping
- Primary endpoint change
- Recruitment/status change
- Positive or negative topline results
- Trial failure
- New subgroup analysis
- Long-term extension data
- Durability data
- New comparator data

### B. Efficacy signals

- Meaningful change in ABR
- Change in spontaneous bleeding
- Change in joint or target-joint bleeding
- Change in factor consumption
- Change in factor activity
- Achievement of clinically meaningful haemostatic targets
- Reduced rescue treatment

### C. Patient-outcome signals

- Quality-of-life improvement/deterioration
- Pain improvement/deterioration
- Physical-function improvement/deterioration
- Joint-health findings
- Treatment-burden changes
- Adherence/persistence findings

### D. Safety signals

- Serious adverse events
- Death
- Thrombosis/thromboembolism
- Thrombotic microangiopathy
- Hypersensitivity
- Liver toxicity
- Inhibitor development
- Unexpected immunogenicity
- New safety warning
- Safety-related trial halt

### E. Regulatory signals

- Approval
- Rejection
- Complete response letter or equivalent
- Label expansion/restriction
- Safety warning
- Conditional approval
- Additional monitoring
- Post-authorisation requirement
- Withdrawal
- Regulatory submission

### F. Scientific/congress signals

- New phase 3 data presented at ISTH/WFH/EHA
- Late-breaking haemophilia data
- New subgroup analysis
- New long-term follow-up
- First presentation of previously unavailable clinical data
- Guideline update
- Consensus statement

### G. Competitive/landscape signals

- New mechanism
- New non-factor therapy
- Gene-therapy development
- New route of administration
- Major dosing-frequency improvement
- Competitor trial success/failure
- Expansion into a new haemophilia population
- Major licensing/acquisition involving a haemophilia asset

## Which function should receive it?

MetaRadar should use function-specific routing rather than sending every signal to everyone.

| Signal type | Primary function | Secondary function(s) |
|---|---|---|
| Major clinical efficacy result | Medical Affairs | Clinical Development, Competitive Intelligence |
| Serious safety signal | Safety / Pharmacovigilance | Medical Affairs, Regulatory |
| Regulatory approval/rejection/label change | Regulatory Affairs | Medical Affairs, Market Access |
| New competitor therapy | Competitive Intelligence / Medical Affairs | Strategy, Clinical Development |
| New patient outcome/QoL evidence | Medical Affairs | Clinical Development, Market Access |
| Trial status change | Clinical Development | Medical Affairs, Competitive Intelligence |
| New congress data | Medical Affairs | Clinical Development, Competitive Intelligence |
| Guideline change | Medical Affairs | Regulatory, Market Access |
| Pricing/access evidence | Market Access | Medical Affairs, Strategy |

## What action might be required?

A priority classification should be tied to a specific action.

### High priority

**Possible actions:**

- Immediate Medical Affairs review
- Medical/scientific validation
- Safety or regulatory escalation
- Update competitor landscape
- Update evidence tracker
- Compare with existing standard of care
- Assess whether an internal scientific response is required
- Link to the relevant clinical programme
- Monitor for follow-up regulatory/publication evidence

### Medium priority

**Possible actions:**

- Expert review within a defined time window
- Add to evidence landscape
- Monitor subsequent publications/congress presentations
- Link to an existing trial/product
- Update the scientific knowledge base

### Low priority

**Possible actions:**

- Archive/index
- Keep for background intelligence
- No immediate escalation
- Deduplicate against existing information

## Proposed MetaRadar priority score

A practical starting model could be:

**Priority Score = Clinical Impact + Safety Impact + Regulatory Impact + Strategic/Competitive Impact + Evidence Maturity + Novelty + Patient Impact − Uncertainty/Duplication**

Suggested weighting:

| Dimension | Score |
|---|---:|
| Major clinical impact | 0–3 |
| Serious safety impact | 0–4 |
| Regulatory impact | 0–4 |
| Strategic/competitive impact | 0–3 |
| Patient outcome impact | 0–3 |
| Evidence maturity | 0–2 |
| Novelty | 0–2 |
| Uncertainty/limitations | 0 to −2 |
| Duplicate/previously known | 0 to −2 |

### Suggested classification

- **High:** 10+ or any automatic high-priority trigger
- **Medium:** 5–9
- **Low:** 0–4

These thresholds are proposed design rules for MetaRadar, not validated clinical scoring systems. They should be calibrated using real historical haemophilia signals and reviewed by Medical Affairs.

### Automatic High-Priority triggers

Regardless of the numerical score, MetaRadar should consider the following automatic escalation triggers:

1. Regulatory approval/rejection/withdrawal/major label change
2. New serious safety signal or safety warning
3. Trial termination for safety or clear efficacy failure
4. Clinically important evidence that materially changes benefit-risk
5. Major phase 3 result likely to change treatment strategy
6. New evidence of serious thrombosis/thrombotic microangiopathy or comparable clinically important risk
7. Gene-therapy durability or safety signal with potential long-term implications
8. Guideline change that materially changes standard-of-care recommendations

## 3-5 examples

### Example 1 — Major phase 3 efficacy signal

**Signal:** A phase 3 haemophilia trial reports a large reduction in treated ABR versus a relevant comparator.

**Evidence example:** HAVEN 3 reported 96–97% lower model-based treated ABR with emicizumab versus no prophylaxis in the randomized comparison. [3]

**Classification:** High if the result is new, robust and clinically meaningful.

**MetaRadar extraction:**
- Phase 3
- Haemophilia A
- Non-factor therapy
- ABR endpoint
- Comparator
- Effect size
- Statistical significance
- Safety

**Routing:** Medical Affairs + Clinical Development + Competitive Intelligence.

**Action:** Validate the result, compare with the current treatment landscape, link the result to the existing trial record and monitor for publication/regulatory consequences.

---

### Example 2 — Serious safety finding within an otherwise positive programme

**Signal:** A haemophilia therapy demonstrates efficacy but new thrombotic events or another serious safety concern emerges.

**Evidence example:** In HAVEN 1, thrombotic microangiopathy and thrombosis were observed in the context of high cumulative aPCC exposure during emicizumab treatment. [4]

**Classification:** High.

**MetaRadar rule:** A serious safety signal should override a purely efficacy-based classification.

**Routing:** Safety/PV + Medical Affairs + Regulatory.

**Action:** Immediate medical review, verify source and patient population, assess whether the event changes the benefit-risk interpretation, and monitor for regulatory action.

---

### Example 3 — Regulatory approval changes the treatment landscape

**Signal:** FDA approves a new haemophilia modality.

**Evidence example:** FDA approved Roctavian in 2023 for eligible adults with severe haemophilia A. [8]

**Classification:** High.

**Routing:** Regulatory + Medical Affairs + Market Access + Competitive Intelligence.

**Action:** Update treatment landscape, product/competitor database, evidence summaries and relevant strategic assessments.

---

### Example 4 — Conditional authorisation creates an ongoing evidence signal

**Signal:** EMA grants conditional authorisation but requires additional long-term evidence.

**Evidence example:** EMA describes Roctavian as conditionally authorised and states that additional evidence on long-term safety/effectiveness and registry data are required. [9]

**Classification:** High initially; subsequent routine follow-ups may be Medium unless they contain important new findings.

**MetaRadar rule:** Create a monitoring obligation:

`Conditional authorisation → required evidence → expected follow-up → new evidence → reassessment`

**Routing:** Medical Affairs + Regulatory.

**Action:** Track whether the required evidence is delivered and whether durability/safety findings alter the original benefit-risk interpretation.

---

### Example 5 — Congress publication/abstract linked to an existing trial

**Signal:** New phase 3 results are presented at ISTH/WFH/EHA.

**Classification:** Medium by default, but High if the presentation contains a major unexpected efficacy/safety/regulatory-relevant finding.

**MetaRadar rule:**

`If source = congress AND trial ID/product matches an existing trial → link to existing trial lifecycle rather than creating a completely independent signal.`

Then:

`If new data changes primary endpoint interpretation, safety profile, durability or competitive position → increase priority.`

**Routing:** Medical Affairs + Clinical Development + Competitive Intelligence.

**Action:** Compare against previous data, identify what is genuinely new, update the evidence timeline and watch for peer-reviewed publication or regulatory consequences.

## Red-Team checks for MetaRadar

MetaRadar should not trust a headline or company claim without checking the underlying evidence.

### Check 1 — “Positive results” is not enough

If an article says “positive phase 3 results,” the system should ask:

- What was the primary endpoint?
- What was the comparator?
- How large was the effect?
- Was it statistically significant?
- Was it clinically meaningful?
- What population was studied?
- What were the safety findings?

### Check 2 — Distinguish treated ABR from all-bleed ABR

ABR can be defined differently across studies. MetaRadar should preserve the exact endpoint definition instead of comparing numbers blindly. ClinicalTrials.gov records show that studies may separately define treated and all bleeding outcomes. [2]

### Check 3 — Do not treat company announcements as equivalent to peer-reviewed evidence

A company press release can be an important early signal, but it may contain less methodological detail than a full publication or regulatory review.

Recommended evidence hierarchy:

**Regulatory document / peer-reviewed full publication / trial registry → congress abstract/presentation → company announcement → secondary media**

This is a routing/validation hierarchy, not a statement that lower-level sources are useless.

### Check 4 — Check whether the signal is genuinely new

MetaRadar should compare:

- Trial ID
- Drug name
- Sponsor
- Patient population
- Endpoint
- Data cutoff
- Publication date
- Congress date

This reduces duplicate alerts.

### Check 5 — Separate statistical significance from clinical importance

A statistically significant change may not always represent a clinically meaningful patient benefit. Conversely, a clinically important finding may require careful interpretation if the study is small or exploratory.

### Check 6 — Gene therapy requires durability monitoring

For gene therapy, a one-time treatment creates a long-term evidence lifecycle. MetaRadar should monitor factor activity, bleeding outcomes, factor use, safety, liver-related monitoring, immunogenicity and durability over time.

EMA's Hemgenix and Roctavian assessments demonstrate why post-authorisation evidence can remain important after approval. [9][10]

## Recommended MetaRadar decision logic

A simplified decision tree could be:

```text
NEW HAEMOPHILIA SIGNAL
        |
        v
Is it genuinely new?
   |             |
  NO            YES
   |             |
Deduplicate      v
              Is there a serious safety/
              regulatory event?
                |          |
               YES         NO
                |           |
             HIGH           v
                       Is there major clinical/
                       patient/competitive impact?
                         |          |
                        YES         NO
                         |           |
                       HIGH          v
                              Is evidence scientifically
                              meaningful but not urgent?
                                |          |
                               YES         NO
                                |           |
                              MEDIUM       LOW
```

## Proposed implementation rules

### Rule 1 — Safety override

`IF serious safety signal = TRUE → priority = HIGH`

### Rule 2 — Regulatory override

`IF regulatory action materially changes indication, approval, restriction or safety → priority = HIGH`

### Rule 3 — Major phase 3 efficacy

`IF phase = 3 AND clinically meaningful efficacy improvement = TRUE → priority >= MEDIUM; HIGH if strategically significant`

### Rule 4 — Patient outcome

`IF meaningful QoL/joint/pain/physical-function outcome = TRUE → add patient-impact score`

### Rule 5 — New modality

`IF new mechanism OR gene therapy OR major route/dosing innovation = TRUE → add strategic-impact score`

### Rule 6 — Congress linkage

`IF congress signal matches existing trial/product → update lifecycle rather than create duplicate signal`

### Rule 7 — Evidence quality

`IF evidence source = regulatory review or peer-reviewed full publication → increase evidence-confidence score`

`IF source = company announcement only → require validation before assigning the highest confidence`

### Rule 8 — Uncertainty penalty

`IF small sample OR early phase OR short follow-up OR exploratory endpoint OR incomplete data → increase uncertainty / reduce confidence`

### Rule 9 — Longitudinal monitoring

`IF conditional approval OR gene therapy OR ongoing extension study → create follow-up monitoring task`

## Overall recommendation for MetaRadar

The most useful Medical Affairs contribution is not simply a list of haemophilia facts. It is a **clinically informed signal-classification layer**.

MetaRadar should answer five questions for every signal:

1. **What happened?**
2. **How strong is the evidence?**
3. **How clinically meaningful is it?**
4. **Who needs to know?**
5. **What should happen next?**

The final output should therefore look like:

> **Signal:** Phase 3 haemophilia therapy reports major reduction in treated ABR  
> **Evidence:** Phase 3 / defined endpoint / comparator / effect size  
> **Clinical impact:** High  
> **Patient impact:** Potentially high  
> **Strategic impact:** High  
> **Safety:** No major new signal / or specify concern  
> **Priority:** HIGH  
> **Route:** Medical Affairs + Clinical Development + Competitive Intelligence  
> **Action:** Validate → compare → link to trial lifecycle → monitor publication/regulatory outcome

This converts Medical Affairs expertise into an implementable MetaRadar workflow rather than a passive news-summary function.

## Sources

1. World Federation of Hemophilia (WFH). *Guidelines for the Management of Hemophilia, 3rd edition.*  
   https://wfh.org/article/now-published-the-wfh-guidelines-for-the-management-of-hemophilia-3rd-edition/

2. ClinicalTrials.gov. *NCT04161495 – Phase 3 study of efanesoctocog alfa in severe haemophilia A.* Endpoint definitions including annualized bleeding rates.  
   https://clinicaltrials.gov/study/NCT04161495

3. Mahlangu J, et al. *Emicizumab Prophylaxis in Patients Who Have Hemophilia A without Inhibitors.* New England Journal of Medicine.  
   https://www.nejm.org/doi/full/10.1056/NEJMoa1803550

4. Oldenburg J, et al. *Emicizumab Prophylaxis in Hemophilia A with Inhibitors.* New England Journal of Medicine.  
   https://www.nejm.org/doi/full/10.1056/NEJMoa1703068

5. European Medicines Agency (EMA). *Alhemo (concizumab) – EPAR.*  
   https://www.ema.europa.eu/en/medicines/human/EPAR/alhemo

6. U.S. Food and Drug Administration (FDA). *Drug Trials Snapshot: ALHEMO.*  
   https://www.fda.gov/drugs/drug-approvals-and-databases/drug-trials-snapshot-alhemo

7. U.S. FDA. *Alhemo (concizumab) clinical/risk review documents.*  
   https://www.accessdata.fda.gov/drugsatfda_docs/nda/2025/761315Orig1s000RiskR.pdf

8. U.S. FDA. *FDA Approves First Gene Therapy for Adults with Severe Hemophilia A – Roctavian.*  
   https://www.fda.gov/news-events/press-announcements/fda-approves-first-gene-therapy-adults-severe-hemophilia

9. European Medicines Agency (EMA). *Roctavian (valoctocogene roxaparvovec) – EPAR.*  
   https://www.ema.europa.eu/en/medicines/human/EPAR/roctavian

10. European Medicines Agency (EMA). *Hemgenix (etranacogene dezaparvovec) – EPAR.*  
    https://www.ema.europa.eu/en/medicines/human/EPAR/hemgenix

11. U.S. FDA. *Orphan Drug Designations and Approvals – concizumab/Alhemo.*  
    https://www.accessdata.fda.gov/scripts/opdlisting/oopd/detailedIndex.cfm?cfgridkey=663618

12. ClinicalTrials.gov. *NCT05145127 – Open-label extension study of marstacimab in haemophilia participants.*  
    https://clinicaltrials.gov/study/NCT05145127

### Source-quality note

The core clinical and regulatory conclusions above are based primarily on WFH, FDA, EMA, ClinicalTrials.gov and peer-reviewed NEJM evidence. Company announcements are appropriate as early signal sources but should be validated against trial-registry, peer-reviewed or regulatory evidence before assigning the highest confidence. Congress material should similarly be treated as an important early/lifecycle signal and linked to the underlying trial whenever possible.
