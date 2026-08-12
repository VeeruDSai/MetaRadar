# Haemophilia Evidence, Safety, Access & Red-Team

## MetaRadar Master Research Report

*Integrated from the three supplied research documents; repetitive
material consolidated while preserving distinct topics, evidence
limitations, operational rules, and references.*

HAEMOPHILIA EVIDENCE, SAFETY, ACCESS & RED-TEAM MetaRadar Master
Research Report Integrated from the three supplied research documents
--- consolidated to preserve unique points while removing repetitive
material Focus: Pharmacovigilance  Treatment Access & Reimbursement 
Clinical-Trial Evidence  MetaRadar Architecture  Red-Team Governance
Prepared as a detailed evidence-to-action framework. MetaRadar is
positioned as an intelligence and governance aid, not an autonomous
clinical or regulatory decision-maker.

Executive Summary Haemophilia intelligence is fragmented across
regulatory communications, safety databases, clinical trials, scientific
publications, congress abstracts, HTA/payer decisions, company
communications, registries and access reports. The three supplied
research documents converge on one central idea: MetaRadar should not
merely collect information; it should detect meaningful change, evaluate
evidence quality, connect the change to the correct product or trial
lifecycle, identify uncertainty and contradictions, prioritise the
signal, and route it to the appropriate human function. The integrated
operating chain is: Source → Entity → Signal → Evidence → Priority →
Function → Action → Lifecycle update. This creates one common
architecture across safety, access and clinical evidence rather than
three isolated monitoring systems. The report therefore separates four
layers: (1) domain intelligence --- what matters in haemophilia; (2)
evidence assessment --- how strong and applicable the information is;
(3) operational rules --- what MetaRadar should detect and do; and (4)
governance --- what automation must not decide without qualified human
review. 1. Scope, Objectives and Source Strategy The source documents
identify the same core evidence streams: regulatory communications,
product labels and safety updates, PubMed literature, congress
abstracts/posters/presentations, ClinicalTrials.gov, HTA and payer
decisions, government and haemophilia-organisation information, official
company announcements, patient/clinician access reports and
disease-specific safety registries. A congress abstract may be an early
signal, while a later publication, registry update, regulatory
assessment or post-marketing report may confirm, qualify or contradict
it. \[1--3\] Source authority must be recorded rather than assumed.
Regulators and authoritative haemophilia organisations are
high-authority sources; peer-reviewed literature provides scientific
evidence; registries provide lifecycle and trial-structure information;
congress evidence is often early and provisional; company and payer
sources may be highly useful but must be labelled for independence and
purpose; patient/clinician reports can identify access friction but
generally require corroboration for policy classification. 2. Safety
Signals and Pharmacovigilance A safety signal is information suggesting
a new or changed risk that requires investigation; it is not proof of
causality. EMA signal-management processes use spontaneous reports,
clinical studies and scientific literature, while FDA adverse-event
monitoring provides another important source of potential serious-risk
information. The haemophilia-specific material emphasises that rare
disease trials may miss rare or delayed events because of small,
selected populations and limited follow-up. \[1,4--8\] Haemophilia
safety surveillance must cover traditional factor products, bypassing
agents, non-factor therapies and AAV gene therapies. The
modality-specific risk profile matters: non-factor therapies can raise
thrombotic or immunogenicity concerns; AAV gene therapy creates
particular attention around immune responses, liver-related events,
vector/capsid effects and long-term durability; inhibitors and
neutralising antibodies remain important disease-specific surveillance
topics. Product quality defects, recalls and lot-specific problems also
require monitoring. \[2,3,9--12\] The source material also highlights
the importance of institutional memory. Historical safety problems
involving contaminated blood products demonstrate why haemophilia
requires specialised and continuous surveillance. This history should
inform governance and vigilance without turning historical experience
into proof of a new causal relationship. 2.1 Safety signal record ---
minimum evidence fields  Product/treatment modality and exact
indication.

Adverse event or event concept, seriousness and outcome.

Population, age/sex where relevant, disease subtype and inhibitor
status.

Exposure duration, dose and exposure-days where available.

Number of exposed patients and denominator.

Comparator or historical baseline where meaningful.

Evidence of clustering, disproportionality or repeated independent
reporting.

Source type, source authority, date and freshness.

Regulatory/clinical relevance and whether the event is already a known
risk.

Related product, trial, risk-management-plan and previous safety
records.

