import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import pytest

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.core.domain_config import get_domain_config
from app.providers.factory import provider_factory
from app.providers.degraded import DegradedProvider
from app.providers.base import ProviderCapability, DataClassification
from app.services.deduplication import generate_fingerprint, chunk_text_for_embedding
from app.services.pii import PIIPHIScrubber
from app.services.redteam import RedTeamNLIService


def test_domain_config_loader():
    """1. Testing DomainConfig loader."""
    config = get_domain_config()
    assert config.domain_config_version == "v5.1.0"
    assert len(config.assets) >= 7
    assert config.confluence.minimum_independent_signals == 3
    assert config.confluence.emerging_threshold == 2


def test_deduplication_fingerprint_and_chunking():
    """2. Testing Deduplication & Chunking."""
    fp1 = generate_fingerprint("ASH 2026 Trial Readout", datetime.now(timezone.utc), pmid="12345678")
    assert fp1 == "pmid:12345678"

    long_text = "A" * 2000
    chunked = chunk_text_for_embedding(long_text, max_tokens=256)
    assert len(chunked) <= 256 * 4


def test_pii_phi_scrubber_and_classification():
    """3. Testing PII/PHI Scrubber."""
    scrubbed, has_pii, counts = PIIPHIScrubber.scrub("Patient email patient@example.com, DOB: 05/12/1980")
    assert has_pii is True
    assert "[EMAIL_REDACTED]" in scrubbed
    assert PIIPHIScrubber.classify_payload(scrubbed, source_type="pubmed") == DataClassification.PUBLIC


@pytest.mark.asyncio
async def test_red_team_contradiction_service():
    """4. Testing Red-Team Contradiction Service."""
    redteam = RedTeamNLIService()
    claims = [
        {"claim_id": "c1", "asset": "Hemgenix", "signal_type": "CLINICAL_TRIAL", "priority": "HIGH", "source": "PubMed"},
        {"claim_id": "c2", "asset": "Hemgenix", "signal_type": "REGULATORY", "priority": "HIGH", "source": "FDA"}
    ]
    flags = await redteam.evaluate_contradictions(claims)
    assert len(flags) > 0
    assert flags[0]["rule_id"] == "RULE_A_DOSING_CONTRADICTION"


@pytest.mark.asyncio
async def test_provider_execution_and_degraded_bart_fallback():
    """5. Testing Provider Execution & Capability Matrix."""
    from httpx import AsyncClient, MockTransport, Response
    import json

    def ollama_handler(request):
        return Response(
            200,
            json={
                "model": "gemma3:4b",
                "response": json.dumps({
                    "what_changed": "Significant haemophilia signal identified.",
                    "why_it_matters": "Directly impacts therapeutic landscape.",
                    "primary_function": "MEDICAL_AFFAIRS",
                    "suggested_action": "Escalate trial readout to Medical Affairs lead.",
                }),
                "done": True,
            },
        )

    # Inject mock client into gemma provider
    provider_factory.gemma._client = AsyncClient(transport=MockTransport(ollama_handler), base_url="http://ollama-test")

    result = await provider_factory.execute_task(
        required_capability=ProviderCapability.REASON,
        evidence=["Trial shows 80% reduction in ABR"],
        task="Evaluate efficacy durability",
        classification=DataClassification.PUBLIC
    )
    assert "model_metadata" in result
    assert result["model_metadata"]["reasoning_available"] is True

    degraded = DegradedProvider()
    deg_result = await degraded.generate_intelligence(
        evidence=["Trial shows 80% reduction in ABR"],
        task="Evaluate efficacy durability",
        classification=DataClassification.PUBLIC
    )
    assert deg_result["mode"] == "degraded_factual"
    assert deg_result["model_metadata"]["reasoning_available"] is False
    assert deg_result["model_metadata"]["actions_available"] is False


async def run_tests():
    print("=== MetaRadar v5.1 Foundation Verification Tests ===")
    test_domain_config_loader()
    print("[PASS] DomainConfig loaded cleanly.")
    test_deduplication_fingerprint_and_chunking()
    print("[PASS] Fingerprint & 256-token text chunking verified.")
    test_pii_phi_scrubber_and_classification()
    print("[PASS] PII/PHI scrubbing and classification verified.")
    await test_red_team_contradiction_service()
    print("[PASS] Red-Team contradiction evaluation verified.")
    await test_provider_execution_and_degraded_bart_fallback()
    print("[PASS] Provider execution and degraded BART fallback verified.")
    print("\n=== ALL FOUNDATION VERIFICATION TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(run_tests())
