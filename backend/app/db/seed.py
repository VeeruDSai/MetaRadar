import asyncio
import sys
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
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

        # 1. Sources
        sources_data = [
            {"source_id": "pubmed", "name": "PubMed MEDLINE", "freshness_class": "batch", "syndication_group": "Literature"},
            {"source_id": "clinicaltrials", "name": "ClinicalTrials.gov", "freshness_class": "near_real_time", "syndication_group": "Trial Registries"},
            {"source_id": "openfda", "name": "openFDA Regulatory Disclosures", "freshness_class": "delayed", "syndication_group": "Regulatory"},
            {"source_id": "newsapi", "name": "NewsAPI Industry Feed", "freshness_class": "near_real_time", "syndication_group": "Press / Media", "quota_remaining": 100},
            {"source_id": "ema_rss", "name": "European Medicines Agency RSS", "freshness_class": "delayed", "syndication_group": "Regulatory"},
        ]
        for s in sources_data:
            existing = await session.get(Source, s["source_id"])
            if not existing:
                session.add(Source(**s, status="active"))
        await session.flush()

        # 2. Companies
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

        # 3. Assets
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

        # 4. Canonical Developments
        dev1_id = uuid.uuid4()
        dev2_id = uuid.uuid4()
        dev3_id = uuid.uuid4()

        devs_res = await session.execute(select(Development))
        existing_devs = devs_res.scalars().all()

        if not existing_devs:
            dev1 = Development(
                development_id=dev1_id,
                title="Haemophilia A Long-Term Factor VIII Expression & Durability",
                disease="haemophilia_a",
                asset_id="roctavian",
                company_id="biomarin",
                current_stage="Phase III Long-term Follow-up",
            )
            dev2 = Development(
                development_id=dev2_id,
                title="Subcutaneous Anti-TFPI Prophylaxis Landscape in Haemophilia B",
                disease="haemophilia_b",
                asset_id="alhemo",
                company_id="novo-nordisk",
                current_stage="Approved (Inhibitors) / Phase III Expansion",
            )
            dev3 = Development(
                development_id=dev3_id,
                title="Next-Generation FVIII-Mimetic Subcutaneous Hemostasis",
                disease="haemophilia_a",
                asset_id="mim8",
                company_id="novo-nordisk",
                current_stage="Phase III FRONTIER Readouts",
            )
            session.add_all([dev1, dev2, dev3])
            await session.flush()

            # 5. Lifecycle Events
            session.add_all([
                LifecycleEvent(
                    development_id=dev1_id,
                    source_id="clinicaltrials",
                    stage="Phase III 5-Year Data Readout",
                    notes="5-year post-infusion data presented at congress showing steady baseline factor expression.",
                ),
                LifecycleEvent(
                    development_id=dev2_id,
                    source_id="openfda",
                    stage="Label Expansion Filing",
                    notes="Regulatory submission under review for non-inhibitor patient population.",
                ),
                LifecycleEvent(
                    development_id=dev3_id,
                    source_id="clinicaltrials",
                    stage="Phase III FRONTIER Topline Primary Endpoint Met",
                    notes="Statistically significant annualized bleeding rate reduction in severe Haemophilia A.",
                ),
            ])

            # 6. Confluences
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

            # 7. Contradictions
            session.add_all([
                Contradiction(
                    claim_a_id="CLAIM-PUBMED-8821",
                    claim_b_id="CLAIM-SEC-1049",
                    rule_id="RULE-M-01",
                    rule_name="Dosing Frequency Contradiction",
                    severity="HIGH",
                    confidence=0.89,
                    description="Abstract reported monthly subcutaneous dosing; corporate SEC filing specifies bi-weekly regimen.",
                ),
                Contradiction(
                    claim_a_id="CLAIM-CT-9012",
                    claim_b_id="CLAIM-EMA-3312",
                    rule_id="RULE-S-04",
                    rule_name="Primary Endpoint Completion Date Discrepancy",
                    severity="MEDIUM",
                    confidence=0.78,
                    description="Trial registry lists primary completion as June 2026; EMA filing states Q4 2026 readout.",
                ),
            ])

            # 8. Watch Rules / Missing Signals
            now = datetime.now(timezone.utc)
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
            ])

            # 9. Starter Signals
            session.add_all([
                Signal(
                    source_id="pubmed",
                    development_id=dev1_id,
                    fingerprint="fp_seed_01",
                    signal_type="congress",
                    disease="haemophilia_a",
                    title="Five-Year Durability Outcomes in AAV5 Gene Therapy for Severe Haemophilia A",
                    content="Sustained median Factor VIII expression was maintained at 5 years with a 92% reduction in annualized bleeding rates compared to baseline prophylactic therapy.",
                    published_at=now - timedelta(days=1),
                    priority="HIGH",
                    score_breakdown={"total_score": 88, "impact": 9, "urgency": 8, "evidence_strength": 9},
                ),
                Signal(
                    source_id="clinicaltrials",
                    development_id=dev3_id,
                    fingerprint="fp_seed_02",
                    signal_type="trial",
                    disease="haemophilia_a",
                    title="Phase 3 FRONTIER-2 Trial Evaluates Subcutaneous Mim8 in Haemophilia A Patients",
                    content="Primary outcome measures achieved zero-bleed status in a majority of treated cohorts without unexpected thromboembolic adverse events.",
                    published_at=now - timedelta(days=3),
                    priority="CRITICAL",
                    score_breakdown={"total_score": 94, "impact": 10, "urgency": 9, "evidence_strength": 9},
                ),
                Signal(
                    source_id="openfda",
                    development_id=dev2_id,
                    fingerprint="fp_seed_03",
                    signal_type="regulatory",
                    disease="haemophilia_b",
                    title="FDA Priority Review Granted for Subcutaneous Anti-TFPI Prophylaxis Expansion",
                    content="Supplemental Biologics License Application (sBLA) accepted under Priority Review with a PDUFA action date scheduled for late 2026.",
                    published_at=now - timedelta(days=5),
                    priority="HIGH",
                    score_breakdown={"total_score": 82, "impact": 8, "urgency": 8, "evidence_strength": 9},
                ),
            ])

        # 10. Scoring Weights
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
        print("[SUCCESS] Database seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed_data())