2.2 Detection rules  New adverse-event/product association.

Repeated independent reports of the same product-event combination.

Seriousness escalation: life-threatening, fatal, hospitalisation or
major intervention.

FDA/EMA or other competent-authority safety communication, warning,
label change or restriction.

Gene-therapy long-term safety or durability-related finding.

Safety data appearing in a congress abstract or publication before
formal regulatory action.

Clusters by product, lot, treatment centre, country, age group or
exposure period.

Inhibitor development or neutralising-antibody signals, including
atypical or early-exposure populations.

EUHASS, WFH or national registry updates that materially change the
safety picture.

2.3 Safety workflow and routing  Compare the new event with the
established safety profile.

Check whether the event is already known and whether the same underlying
case is reported elsewhere.

Verify denominator/exposure and assess whether reports are independent.

Increase priority when serious, unexpected, repeated, clustered or
regulator-confirmed.

Route to Pharmacovigilance/Drug Safety; add Medical Affairs, Clinical
Development or Regulatory Affairs as appropriate.  Where a trial is
ongoing, feed the signal back into protocol and trial-safety review.

Track subsequent label, RMP, regulatory or post-marketing actions.

2.4 Safety Red-Team tests  Correlation must not be converted into
causation.

A single case must not become a validated signal automatically.

Duplicate case reports must not become multiple independent events.

Known risk must be distinguished from a genuinely new risk.

Congress/abstract evidence must not be treated as equivalent to
peer-reviewed or regulatory confirmation.

Small denominators and random variation must be considered before
declaring a cluster.

Source independence and sponsor/funding relationships must be visible.

3.  Treatment Access and Reimbursement Access is a separate lifecycle
    event from regulatory approval. A therapy may be approved but not
    reimbursed, restricted to a narrow population, unavailable at
    suitable treatment centres, affected by supply problems, or
    inaccessible because of infrastructure, affordability, diagnostic or
    specialist requirements. The supplied research specifically
    distinguishes clinical success from access success. \[2,3,13--18\]
    Access monitoring should therefore cover both formal payer decisions
    and real-world delivery. Relevant systems include HTA bodies,
    national formularies, payer bulletins, procurement/tender
    information, patient-support programme terms, supply/distribution
    information, treatment-centre capacity and credible access reports.

3.1 Access fields  Country and subnational jurisdiction.

Effective date and review/expiry date.

Product and indication.

Disease subtype, inhibitor status and eligible population.

Treatment line and prior-treatment requirements.

Coverage status: approved, reimbursed, restricted, conditional, not
reimbursed or withdrawn.

Restrictions, prior authorisation and specialist-centre requirements.

Supply/distribution status and practical delivery requirements.

Source authority and policy version.

Whether the source describes intended access, commercial availability or
actual patient access.

3.2 Access signal classes  ACCESS_REIMBURSEMENT_EVENT --- positive,
negative, conditional or restricted payer/HTA decision.

RESTRICTED_REIMBURSEMENT --- eligibility narrowed by severity, age,
treatment history or other criteria.

SUPPLY_ACCESS_RISK --- shortage, manufacturing, distribution or
treatment-interruption risk.

GEOGRAPHIC_ACCESS_GAP --- material variation between countries/regions.

BUDGET_IMPACT_SIGNAL --- evidence of major economic consequences for
payers.

OUTCOME_BASED_ACCESS_MODEL --- payment linked to performance/durability.

REAL_WORLD_ACCESS_GAP --- approved treatment is not reaching intended
patients because of affordability/infrastructure or system barriers. 
ACCESS_SUPPORT --- manufacturer patient-support programme, kept distinct
from reimbursement.

3.3 Access-specific Red-Team controls  Approval ≠ reimbursement.

Commercial availability ≠ actual patient access.

Manufacturer support ≠ payer coverage.

One country's reimbursement decision must not be generalised to another
jurisdiction.

Current policy date and effective date must be checked.

Eligibility criteria must be extracted rather than inferred from the
product label alone.

Strong clinical evidence does not guarantee strong access.

