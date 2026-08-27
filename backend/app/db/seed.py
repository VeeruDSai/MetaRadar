import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import select, delete, update
from app.db.session import async_session_factory
from app.models import (
    Company,
    Asset,
    Development,
    Source,
    LifecycleEvent,
    Confluence,
    Signal,
    Contradiction,
    WatchItem,
    ScoringWeights,
    CalibrationFeedback,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


async def seed_data():
    async with async_session_factory() as session:
        print("[SEED] Seeding MetaRadar reference and synthetic landscape data...")

        # 1. Remap and clean up legacy / deprecated source IDs
        from app.models import RawSignalBronze, SourceHealthLog
        remap = {
            "clinicaltrials": "clinical_trials",
            "openfda": "fda",
            "ema_rss": "ema",
        }
        for old_id, new_id in remap.items():
            await session.execute(update(Signal).where(Signal.source_id == old_id).values(source_id=new_id))
            await session.execute(update(LifecycleEvent).where(LifecycleEvent.source_id == old_id).values(source_id=new_id))
            await session.execute(update(RawSignalBronze).where(RawSignalBronze.source_id == old_id).values(source_id=new_id))
            await session.execute(update(SourceHealthLog).where(SourceHealthLog.source_id == old_id).values(source_id=new_id))

        legacy_source_ids = list(remap.keys())
        await session.execute(delete(Source).where(Source.source_id.in_(legacy_source_ids)))
        await session.flush()

        # 2. Canonical Data Sources (All 8 registered pipeline connectors)
        sources_data = [
            {
                "source_id": "pubmed",
                "name": "PubMed MEDLINE (E-Utilities)",
                "freshness_class": "batch",
                "syndication_group": "Literature",
                "status": "active",
            },
            {
                "source_id": "clinical_trials",
                "name": "ClinicalTrials.gov API v2",
                "freshness_class": "near_real_time",
                "syndication_group": "Trial Registries",
                "status": "active",
            },
            {
                "source_id": "fda",
                "name": "openFDA Drugs & Adverse Events",
                "freshness_class": "delayed",
                "syndication_group": "Regulatory",
                "status": "active",
            },
            {
                "source_id": "ema",
                "name": "European Medicines Agency",
                "freshness_class": "delayed",
                "syndication_group": "Regulatory",
                "status": "active",
            },
            {
                "source_id": "newsapi",
                "name": "NewsAPI Industry Feed",
                "freshness_class": "near_real_time",
                "syndication_group": "Press / Media",
                "status": "active",
                "quota_remaining": 100,
            },
            {
                "source_id": "fierce_pharma",
                "name": "Fierce Pharma RSS",
                "freshness_class": "near_real_time",
                "syndication_group": "Press / Media",
                "status": "active",
            },
            {
                "source_id": "biopharma_dive",
                "name": "BioPharma Dive RSS",
                "freshness_class": "near_real_time",
                "syndication_group": "Press / Media",
                "status": "active",
            },
            {
                "source_id": "et_pharma",
                "name": "ET Pharma (India)",
                "freshness_class": "near_real_time",
                "syndication_group": "Press / Media",
                "status": "active",
            },
        ]
        for s in sources_data:
            existing = await session.get(Source, s["source_id"])
            if not existing:
                session.add(Source(**s))
            else:
                existing.name = s["name"]
                existing.freshness_class = s["freshness_class"]
                existing.syndication_group = s["syndication_group"]
                existing.status = s["status"]
        await session.flush()

        # 3. Companies
        companies_data = [
            {"company_id": "novo-nordisk", "name": "Novo Nordisk", "is_novo_nordisk": True},
            {"company_id": "csl-behring", "name": "CSL Behring", "is_novo_nordisk": False},
            {"company_id": "biomarin", "name": "BioMarin", "is_novo_nordisk": False},
            {"company_id": "pfizer", "name": "Pfizer", "is_novo_nordisk": False},
            {"company_id": "roche", "name": "Roche / Genentech", "is_novo_nordisk": False},
        ]
        for c in companies_data:
            existing = await session.get(Company, c["company_id"])
            if not existing:
                session.add(Company(**c))
        await session.flush()

        # 4. Assets
        assets_data = [
            {
                "asset_id": "hemgenix",
                "brand_name": "Hemgenix",
                "generic_name": "etranacogene dezaparvovec",
                "company_id": "csl-behring",
                "mechanism": "AAV5 vector delivering Padua variant Factor IX gene",
                "modality": "Gene Therapy",
                "indication": "Haemophilia B",
                "approval_status": "Approved",
                "approval_date": "2022-11-22",
                "jurisdiction": "FDA / EMA",
            },
            {
                "asset_id": "roctavian",
                "brand_name": "Roctavian",
                "generic_name": "valoctocogene roxaparvovec",
                "company_id": "biomarin",
                "mechanism": "AAV5 vector delivering B-domain deleted Factor VIII gene",
                "modality": "Gene Therapy",
                "indication": "Haemophilia A",
                "approval_status": "Approved",
                "approval_date": "2023-06-29",
                "jurisdiction": "FDA / EMA",
            },
            {
                "asset_id": "hympavzi",
                "brand_name": "Hympavzi",
                "generic_name": "marstacimab-hncq",
                "company_id": "pfizer",
                "mechanism": "Anti-tissue factor pathway inhibitor (anti-TFPI) mAb",
                "modality": "Monoclonal Antibody",
                "indication": "Haemophilia A and B without inhibitors",
                "approval_status": "Approved",
                "approval_date": "2024-10-11",
                "jurisdiction": "FDA",
            },
            {
                "asset_id": "alhemo",
                "brand_name": "Alhemo",
                "generic_name": "concizumab",
                "company_id": "novo-nordisk",
                "mechanism": "Anti-TFPI humanized monoclonal antibody",
                "modality": "Monoclonal Antibody",
                "indication": "Haemophilia A and B with inhibitors",
                "approval_status": "Approved",
                "approval_date": "2023-03-21",
                "jurisdiction": "Health Canada / Japan / EU",
            },
            {
                "asset_id": "mim8",
                "brand_name": "Mim8",
                "generic_name": "Mim8 bispecific antibody",
                "company_id": "novo-nordisk",
                "mechanism": "Next-generation Factor VIII-mimetic bispecific antibody (FIXa/FX)",
                "modality": "Bispecific Antibody",
                "indication": "Haemophilia A with and without inhibitors",
                "approval_status": "Investigational (Phase III FRONTIER)",
                "approval_date": None,
                "jurisdiction": "Global Trials",
            },
        ]
        for a in assets_data:
            existing = await session.get(Asset, a["asset_id"])
            if not existing:
                session.add(Asset(**a))

        await session.flush()

        # 5. Canonical Developments
        dev1_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        dev2_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
        dev3_id = uuid.UUID("33333333-3333-3333-3333-333333333333")

        dev1 = await session.get(Development, dev1_id)
        if not dev1:
            dev1 = Development(
                development_id=dev1_id,
                title="Haemophilia A Long-Term Factor VIII Expression & Durability",
                disease="haemophilia_a",
                asset_id="roctavian",
                company_id="biomarin",
                current_stage="Phase III Long-term Follow-up",
            )
            session.add(dev1)

        dev2 = await session.get(Development, dev2_id)
        if not dev2:
            dev2 = Development(
                development_id=dev2_id,
                title="Subcutaneous Anti-TFPI Prophylaxis Landscape in Haemophilia B",
                disease="haemophilia_b",
                asset_id="alhemo",
                company_id="novo-nordisk",
                current_stage="Approved (Inhibitors) / Phase III Expansion",
            )
            session.add(dev2)

        dev3 = await session.get(Development, dev3_id)
        if not dev3:
            dev3 = Development(
                development_id=dev3_id,
                title="Next-Generation FVIII-Mimetic Subcutaneous Hemostasis",
                disease="haemophilia_a",
                asset_id="mim8",
                company_id="novo-nordisk",
                current_stage="Phase III FRONTIER Readouts",
            )
            session.add(dev3)

        await session.flush()

        # 6. Lifecycle Events
        await session.execute(delete(LifecycleEvent))
        session.add_all([
            LifecycleEvent(
                development_id=dev1_id,
                source_id="clinical_trials",
                stage="Phase III 5-Year Data Readout",
                notes="5-year post-infusion data presented at congress showing steady baseline factor expression.",
            ),
            LifecycleEvent(
                development_id=dev2_id,
                source_id="fda",
                stage="Label Expansion Filing",
                notes="Regulatory submission under review for non-inhibitor patient population.",
            ),
            LifecycleEvent(
                development_id=dev3_id,
                source_id="clinical_trials",
                stage="Phase III FRONTIER Topline Primary Endpoint Met",
                notes="Statistically significant annualized bleeding rate reduction in severe Haemophilia A.",
            ),
        ])

        # 7. Confluences
        await session.execute(delete(Confluence))
        session.add_all([
            Confluence(
                development_id=dev1_id,
                signal_count=4,
                confluence_type="strategic_inflection",
            ),
            Confluence(
                development_id=dev3_id,
                signal_count=3,
                confluence_type="regulatory_catalyst",
            ),
        ])

        # 8. Contradictions (with verbatim clinical claims)
        await session.execute(delete(Contradiction))
        session.add_all([
            Contradiction(
                claim_a_id="38291023",
                claim_b_id="SEC-10K-2026-Q1",
                rule_id="RULE-M-01",
                rule_name="Dosing Frequency Contradiction",
                severity="HIGH",
                confidence=0.89,
                description="Medical publication reports monthly subcutaneous dosing in severe cohorts; corporate SEC filing specifies bi-weekly maintenance regimen.",
                claim_a_excerpt="Abstract conclusions specify a once-monthly 300mg subcutaneous dosing schedule achieves protective factor trough levels (>15%).",
                claim_b_excerpt="Section 1.A Form 10-K specifies commercial packaging and pivotal label guidance will launch exclusively under a bi-weekly dosing regimen.",
            ),
            Contradiction(
                claim_a_id="NCT04869267",
                claim_b_id="EMA-CHMP-2026-04",
                rule_id="RULE-S-04",
                rule_name="Primary Endpoint Completion Date Discrepancy",
                severity="MEDIUM",
                confidence=0.78,
                description="ClinicalTrials.gov registry lists primary study completion as June 2026; EMA CHMP briefing document forecasts Q4 2026 topline dataset.",
                claim_a_excerpt="Study NCT04869267 Primary Completion Date: June 30, 2026 [Anticipated]. Final protocol amendment 4 closed enrollment.",
                claim_b_excerpt="CHMP Assessment Timetable: Sponsor indicates final 52-week clinical study report will be submitted for review in November 2026.",
            ),
        ])

        # 9. Watch Rules / Missing Signals (Rich 6-State FSM items)
        now = datetime.now(timezone.utc)
        await session.execute(delete(WatchItem))
        session.add_all([
            WatchItem(
                development_id=dev1_id,
                trigger_event="Phase III 5-Year Data Completion",
                expected_event="Annualized Bleed Rate durability publication in peer-reviewed journal",
                monitoring_window_days=90,
                responsible_function="MEDICAL_AFFAIRS",
                status="watching",
                created_at=now - timedelta(days=105),
            ),
            WatchItem(
                development_id=dev2_id,
                trigger_event="EMA Positive Opinion for Non-Inhibitor Cohort",
                expected_event="National Reimbursement & Pricing Dossier Submission in G5 European Markets",
                monitoring_window_days=60,
                responsible_function="MARKET_ACCESS",
                status="watching",
                created_at=now - timedelta(days=20),
            ),
            WatchItem(
                development_id=dev3_id,
                trigger_event="FRONTIER-2 Primary Endpoint Readout",
                expected_event="FDA Advisory Committee (AdCom) Briefing Document Publication",
                monitoring_window_days=45,
                responsible_function="REGULATORY",
                status="watching",
                created_at=now - timedelta(days=52),
            ),
            WatchItem(
                development_id=dev1_id,
                trigger_event="Vector Shedding & Liver Safety Monitoring",
                expected_event="12-Month Post-Marketing Transaminitis Registry Safety Report",
                monitoring_window_days=90,
                responsible_function="SAFETY",
                status="watching",
                created_at=now - timedelta(days=15),
            ),
        ])

        # 10. Starter Signals with Real Provenance, Authority Tiers & Verified Multi-Factor Scoring
        signal_rows = [
            {
                "fingerprint": "fp_seed_01",
                "source_id": "pubmed",
                "source_name": "PubMed MEDLINE",
                "development_id": dev1_id,
                "external_id": "38291023",
                "pmid": "38291023",
                "nct_id": None,
                "regulatory_id": None,
                "signal_type": "PUBLICATIONS",
                "disease": "haemophilia_a",
                "title": "Five-Year Durability Outcomes in AAV5 Gene Therapy for Severe Haemophilia A",
                "content": "Sustained median Factor VIII expression was maintained at 5 years with a 92% reduction in annualized bleeding rates compared to baseline prophylactic therapy.",
                "canonical_url": "https://pubmed.ncbi.nlm.nih.gov/38291023/",
                "published_at": now - timedelta(days=1),
                "retrieved_at": now,
                "ingested_at": now,
                "data_mode": "test_fixture",
                "is_synthetic": True,
                "provenance_status": "available",
                "evidence_text": "Sustained median Factor VIII expression was maintained at 5 years with a 92% reduction in annualized bleeding rates compared to baseline prophylactic therapy.",
                "source_authority_tier": "AUTHORITATIVE",
                "validation_status": "VALIDATED",
                "what_changed": "5-year long-term follow-up demonstrates sustained median Factor VIII expression (15.2 IU/dL) and 92% reduction in annualized bleeding rate.",
                "why_it_matters": "Validates durability profile of AAV5 viral vector platforms and establishes long-term benchmark against daily/weekly non-factor prophylaxis.",
                "relevant_function": "MEDICAL_AFFAIRS",
                "route_destination": "MEDICAL_AFFAIRS",
                "route_role": "FUNCTION",
                "is_escalated": False,
                "routing_reason": "Routed to Medical Affairs based on scientific publication classification and clinical benchmark relevance.",
                "routing_timestamp": now - timedelta(hours=12),
                "suggested_action": "Incorporate 5-year FVIII expression durability curve into comparative clinical positioning dossiers and brief field MSLs.",
                "action_rationale": "Direct comparative evidence against standard-of-care prophylaxis informs clinician counseling and competitive differentiation.",
                "review_status": "UNREVIEWED",
                "facts": [
                    "Sustained median Factor VIII expression maintained at 5 years post-infusion.",
                    "92% reduction in annualized bleeding rate compared to standard prophylaxis.",
                ],
                "interpretation": "AAV5 gene therapy demonstrates prolonged hemostatic protection without progressive late-onset expression decay.",
                "speculation": "May accelerate commercial adoption in adult severe cohorts without neutralizing antibodies.",
                "priority": "HIGH",
                "score_breakdown": {
                    "novelty": 20.0,
                    "clinical": 24.0,
                    "regulatory": 18.0,
                    "recency": 18.0,
                    "total": 80.0,
                    "priority_level": "HIGH",
                    "version": "haemophilia_v2.0",
                },
            },
            {
                "fingerprint": "fp_seed_02",
                "source_id": "clinical_trials",
                "source_name": "ClinicalTrials.gov",
                "development_id": dev3_id,
                "external_id": "NCT04869267",
                "pmid": None,
                "nct_id": "NCT04869267",
                "regulatory_id": None,
                "signal_type": "CLINICAL_TRIAL",
                "disease": "haemophilia_a",
                "title": "Phase 3 FRONTIER-2 Trial Evaluates Subcutaneous Mim8 in Haemophilia A Patients",
                "content": "Primary outcome measures achieved zero-bleed status in a majority of treated cohorts without unexpected thromboembolic adverse events.",
                "canonical_url": "https://clinicaltrials.gov/study/NCT04869267",
                "published_at": now - timedelta(days=3),
                "retrieved_at": now,
                "ingested_at": now,
                "data_mode": "test_fixture",
                "is_synthetic": True,
                "provenance_status": "available",
                "evidence_text": "Primary outcome measures achieved zero-bleed status in a majority of treated cohorts without unexpected thromboembolic adverse events.",
                "source_authority_tier": "AUTHORITATIVE",
                "validation_status": "VALIDATED",
                "what_changed": "Pivotal Phase 3 FRONTIER-2 topline readout met all primary and secondary endpoints with superior zero-bleed rates across weekly/monthly dosing.",
                "why_it_matters": "Novo Nordisk core next-generation FVIIIa-mimetic bispecific antibody demonstrates best-in-class efficacy profile against emicizumab.",
                "relevant_function": "LEADERSHIP",
                "route_destination": "LEADERSHIP",
                "route_role": "LEADERSHIP",
                "is_escalated": True,
                "routing_reason": "Escalated to Executive Leadership due to CRITICAL priority impact across global portfolio strategy and regulatory filing schedule.",
                "routing_timestamp": now - timedelta(hours=8),
                "suggested_action": "Convene Executive Steering Committee to finalize global BLA/MAA submission timetables and align commercial launch supply readiness.",
                "action_rationale": "Pivotal Phase 3 milestone represents primary strategic growth pillar for rare disease franchise.",
                "review_status": "REVIEWED",
                "reviewed_by": "Global Medical Lead",
                "reviewed_at": now - timedelta(hours=4),
                "review_decision": "Approved for executive briefing and global regulatory submission preparation.",
                "review_notes": "Topline data confirmed zero-bleed superiority in inhibitor and non-inhibitor cohorts.",
                "resulting_action": "Executive steering briefing scheduled; BLA filing preparation initiated.",
                "facts": [
                    "Phase 3 FRONTIER-2 met primary and key secondary endpoints.",
                    "Achieved statistically significant reduction in treated bleeds vs prior prophylaxis.",
                ],
                "interpretation": "Subcutaneous Mim8 delivers high-potency Factor VIIIa-mimetic activity with convenient dosing flexibility.",
                "speculation": "Expected to capture substantial share in both inhibitor and non-inhibitor Haemophilia A populations upon approval.",
                "priority": "CRITICAL",
                "score_breakdown": {
                    "novelty": 23.5,
                    "clinical": 28.5,
                    "regulatory": 23.0,
                    "recency": 15.0,
                    "total": 90.0,
                    "priority_level": "CRITICAL",
                    "version": "haemophilia_v2.0",
                },
            },
            {
                "fingerprint": "fp_seed_03",
                "source_id": "fda",
                "source_name": "openFDA Regulatory",
                "development_id": dev2_id,
                "external_id": "BLA761083",
                "pmid": None,
                "nct_id": None,
                "regulatory_id": "BLA761083",
                "signal_type": "REGULATORY",
                "disease": "haemophilia_a",
                "title": "FDA Priority Review Granted for Subcutaneous Anti-TFPI Prophylaxis Expansion",
                "content": "Supplemental Biologics License Application (sBLA) accepted under Priority Review with a PDUFA action date scheduled for late 2026.",
                "canonical_url": "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo=761083",
                "published_at": now - timedelta(days=5),
                "retrieved_at": now,
                "ingested_at": now,
                "data_mode": "test_fixture",
                "is_synthetic": True,
                "provenance_status": "available",
                "evidence_text": "Supplemental Biologics License Application (sBLA) accepted under Priority Review with a PDUFA action date scheduled for late 2026.",
                "source_authority_tier": "AUTHORITATIVE",
                "validation_status": "VALIDATED",
                "what_changed": "FDA accepted sBLA with Priority Review designation for expanding anti-TFPI subcutaneous prophylaxis indication to non-inhibitor cohorts.",
                "why_it_matters": "Shortens regulatory review timeline to 6 months and expands addressable target patient population significantly.",
                "relevant_function": "REGULATORY",
                "route_destination": "REGULATORY",
                "route_role": "FUNCTION",
                "is_escalated": False,
                "routing_reason": "Routed to Regulatory Affairs based on FDA agency action and PDUFA milestone tracking.",
                "routing_timestamp": now - timedelta(days=2),
                "suggested_action": "Prepare Advisory Committee briefing materials and align label negotiation strategy with Regulatory and Medical Affairs teams.",
                "action_rationale": "Priority review accelerates inspection schedules and mid-cycle review deadlines.",
                "review_status": "UNREVIEWED",
                "facts": [
                    "sBLA accepted under FDA Priority Review.",
                    "PDUFA target action date established for Q4 2026.",
                ],
                "interpretation": "FDA recognition of unmet medical need provides accelerated pathway for label expansion.",
                "speculation": "Potential for broader market adoption if label includes flexible self-administration device.",
                "priority": "HIGH",
                "score_breakdown": {
                    "novelty": 18.0,
                    "clinical": 22.0,
                    "regulatory": 24.0,
                    "recency": 14.0,
                    "total": 78.0,
                    "priority_level": "HIGH",
                    "version": "haemophilia_v2.0",
                },
            },
            {
                "fingerprint": "fp_seed_04",
                "source_id": "ema",
                "source_name": "European Medicines Agency",
                "development_id": dev1_id,
                "external_id": "EMA-CHMP-2026-04",
                "pmid": None,
                "nct_id": None,
                "regulatory_id": "EMA-CHMP-2026-04",
                "signal_type": "SAFETY",
                "disease": "haemophilia_a",
                "title": "EMA CHMP Concludes 5-Year Safety Review for Gene Transfer Vectors",
                "content": "European Medicines Agency CHMP committee confirms positive benefit-risk ratio with stable long-term transaminitis profile across adult cohorts.",
                "canonical_url": "https://www.ema.europa.eu/en/medicines/human/EPAR/roctavian#safety-updates-section",
                "published_at": now - timedelta(days=2),
                "retrieved_at": now,
                "ingested_at": now,
                "data_mode": "test_fixture",
                "is_synthetic": True,
                "provenance_status": "available",
                "evidence_text": "European Medicines Agency CHMP committee confirms positive benefit-risk ratio with stable long-term transaminitis profile across adult cohorts.",
                "source_authority_tier": "AUTHORITATIVE",
                "validation_status": "VALIDATED",
                "what_changed": "EMA CHMP concluded comprehensive 5-year post-authorization safety review, confirming positive benefit-risk ratio without new safety signals.",
                "why_it_matters": "Provides regulatory affirmation of liver safety and long-term vector clearance in severe Haemophilia A patients.",
                "relevant_function": "SAFETY",
                "route_destination": "SAFETY",
                "route_role": "FUNCTION",
                "is_escalated": False,
                "routing_reason": "Routed to Safety / Pharmacovigilance based on EMA CHMP safety assessment conclusions.",
                "routing_timestamp": now - timedelta(hours=18),
                "suggested_action": "Update global safety surveillance registry benchmarks and reconcile post-marketing liver enzyme monitoring protocols.",
                "action_rationale": "Authoritative regulatory assessment reaffirms class-wide safety thresholds for gene therapy programs.",
                "review_status": "UNREVIEWED",
                "facts": [
                    "EMA CHMP confirmed positive benefit-risk profile.",
                    "No cases of delayed thrombotic microangiopathy or vector-related malignancy observed.",
                ],
                "interpretation": "Reassures clinicians regarding long-term hepatic tolerability of AAV gene transfer.",
                "speculation": "May reduce corticosteroid prophylaxis duration requirements in future protocol designs.",
                "priority": "HIGH",
                "score_breakdown": {
                    "novelty": 19.0,
                    "clinical": 25.0,
                    "regulatory": 22.0,
                    "recency": 16.0,
                    "total": 82.0,
                    "priority_level": "HIGH",
                    "version": "haemophilia_v2.0",
                },
            },
        ]

        for s_data in signal_rows:
            stmt = select(Signal).where(Signal.fingerprint == s_data["fingerprint"])
            res = await session.execute(stmt)
            sig_obj = res.scalar_one_or_none()
            if not sig_obj:
                session.add(Signal(**s_data))
            else:
                # Update with verified score breakdown, decision fields, and provenance URLs
                sig_obj.score_breakdown = s_data["score_breakdown"]
                sig_obj.canonical_url = s_data["canonical_url"]
                sig_obj.external_id = s_data["external_id"]
                sig_obj.development_id = s_data["development_id"]
                sig_obj.pmid = s_data["pmid"]
                sig_obj.nct_id = s_data["nct_id"]
                sig_obj.regulatory_id = s_data["regulatory_id"]
                sig_obj.provenance_status = s_data["provenance_status"]
                sig_obj.evidence_text = s_data["evidence_text"]
                sig_obj.priority = s_data["priority"]
                sig_obj.what_changed = s_data["what_changed"]
                sig_obj.why_it_matters = s_data["why_it_matters"]
                sig_obj.relevant_function = s_data["relevant_function"]
                sig_obj.route_destination = s_data["route_destination"]
                sig_obj.route_role = s_data["route_role"]
                sig_obj.is_escalated = s_data["is_escalated"]
                sig_obj.routing_reason = s_data["routing_reason"]
                sig_obj.routing_timestamp = s_data["routing_timestamp"]
                sig_obj.source_authority_tier = s_data["source_authority_tier"]
                sig_obj.validation_status = s_data["validation_status"]
                sig_obj.suggested_action = s_data["suggested_action"]
                sig_obj.action_rationale = s_data["action_rationale"]
                sig_obj.review_status = s_data["review_status"]
                sig_obj.facts = s_data["facts"]
                sig_obj.interpretation = s_data["interpretation"]
                sig_obj.speculation = s_data["speculation"]

        # 11. Scoring Weights & Calibration Feedback
        roles_weights = {
            "MEDICAL_AFFAIRS": {"impact": 1.15, "urgency": 1.10, "novelty": 0.95},
            "REGULATORY": {"impact": 1.20, "urgency": 1.15, "novelty": 0.90},
            "SAFETY": {"impact": 1.25, "urgency": 1.20, "novelty": 0.85},
            "MARKET_ACCESS": {"impact": 1.10, "urgency": 1.05, "novelty": 1.00},
            "COMMUNICATIONS": {"impact": 1.05, "urgency": 1.05, "novelty": 1.00},
            "LEADERSHIP": {"impact": 1.00, "urgency": 1.00, "novelty": 1.00},
        }
        for r, w in roles_weights.items():
            existing = await session.execute(select(ScoringWeights).where(ScoringWeights.stakeholder_function == r))
            row = existing.scalar_one_or_none()
            if not row:
                session.add(ScoringWeights(
                    stakeholder_function=r,
                    impact_weight=w["impact"],
                    urgency_weight=w["urgency"],
                    novelty_weight=w["novelty"],
                ))
            else:
                row.impact_weight = w["impact"]
                row.urgency_weight = w["urgency"]
                row.novelty_weight = w["novelty"]

        # 12. Seed Calibration Feedback for Stakeholder Functions
        await session.execute(delete(CalibrationFeedback))
        sample_signals_res = await session.execute(select(Signal).limit(10))
        sample_signals = sample_signals_res.scalars().all()
        
        if sample_signals:
            feedbacks_to_add = [
                # Medical Affairs feedback
                CalibrationFeedback(
                    signal_id=sample_signals[0].signal_id,
                    stakeholder_function="MEDICAL_AFFAIRS",
                    relevance_rating=5,
                    urgency_rating=4,
                    action_appropriate=True,
                    comments="Critical 5-year durability data directly informs MSL field briefings.",
                    submitted_at=now - timedelta(days=2),
                ),
                CalibrationFeedback(
                    signal_id=sample_signals[min(1, len(sample_signals)-1)].signal_id,
                    stakeholder_function="MEDICAL_AFFAIRS",
                    relevance_rating=4,
                    urgency_rating=4,
                    action_appropriate=True,
                    comments="Pivotal trial endpoints corroborate our non-factor comparative dataset.",
                    submitted_at=now - timedelta(days=4),
                ),
                # Regulatory feedback
                CalibrationFeedback(
                    signal_id=sample_signals[min(2, len(sample_signals)-1)].signal_id,
                    stakeholder_function="REGULATORY",
                    relevance_rating=5,
                    urgency_rating=5,
                    action_appropriate=True,
                    comments="Priority review designation requires immediate filing schedule alignment.",
                    submitted_at=now - timedelta(days=1),
                ),
                CalibrationFeedback(
                    signal_id=sample_signals[min(3, len(sample_signals)-1)].signal_id,
                    stakeholder_function="REGULATORY",
                    relevance_rating=4,
                    urgency_rating=4,
                    action_appropriate=True,
                    comments="EMA CHMP scientific opinion verified against European filing dossiers.",
                    submitted_at=now - timedelta(days=3),
                ),
                # Safety feedback
                CalibrationFeedback(
                    signal_id=sample_signals[min(3, len(sample_signals)-1)].signal_id,
                    stakeholder_function="SAFETY",
                    relevance_rating=5,
                    urgency_rating=5,
                    action_appropriate=True,
                    comments="Transaminitis surveillance profile confirms baseline safety threshold.",
                    submitted_at=now - timedelta(days=2),
                ),
                # Market Access feedback
                CalibrationFeedback(
                    signal_id=sample_signals[0].signal_id,
                    stakeholder_function="MARKET_ACCESS",
                    relevance_rating=4,
                    urgency_rating=3,
                    action_appropriate=True,
                    comments="Durability curves strengthen health economics dossier for reimbursement.",
                    submitted_at=now - timedelta(days=5),
                ),
                # Communications feedback
                CalibrationFeedback(
                    signal_id=sample_signals[min(1, len(sample_signals)-1)].signal_id,
                    stakeholder_function="COMMUNICATIONS",
                    relevance_rating=4,
                    urgency_rating=4,
                    action_appropriate=True,
                    comments="Clear scientific narrative for press statement and external communications.",
                    submitted_at=now - timedelta(days=3),
                ),
            ]
            session.add_all(feedbacks_to_add)

        # 13. Clean orphaned test fixture signals and seed synthetic landscape records
        from sqlalchemy import or_
        test_patterns = [
            '%Test Signal%',
            'S1 Pending',
            'S2 In Review',
            'S3 Actioned',
            'FSM Lifecycle%',
            'Terminal State%',
            'Invalid Transition%',
            'Escalation Lifecycle%',
            'Deterministic E2E Acceptance%',
            'Test Signal Title',
            'MedAffairs Test Trial Signal',
            'Safety Test Advisory Signal',
            'Actioned Permission Test Signal',
        ]
        await session.execute(delete(Signal).where(or_(*[Signal.title.ilike(p) for p in test_patterns])))

        # 14. Load synthetic signals across all 8 sources
        import json
        syn_path = Path(__file__).resolve().parents[1] / "data" / "synthetic_signals.json"
        if syn_path.exists():
            syn_data = json.loads(syn_path.read_text(encoding="utf-8"))
            from app.services.scoring import priority_scorer
            from app.services.authority import get_source_authority_tier, resolve_validation_status
            from app.services.routing import resolve_signal_routing, StakeholderFunction

            for item in syn_data[:60]:
                fp = f"syn:{item['id']}"
                sig_stmt = select(Signal).where(Signal.fingerprint == fp)
                sig_res = await session.execute(sig_stmt)
                existing_sig = sig_res.scalar_one_or_none()
                
                title = item.get("title", "")
                content = item.get("content", "")
                source_id = item.get("source_id", "newsapi")
                pub_at = datetime.fromisoformat(item["published_at"]) if "published_at" in item else now
                
                score_obj = priority_scorer.score_text(f"{title} {content}", pub_at, novelty_distance=0.65)
                routing = resolve_signal_routing(
                    signal_type=item.get("signal_type", "NEWS"),
                    title=title,
                    content=content,
                    priority=score_obj.priority_level,
                    priority_score=score_obj.total,
                )

                syn_record_data = {
                    "fingerprint": fp,
                    "source_id": source_id,
                    "source_name": source_id.upper().replace("_", " "),
                    "external_id": item.get("external_id"),
                    "pmid": item.get("pmid"),
                    "nct_id": item.get("nct_id"),
                    "regulatory_id": item.get("regulatory_id"),
                    "signal_type": item.get("signal_type", "NEWS"),
                    "disease": item.get("disease", "haemophilia_a"),
                    "title": title,
                    "content": content,
                    "canonical_url": item.get("url"),
                    "published_at": pub_at,
                    "retrieved_at": now,
                    "ingested_at": now,
                    "data_mode": "test_fixture",
                    "is_synthetic": True,
                    "provenance_status": "available",
                    "evidence_text": content,
                    "source_authority_tier": get_source_authority_tier(source_id).value,
                    "validation_status": resolve_validation_status(source_id).value,
                    "what_changed": title,
                    "why_it_matters": content[:200],
                    "relevant_function": routing["relevant_function"].value if hasattr(routing["relevant_function"], "value") else str(routing["relevant_function"]),
                    "route_destination": routing["route_destination"],
                    "route_role": routing["route_role"],
                    "is_escalated": routing["is_escalated"],
                    "routing_reason": routing["routing_reason"],
                    "routing_timestamp": now,
                    "suggested_action": routing["suggested_action"],
                    "action_rationale": "Automated deterministic routing synthesis.",
                    "review_status": "UNREVIEWED",
                    "priority": score_obj.priority_level,
                    "score_breakdown": score_obj.to_dict(),
                    "scoring_model_version": score_obj.version,
                }

                if not existing_sig:
                    session.add(Signal(**syn_record_data))
                else:
                    for k, v in syn_record_data.items():
                        setattr(existing_sig, k, v)

        # 15. Backfill vector embeddings and multi-factor scores for all signals
        all_signals_res = await session.execute(select(Signal))
        all_signals = all_signals_res.scalars().all()
        
        from app.services.embeddings import embedding_service
        from app.services.scoring import priority_scorer
        
        for sig in all_signals:
            text_to_process = f"{sig.title or ''} {sig.content or ''}"
            # Embed if missing
            if sig.embedding is None:
                try:
                    sig.embedding = await embedding_service.embed_text(text_to_process)
                except Exception:
                    pass
            # Multi-factor score if missing
            if not sig.score_breakdown or not isinstance(sig.score_breakdown, dict) or not sig.score_breakdown.get("total"):
                sb = priority_scorer.score_text(text_to_process, sig.published_at or now, novelty_distance=0.6)
                if sb:
                    sig.score_breakdown = sb.to_dict()
                    if not sig.priority:
                        sig.priority = sb.priority_level

        await session.commit()
        print("[SUCCESS] Database seeding and source reconciliation complete.")


if __name__ == "__main__":
    asyncio.run(seed_data())

