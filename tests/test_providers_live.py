import os
import pytest


@pytest.mark.live
@pytest.mark.skipif(not os.getenv("LIVE_XAI_KEY"), reason="Requires LIVE_XAI_KEY env var")
async def test_grok_live_structured_output():
    """Real Grok API call -- only runs with LIVE_XAI_KEY set. CI stays green without it."""
    from app.providers.grok import GrokProvider
    from app.providers.base import DataClassification

    provider = GrokProvider(api_key=os.environ["LIVE_XAI_KEY"])
    result = await provider.generate_intelligence(
        evidence=["Emicizumab phase 3 trial showed 96% bleed reduction."],
        task="Summarize clinical impact for haemophilia A market.",
        classification=DataClassification.SYNTHETIC
    )
    assert "what_changed" in result
    assert "model_metadata" in result