4.  Clinical-Trial Evidence and Evidence Limitations Haemophilia is a
    rare disease, making conventional large randomised trials difficult.
    The supplied documents identify recurring limitations: small sample
    size, single-arm/open-label or non-randomised designs, historical
    controls, short follow-up, rare outcome events, heterogeneous
    baseline bleeding risk, different assays, different definitions of
    bleeding/treatment success, missing data, selective reporting,
    post-hoc subgroup analysis, limited representation of women/older
    adults/comorbidities/lower-resource populations, restricted evidence
    for haemophilia B or inhibitor populations, and reliance on
    surrogate or exploratory endpoints. \[19--25\] Modern therapies
    create additional evidence problems. Very low bleeding rates can
    make conventional comparisons difficult; patient-reported outcomes
    add clinically valuable but potentially subjective information; gene
    therapy raises long-term durability questions; and different
    laboratory assays can complicate cross-trial comparisons. The
    evidence layer must therefore capture the study design and
    uncertainty alongside the headline result.

The Claude research adds an important regulatory/HTA dimension: small
early studies and short follow-up can make lifetime extrapolation
unstable. The supplied examples include regulatory concern about
extrapolating phase 1/2 durability to later-stage claims, long-term
gene-therapy follow-up requirements, terminated long-term studies, and
the effect of limited sample/follow-up on HTA survival modelling.
\[26--31\] 4.1 Trial lifecycle that MetaRadar should connect Trial
registration → recruitment/status change → protocol amendment → interim
result → congress abstract/presentation → registry results → primary
publication → correction/retraction → regulatory review → long-term
follow-up → post-marketing/real-world evidence. The key principle is
lifecycle linkage: a later publication or abstract should update the
existing trial/product record rather than become a separate independent
evidence count. 4.2 Evidence-quality fields  Trial/registry identifier
and study phase.

Intervention, comparator and analysis population.

Sample size and dropout/loss-to-follow-up.

Endpoint definitions, measurement method and whether endpoints are
patient-important.

Follow-up duration and whether it is sufficient for the claimed
durability question.

Interim vs final status.

Evidence source: registry, abstract, peer-reviewed paper, regulator,
company or commentary.

Population applicability: age, sex, subtype, inhibitor status, prior
treatment and geography.

Funding/sponsor relationship and independence.

Contradictions with earlier or later evidence.

4.3 Clinical-evidence signals  TRIAL_LIFECYCLE_CHANGE --- recruitment,
completion, suspension, termination or withdrawal.

NEW_CLINICAL_EVIDENCE --- new primary/secondary results.

ENDPOINT_CHANGE --- protocol or analysis changes that alter
interpretation.

PROMISING_LOW_MATURITY_EVIDENCE --- positive but small/short or
otherwise immature evidence.

LONG_TERM_DURABILITY_UPDATE --- meaningful new long-term follow-up.

CONGRESS_TO_PUBLICATION_UPDATE --- preliminary evidence later
confirmed/qualified by publication.

EVIDENCE_CONTRADICTION --- materially different efficacy, safety or
durability result.

POPULATION_LIMITATION --- evidence restricted to a subgroup and not
generalisable automatically.

ENDPOINT_COMPARABILITY_ISSUE --- studies use materially different
outcome definitions/measurement.

4.4 Evidence score as a prioritisation aid One supplied framework
proposes an Evidence Priority Score (0--100): +25
regulatory/peer-reviewed source; +20 clinically important new outcome;
+15 long-term follow-up; +15 evidence contradicting a prior result; +10
new population/indication; +10 trial-status change; +5 major congress
presentation. Suggested uncertainty penalties include −10 for a very
small cohort, −10 for short follow-up when durability is the question,
−10 for abstract-only evidence, and −10 for non-comparable endpoints.
This is a prioritisation aid, not a statistical measure of clinical
truth. \[2\] 5. Cross-Topic Intelligence: Where Signals Intersect The
strongest unique insight across the three documents is that safety,
access and evidence should not operate as isolated classifiers. One
event can affect multiple functions. For example, a durability shortfall
may simultaneously become an evidence-quality signal, a
safety-monitoring concern and a reimbursement/risk-sharing trigger. The
system

