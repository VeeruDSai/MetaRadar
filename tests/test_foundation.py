import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend directory to sys.path
base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.core.domain_config import get_domain_config
from app.providers.factory import provider_factory
from app.providers.degraded import DegradedProvider
from app.providers.base import ProviderCapability, DataClassification
from app.services.deduplication import generate_fingerprint, chunk_text_for_embedding


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

    # 3. Test Provider Execution & Degraded BART Fallback
    print("\n3. Testing Provider Execution & Capability Matrix...")
    # Primary execution (Gemma)
    result = await provider_factory.execute_task(
        required_capability=ProviderCapability.REASON,
        evidence=["Trial shows 80% reduction in ABR"],
        task="Evaluate efficacy durability",
        classification=DataClassification.PUBLIC
    )
    assert "model_metadata" in result
    assert result["model_metadata"]["provider"] == "local_gemma"
    assert result["model_metadata"]["reasoning_available"] is True
    print("[PASS] Local Gemma reasoning execution verified.")

    # Fallback execution (Degraded BART)
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
