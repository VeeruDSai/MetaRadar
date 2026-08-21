import asyncio
import sys
import uuid
from datetime import datetime, timezone, timedelta
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

        # 2. Canonical Data Sources (Exactly the 5 registered pipeline connectors)
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

        # 10. Starter Signals with Real Provenance & Verified Multi-Factor Scoring
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
                "disease": "haemophilia_b",
                "title": "FDA Priority Review Granted for Subcutaneous Anti-TFPI Prophylaxis Expansion",
                "content": "Supplemental Biologics License Application (sBLA) accepted under Priority Review with a PDUFA action date scheduled for late 2026.",
                "canonical_url": "https://open.fda.gov/drug/event/",
                "published_at": now - timedelta(days=5),
                "retrieved_at": now,
                "ingested_at": now,
                "data_mode": "test_fixture",
                "is_synthetic": True,
                "provenance_status": "available",
                "evidence_text": "Supplemental Biologics License Application (sBLA) accepted under Priority Review with a PDUFA action date scheduled for late 2026.",
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
        ]

        for s_data in signal_rows:
            stmt = select(Signal).where(Signal.fingerprint == s_data["fingerprint"])
            res = await session.execute(stmt)
            sig_obj = res.scalar_one_or_none()
            if not sig_obj:
                session.add(Signal(**s_data))
            else:
                # Update with verified score breakdown and provenance URLs
                sig_obj.score_breakdown = s_data["score_breakdown"]
                sig_obj.canonical_url = s_data["canonical_url"]
                sig_obj.external_id = s_data["external_id"]
                sig_obj.pmid = s_data["pmid"]
                sig_obj.nct_id = s_data["nct_id"]
                sig_obj.regulatory_id = s_data["regulatory_id"]
                sig_obj.provenance_status = s_data["provenance_status"]
                sig_obj.evidence_text = s_data["evidence_text"]
                sig_obj.priority = s_data["priority"]

        # 11. Scoring Weights
        roles = ["MEDICAL_AFFAIRS", "REGULATORY", "SAFETY", "MARKET_ACCESS", "COMMUNICATIONS", "LEADERSHIP"]
        for r in roles:
            existing = await session.execute(select(ScoringWeights).where(ScoringWeights.stakeholder_function == r))
            if not existing.scalar_one_or_none():
                session.add(ScoringWeights(
                    stakeholder_function=r,
                    impact_weight=1.0,
                    urgency_weight=1.0,
                    novelty_weight=1.0,
                ))

        await session.commit()
        print("[SUCCESS] Database seeding and source reconciliation complete.")


if __name__ == "__main__":
    asyncio.run(seed_data())