should therefore support linked records across functions. \[3\] A
practical cross-topic object is: Signal → Source type → Modality →
Product/Trial entity → Population → Evidence tier → Priority → Function
routing → Linked records → Human review → Lifecycle update. Congress
evidence should be ingested as provisional rather than discarded until
publication. In a low-volume field, congress data can precede formal
literature and may be the first indication of a trial-lifecycle change.
Confidence should start lower and be upgraded when peer-reviewed
publication, registry results or regulatory documentation confirm or
qualify the finding. \[2,3\] 6. MetaRadar Operational Data Model A
strong record should answer: What changed? Which product/trial/programme
is affected? Which haemophilia population? Where? How authoritative is
the source? Is evidence preliminary or confirmed? What previous records
are connected? Is there contradictory evidence? Which function owns the
response? What action and deadline are required? \[2\] Recommended core
fields: product/modality; disease subtype; inhibitor status; population;
event/endpoint; source type; source authority; jurisdiction;
publication/congress date; registry identifier; evidence tier;
comparator; denominator; seriousness; actionability; confidence;
freshness; related records; human-review status; evidence gap; lifecycle
stage; review deadline; final decision and rationale. 7. Priority,
Confidence and Uncertainty The supplied operational research proposes a
transparent priority formula: Priority = 0.25 novelty + 0.20
seriousness/actionability + 0.15 source authority + 0.15 evidence
strength + 0.10 population relevance + 0.10 geographic/access impact +
0.05 freshness. Components can be normalised from 0--100. This should be
treated as a triage mechanism, not as a validated clinical score. \[2\]
An uncertainty penalty should be applied when the denominator is
missing, the source is preliminary, the population is unclear, sources
conflict, the event cannot be independently verified, the trial record
is incomplete, or the jurisdiction/effective date is missing. Priority
Typical trigger Escalation CRITICAL Regulator-confirmed serious safety
risk; major supply interruption; major contradiction affecting
safety/development Immediate human review HIGH Serious/repeated safety
signal; major reimbursement restriction; major long-term evidence; major
trial result Rapid functional review MEDIUM Limited new evidence;
congress abstract; trial-status update; non-critical access change;
known-risk confirmation Routine expert review LOW Duplicate/background
information without lifecycle impact Monitor / no automatic escalation
8. Master Red-Team Framework The Red-Team layer asks how MetaRadar could
generate a confident but unsafe conclusion. The three source documents
provide overlapping checks; these are consolidated below so each failure
mode appears once but captures all the unique tests. 1. Causality error
Adverse-event mention → proof of causation. Require causality assessment
and preserve uncertainty. 2. Duplicate counting Same case/abstract/press
release/publication → multiple independent events. Link records and
deduplicate. 3. Denominator blindness Risk percentage or cluster
interpreted without exposure denominator/exposure-days. Block
confirmation when denominator is absent.

4.  Population mismatch Evidence from haemophilia A, non-inhibitor
    patients or adults generalised to haemophilia B, inhibitor
    populations or children. Check applicability fields.
5.  Endpoint mismatch Different bleeding definitions, assays, follow-up
    or outcome measures compared as if identical.
6.  Surrogate overclaim Factor activity or another surrogate treated as
    proof of patient-important benefit without sufficient support.
7.  Small-sample overconfidence Very small cohort assigned high
    certainty. Apply evidence-maturity/uncertainty penalty.
8.  Short-follow-up / durability error Early gene-therapy data
    interpreted as lifelong durability. Require explicit
    follow-up-duration check.
9.  Preliminary-evidence error Congress abstract, preprint or press
    release treated as final evidence. Label evidence maturity.
10. Source-independence error Company statement treated as independent
    confirmation. Capture sponsor/funding relationship.
11. Stale-information error Old label, reimbursement rule or trial
    status used after a newer authoritative update.
12. Negative-evidence omission Terminated, withdrawn, unpublished or
    missing-result trials ignored. Search for negative/disconfirming
    evidence.
13. Approval-access error Marketing authorisation interpreted as
    reimbursement or actual patient access.
14. Jurisdiction error A payer decision in one country/general health
    system applied elsewhere.
15. Lifecycle disconnection Publication, congress result or registry
    update not linked to the existing product/trial record.
16. Endpoint/population-change blindness Protocol amendment, sample-size
    change, analysis-population change or endpoint change missed.
17. Statistical-vs-clinical significance error Statistical significance
    treated as automatically clinically meaningful.
18. Contradiction blindness System reports a strong positive/safety
    claim without actively searching for conflicting evidence.
19. Governance bypass Automated system diagnoses, establishes causality,
    changes treatment, makes regulatory submissions or makes high-impact
    decisions without qualified human review. Required contradiction
    search for high-impact claims

Contradictory publications and independent replication failures.

Regulatory warnings, label changes or safety assessments.

Trial withdrawals, terminations, protocol changes and missing results.

