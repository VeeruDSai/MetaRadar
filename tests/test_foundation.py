import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.core.domain_config import get_domain_config
from app.providers.factory import provider_factory
from app.providers.degraded import DegradedProvider
from app.providers.base import ProviderCapability, DataClassification
from app.services.deduplication import generate_fingerprint, chunk_text_for_embedding
from app.services.pii import PIIPHIScrubber
from app.services.redteam import RedTeamNLIService


async def run_tests():
    print("=== MetaRadar v5.1 Foundation Verification Tests ===")

    # 1. Test DomainConfig Loader
    print("\n1. Testing DomainConfig loader...")
    config = get_domain_config()
    assert config.domain_config_version == "v5.1.0"
    assert len(config.assets) >= 7
    assert config.confluence.minimum_independent_signals == 3
    assert config.confluence.emerging_threshold == 2
    print(f"[PASS] DomainConfig loaded cleanly: {config.disease_area} ({len(config.assets)} assets configured).")

    # 2. Test Deduplication Fingerprint & Chunking
    print("\n2. Testing Deduplication & Chunking...")
    fp1 = generate_fingerprint("ASH 2026 Trial Readout", datetime.now(timezone.utc), pmid="12345678")
    assert fp1 == "pmid:12345678"

    long_text = "A" * 2000
    chunked = chunk_text_for_embedding(long_text, max_tokens=256)
    assert len(chunked) <= 256 * 4
    print("[PASS] Fingerprint & 256-token text chunking verified.")

    # 3. Test PII/PHI Scrubber & Classification
    print("\n3. Testing PII/PHI Scrubber...")
    scrubbed, has_pii, counts = PIIPHIScrubber.scrub("Patient email patient@example.com, DOB: 05/12/1980")
    assert has_pii is True
    assert "[EMAIL_REDACTED]" in scrubbed
    assert PIIPHIScrubber.classify_payload(scrubbed, source_type="pubmed") == DataClassification.PUBLIC
    print("[PASS] PII/PHI scrubbing and classification verified.")

    # 4. Test Red-Team Rule Registry & Contradiction Service
    print("\n4. Testing Red-Team Contradiction Service...")
    redteam = RedTeamNLIService()
    claims = [
        {"claim_id": "c1", "asset": "Hemgenix", "signal_type": "CLINICAL_TRIAL", "priority": "HIGH", "source": "PubMed"},
        {"claim_id": "c2", "asset": "Hemgenix", "signal_type": "REGULATORY", "priority": "HIGH", "source": "FDA"}
    ]
    flags = await redteam.evaluate_contradictions(claims)
    assert len(flags) > 0
    assert flags[0]["rule_id"] == "RULE_A_DOSING_CONTRADICTION"
    print("[PASS] Red-Team contradiction evaluation verified.")

    # 5. Test Provider Execution & Degraded BART Fallback
    print("\n5. Testing Provider Execution & Capability Matrix...")
    result = await provider_factory.execute_task(
        required_capability=ProviderCapability.REASON,
        evidence=["Trial shows 80% reduction in ABR"],
        task="Evaluate efficacy durability",
        classification=DataClassification.PUBLIC
    )
    assert "model_metadata" in result
    assert result["model_metadata"]["reasoning_available"] is True
    print("[PASS] Provider execution verified.")

    degraded = DegradedProvider()
    deg_result = await degraded.generate_intelligence(
        evidence=["Trial shows 80% reduction in ABR"],
        task="Evaluate efficacy durability",
        classification=DataClassification.PUBLIC
    )
    assert deg_result["mode"] == "degraded_factual"
    assert deg_result["model_metadata"]["reasoning_available"] is False
    assert deg_result["model_metadata"]["actions_available"] is False
    print("[PASS] Degraded BART fallback execution verified.")

    print("\n=== ALL FOUNDATION VERIFICATION TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(run_tests())