Reimbursement exclusions, restrictions and supply constraints.

Different outcomes in underrepresented populations.

Registry--publication discrepancies.

Changes in sponsor/company claims versus authoritative records.

9.  Signal Routing and Actions Signal Primary function Secondary
    function(s) Core action Serious adverse event / possible cluster
    Pharmacovigilance Medical, Regulatory Validate, assess
    causality/seriousness, check denominator, escalate Regulator warning
    / label / recall Regulatory Affairs Safety, Medical, Quality, Supply
    Assess regulatory impact and product handling Reimbursement / HTA
    decision Market Access / HEOR Medical, Commercial, Policy Map
    coverage, restrictions, evidence gaps Supply interruption / shortage
    Supply Chain / Quality Patient Services, Regulatory Assess treatment
    continuity and mitigation Trial design/status change Clinical
    Development Biostatistics, Medical Writing, Regulatory Assess
    evidence maturity, timelines and risk Congress / publication Medical
    / Scientific Intelligence Clinical Development, PV Capture early
    evidence and link lifecycle Contradiction / missing result /
    overclaim Evidence Governance / Red-Team Medical, Statistics,
    Compliance Block unsupported conclusion; adjudicate
10. End-to-End MetaRadar Workflow STEP 1 --- Detect Ingest authoritative
    and relevant evidence streams; identify changed entities and
    candidate signals. STEP 2 --- Triage Assign signal class, initial
    priority, evidence tier, responsible function and escalation
    threshold. STEP 3 --- Verify Retrieve primary source; confirm
    product, indication, subtype, inhibitor status, population, sample
    size, jurisdiction, effective date and endpoint. STEP 4 ---
    Deduplicate Link identical underlying cases, trials, abstracts,
    publications and regulatory events. STEP 5 --- Assess evidence
    Evaluate design, denominator, comparator, follow-up, endpoint,
    source authority, independence and applicability. STEP 6 ---
    Contradiction search Actively search for disconfirming or qualifying
    evidence. STEP 7 --- Cross-link lifecycle Attach the signal to
    existing product/trial/access/safety records. STEP 8 --- Prioritise
    Apply the transparent priority model and uncertainty penalties. STEP
    9 --- Route Send to the responsible function and secondary
    stakeholders.

STEP 10 --- Human adjudication Require qualified review for causal,
clinical, regulatory and high-impact conclusions. STEP 11 --- Action
Create the appropriate safety review, trial-risk log, evidence map,
payer update, supply workflow or Red-Team memo. STEP 12 --- Close the
loop Record decision, rationale, sources reviewed, reviewer, source
version, follow-up question and re-check date. STEP 13 --- Lifecycle
update When later evidence confirms, qualifies or refutes the signal,
update the same record rather than creating an isolated conclusion. 11.
Integrated MetaRadar Examples These examples combine the unique
operational examples from the source documents without repeating the
same scenario. A. Safety cluster with regulator involvement Several
reports and a congress abstract describe thrombosis after a non-factor
therapy while a regulator adds monitoring language. Match
product/event/time window/population/exposure; deduplicate; check
denominator; search label/regulatory sources; prioritise as
High/Critical if serious, clustered or regulator-confirmed; route to
Pharmacovigilance + Regulatory Affairs; do not automatically assign
causality. B. Restricted reimbursement plus patient-support programme A
payer narrows coverage and the manufacturer announces support. Classify
the payer event as restricted reimbursement and the manufacturer
programme as access support. Store jurisdiction, effective date,
eligible population and policy version separately. Do not classify the
therapy as broadly accessible merely because support exists. C. Positive
congress abstract vs small single-arm registry A congress abstract
reports reduced bleeding but the registry shows a small single-arm
exploratory study. Link the abstract to the registry; compare endpoint,
n, analysis population, follow-up and design; classify as preliminary;
route to Clinical Development, Statistics and Medical Writing. D. Trial
termination while company messaging remains positive A registry changes
to terminated or results remain absent while a company webpage continues
positive programme messaging. Flag the lifecycle discrepancy, check why
the study stopped, search for missing/negative evidence, and prevent an
unqualified success classification. E. Generalisation failure A study in
previously untreated haemophilia A is used to support a statement
covering all haemophilia, including B and inhibitor populations. Compare
inclusion criteria with claim scope; flag subtype, inhibitor, age, sex,
geography and treatment-history mismatch; narrow the claim to the
studied population. F. Durability shortfall linked to reimbursement New
long-term data show a durability decline relevant to an outcomes-based
agreement. Link the new evidence to the original evidence-gap record and
reimbursement contract; recalculate priority; route to Clinical
Development, HEOR, Market Access and Red-Team. G. Terminated long-term
safety study A post-marketing study stops early because of a
licensing/business issue before its planned exposure target. Do not
treat termination as closure. Flag the resulting safety-data shortfall
as an open monitoring gap and set a re-check/alternative

evidence plan. H. Registry-publication discrepancy A paper reports a
different endpoint/population than the registry. Trigger an
evidence-quality review, preserve both records, document the discrepancy
and require human adjudication before using the result in a high-impact
claim. 12. Human Review and Governance Boundaries  MetaRadar may detect,
classify, prioritise, route and document information.

It should not diagnose patients.

It should not independently establish drug-event causality.

It should not change treatment.

It should not make regulatory submissions autonomously.

It should not make high-impact clinical, regulatory, reimbursement or
safety decisions without qualified human review.

Human reviewers should be visible in the record, with decision rationale
and evidence version retained.

High-impact safety clusters, regulator actions, gene-therapy durability
claims, major access restrictions and major evidence contradictions
should require explicit human adjudication. 13. Consolidated MetaRadar
Rulebook 1. IF a haemophilia product + serious/novel adverse event
appears, THEN create SAFETY_SIGNAL_CANDIDATE, check
duplicates/denominator, increase priority and route to
Pharmacovigilance. 2. IF a competent authority issues a safety
warning/label change, THEN create REGULATORY_SAFETY_SIGNAL and route to
Regulatory Affairs + Safety. 3. IF repeated independent reports support
the same product-event combination, THEN increase confidence/priority
only after checking that the reports are truly independent. 4. IF a
therapy is approved but reimbursement is absent/restricted, THEN
classify separately as APPROVED_NOT_REIMBURSED or
RESTRICTED_REIMBURSEMENT. 5. IF a manufacturer launches access support,
THEN classify ACCESS_SUPPORT separately from reimbursement.

6.  IF supply interruption could interrupt treatment, THEN create
    SUPPLY_ACCESS_RISK and escalate to Supply Chain + relevant
    clinical/access functions.

7.  IF a trial status, protocol, endpoint or sample size changes, THEN
    update TRIAL_LIFECYCLE_CHANGE and link all associated evidence.

8.  IF evidence is small, short, single-arm, abstract-only or uses
    non-comparable endpoints, THEN reduce evidence maturity and apply
    uncertainty penalties.

9.  IF a congress abstract later becomes a publication, THEN link the
    records and upgrade evidence maturity rather than counting two
    independent findings.

10. IF new evidence contradicts a prior result, THEN create
    EVIDENCE_CONTRADICTION and require statistical/clinical review.

11. IF a high-impact claim is detected, THEN launch a contradiction
    search before allowing a strong automated label such as
    safe/effective/superior/cost-effective.

12. IF a study population differs from the proposed claim, THEN block
    generalisation until applicability is reviewed.

13. IF an authoritative newer source conflicts with an old record, THEN
    mark the old record stale and update the lifecycle.

14. IF a trial is terminated or results remain missing after a plausible
    reporting period, THEN trigger transparency review; do not infer
    failure.

15. IF gene-therapy durability is claimed, THEN require explicit
    follow-up duration and long-term evidence assessment.

16. IF a signal crosses safety/access/evidence boundaries, THEN fan it
    out to linked records and relevant functions rather than creating
    disconnected alerts.

17. IF a high-impact decision is involved, THEN require qualified human
    adjudication and retain rationale/source versions.

18. Consolidated References References below are consolidated from the
    three supplied research documents. Repeated references have been
    merged rather than listed multiple times. The numbering is for
    navigation in this report; the MetaRadar rules themselves are
    proposed design recommendations, not validated regulatory or
    clinical algorithms.

19. World Federation of Hemophilia (WFH). Treatment and Care.
    https://wfh.org/treatment-and-care/

20. World Federation of Hemophilia. WFH statement on recent developments
    related to hemophilia therapies. 2025.
    https://wfh.org/article/wfh-statement-on-recent-developments-related-to-hemophilia-therapies/

21. World Federation of Hemophilia. Global Policy and Access
    Summit 2025. https://wfh.org/gpas2025/

22. World Federation of Hemophilia. Critical juncture in hemophilia
    treatment: global organizations issue urgent call to action. 2025.
    https://wfh.org/article/critical-juncture-in-hemophilia-treatment-global-organizations-issue-urgent-call-to-action/

23. World Federation of Hemophilia. 2025 Annual Report released. 2026.
    https://wfh.org/article/wfh-2025-annual-report-released/

24. European Medicines Agency. Signal management.
    https://www.ema.europa.eu/en/human-regulatory-overview/post-authorisation/pharmacovigilance-post-authorisation/signal-manage
    ment

25. European Medicines Agency. PRAC recommendations on safety signals.
    https://www.ema.europa.eu/en/human-regulatory-overview/post-authorisation/pharmacovigilance-post-authorisation/signal-manage
    ment/prac-recommendations-safety-signals

26. European Medicines Agency. Pharmacovigilance overview.
    https://www.ema.europa.eu/en/human-regulatory-overview/pharmacovigilance-overview

27. European Medicines Agency. Human medicines --- EMA Annual
    Report 2025.
    https://www.ema.europa.eu/assets/en/annual-report/2025/human-medicines/index.html

28. U.S. FDA. FDA Adverse Event Reporting System / AEMS (FAERS).
    https://www.fda.gov/drugs/fdas-adverse-event-reporting-system-faers

29. U.S. FDA. Human Gene Therapy for Hemophilia: Guidance for
    Industry. 2020.
    https://www.fda.gov/regulatory-information/search-fda-guidance-documents/human-gene-therapy-hemophilia

30. U.S. FDA. Long Term Follow-up After Administration of Human Gene
    Therapy Products: Guidance for Industry. 2020.
    https://www.fda.gov/regulatory-information/search-fda-guidance-documents/long-term-follow-after-administration-human-gene-thera
    py-products

31. U.S. FDA. Postapproval Methods to Capture Safety and Efficacy Data
    for Cell and Gene Therapy Products. Draft Guidance, 2025.
    https://www.fda.gov/regulatory-information/search-fda-guidance-documents/postapproval-methods-capture-safety-and-efficacy-data
    -cell-and-gene-therapy-products

32. FDA. FDA Approves First Gene Therapy for Adults with Severe
    Hemophilia A.
    https://www.fda.gov/news-events/press-announcements/fda-approves-first-gene-therapy-adults-severe-hemophilia

33. FDA. FDA Approves Novel Treatment for Hemophilia A or B, with or
    without Factor Inhibitors. 2025.
    https://www.fda.gov/news-events/press-announcements/fda-approves-novel-treatment-hemophilia-or-b-or-without-factor-inhibitors

34. Peyvandi F, Garagiola I, Mannucci PM. Post-authorization
    pharmacovigilance for hemophilia in Europe and the USA: Independence
    and transparency are keys. Blood Reviews. 2021.
    https://pubmed.ncbi.nlm.nih.gov/33810898/

35. DiMichele DM, Blanchette V, Berntorp E. Clinical trial design in
    haemophilia. Haemophilia. 2012.
    https://pubmed.ncbi.nlm.nih.gov/22726077/

36. Safety surveillance in haemophilia and allied disorders. PubMed.
    https://pubmed.ncbi.nlm.nih.gov/27001233/

37. The current state of adverse event reporting in hemophilia. PubMed.
    https://pubmed.ncbi.nlm.nih.gov/28013565/

38. Fischer K, Lassila R, Peyvandi F, et al. Inhibitor development in
    nonsevere hemophilia: data from the EUHASS registry. Research and
    Practice in Thrombosis and Haemostasis. 2025.
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12178916/

39. EUHASS overview. PubMed. https://pubmed.ncbi.nlm.nih.gov/21193110/

40. Ozelo MC, Chowdary P, Young G, et al. New Treatment in Haemophilia:
    Challenges, Controversies and Uncertainties. Haemophilia.

41. https://pubmed.ncbi.nlm.nih.gov/41988942/

42. Building safeguards for gene therapy in haemophilia. The Lancet
    Haematology. 2026.
    https://www.thelancet.com/journals/lanhae/article/PIIS2352-3026(26)00008-6/abstract

43. EAHAD 2026 Congress Abstracts. Haemophilia, 32(S1).
    https://onlinelibrary.wiley.com/doi/abs/10.1111/hae.70195

44. World Federation of Hemophilia. Guidelines for the Management of
    Hemophilia, 3rd edition.
    https://www1.wfh.org/publications/files/pdf-1863.pdf

45. International Society on Thrombosis and Haemostasis (ISTH).
    https://www.isth.org/

46. European Association for Haemophilia and Allied Disorders (EAHAD).
    https://www.eahad.org/

47. ClinicalTrials.gov. https://clinicaltrials.gov/

48. PubMed. Challenges of defining reliable clinical surrogate end
    points in haemophilia trials: a critical review. PMID 19543078.
    https://pubmed.ncbi.nlm.nih.gov/19543078/

49. PubMed. Hemophilia trials in the twenty-first century: Defining
    patient important outcomes. PMID 31011702.
    https://pubmed.ncbi.nlm.nih.gov/31011702/

50. PubMed. Outcome measures in hemophilia: current and future
    perspectives. PMID 38861342.
    https://pubmed.ncbi.nlm.nih.gov/38861342/

51. PubMed. Health technology assessment for gene therapies in
    haemophilia. PMID 35075731.
    https://pubmed.ncbi.nlm.nih.gov/35075731/

52. PubMed. Hemophilia Gene Therapy Value Assessment: Methodological
    Challenges and Recommendations. PMID 34711363.
    https://pubmed.ncbi.nlm.nih.gov/34711363/

53. PubMed. Gene therapy in the treatment of hemophilia A: a systematic
    review and meta-analysis. PMID 41709782.
    https://pubmed.ncbi.nlm.nih.gov/41709782/

54. PubMed. 2025 Clinical Trials Update on Hemophilia, VWD, and Rare
    Inherited Bleeding Disorders. PMID 39901862.
    https://pubmed.ncbi.nlm.nih.gov/39901862/

55. PubMed. Gene Therapy of Haemophilia: Current Status and Future
    Directions. PMID 41702383. https://pubmed.ncbi.nlm.nih.gov/41702383/

56. Mahlangu J. Haemophilia and access to gene therapy.
    eBioMedicine. 2025.
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12019289/

57. Recent Advances in Gene Therapy for Hemophilia. 2025.
    https://pmc.ncbi.nlm.nih.gov/articles/PMC12423543/

58. Treating Hemophilia: The Impact of New Gene Therapies. MMIT. 2024.
    https://www.mmitnetwork.com/thought-leadership/treating-hemophilia/

59. UKHCDO gene therapy taskforce guidance.
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11780224/

60. Genentech. Access To Hemophilia A Medicine.
    https://www.gene.com/patients/access-to-hemophila-a-medicine

61. Hermans C. Haemophilia gene therapy: experiences and lessons from
    treated patients. 2022.
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8981926/

62. Leebeek FWG, Miesbach W. Gene therapy for hemophilia: a review on
    clinical benefit, limitations, and remaining issues. Blood. 2021.
    https://ashpublications.org/blood/article/138/11/923/476350/

63. ClinicalTrials.gov. Long-Term Follow-Up Study of Haemophilia B
    Patients Who Have Undergone Gene Therapy (FLT180a), NCT03641703.
    https://clinicaltrials.gov/study/NCT03641703

64. ClinicalTrials.gov. Post-Marketing Safety Study Following Long-Term
    Prophylactic Optivate Treatment, NCT01811875.
    https://clinicaltrials.gov/study/NCT01811875

65. ASGCT Patient Education. Hemophilia --- Cell & Gene Therapy.
    https://patienteducation.asgct.org/understanding-cell-gene-therapy/conditions-treated/blood-disorders/hemophilia

66. A 360-degree perspective on AAV-based gene therapy for
    haemophilia. 2024.
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11092086/

67. Impact of limited sample size and follow-up on single event survival
    extrapolation for HTA: a simulation study. BMC Medical Research
    Methodology. 2021.
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8684239/

68. Value of information methods to design a clinical trial in a small
    population: haemophilia A example.
    https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5806391/ Reference and
    synthesis note This master report was constructed from the three
    supplied research documents. Repeated concepts were merged into a
    single stronger rule; unique examples and operational details were
    retained where they added distinct value. Where a point in the
    supplied documents was presented as a proposed MetaRadar rule rather
    than an established clinical/regulatory standard, it is explicitly
    framed as a design recommendation. Claims requiring current status
    should be rechecked against the latest authoritative source before
    external professional use.
