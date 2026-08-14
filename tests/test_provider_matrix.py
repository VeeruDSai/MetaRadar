import json
import pytest
import sys
from pathlib import Path
from httpx import AsyncClient, MockTransport, Response

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.providers.gemma import GemmaProvider
from app.providers.grok import GrokProvider
from app.providers.degraded import DegradedProvider
from app.providers.factory import ProviderFactory
from app.providers.base import ProviderCapability, DataClassification
from app.core.config import settings


@pytest.mark.asyncio
async def test_case_a_gemma_available():
    gemma = GemmaProvider()

    def ollama_handler(request):
        return Response(
            200,
            json={
                "model": "gemma3:4b",
                "response": json.dumps({
                    "what_changed": "Significant haemophilia signal identified across 1 evidence excerpts.",
                    "why_it_matters": "Directly impacts therapeutic landscape.",
                    "primary_function": "MEDICAL_AFFAIRS",
                    "suggested_action": "Escalate trial readout to Medical Affairs lead.",
                }),
                "done": True,
            },
        )

    gemma._client = AsyncClient(transport=MockTransport(ollama_handler), base_url="http://ollama-test")

    result = await gemma.generate_intelligence(
        evidence=["Factor IX level stable at 35%"],
        task="Evaluate FIX expression durability",
        classification=DataClassification.PUBLIC
    )
    meta = result["model_metadata"]
    assert meta["provider"] == "local_gemma"
    assert meta["mode"] == "reasoning"
    assert meta["fallback_used"] is False
    assert meta["reasoning_available"] is True


@pytest.mark.asyncio
async def test_case_b_gemma_unavailable_grok_disabled(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "none")
    monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", False)

    factory = ProviderFactory()
    result = await factory.execute_task(
        required_capability=ProviderCapability.REASON,
        evidence=["Factor IX level stable at 35%"],
        task="Evaluate FIX expression durability",
        classification=DataClassification.PUBLIC
    )
    meta = result["model_metadata"]
    assert meta["provider"] == "bart"
    assert meta["mode"] == "degraded_factual"
    assert meta["reasoning_available"] is False


@pytest.mark.asyncio
async def test_case_c_gemma_unavailable_grok_enabled(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "xai")
    monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", True)

    grok_provider = GrokProvider(api_key="mock-xai-key-for-test")
    factory = ProviderFactory()
    factory.grok = grok_provider

    result = await factory.execute_task(
        required_capability=ProviderCapability.REASON,
        evidence=["Factor IX level stable at 35%"],
        task="Evaluate FIX expression durability",
        classification=DataClassification.PUBLIC
    )
    meta = result["model_metadata"]
    assert meta["provider"] == "xai"
    assert meta["fallback_used"] is True


@pytest.mark.asyncio
async def test_case_d_gemma_unavailable_grok_key_missing(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "xai")
    monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", True)

    grok_provider = GrokProvider(api_key="")
    factory = ProviderFactory()
    factory.grok = grok_provider

    result = await factory.execute_task(
        required_capability=ProviderCapability.REASON,
        evidence=["Factor IX level stable at 35%"],
        task="Evaluate FIX expression durability",
        classification=DataClassification.PUBLIC
    )
    meta = result["model_metadata"]
    assert meta["provider"] == "bart"
    assert meta["mode"] == "degraded_factual"


@pytest.mark.asyncio
async def test_case_e_summarize_capability():
    degraded = DegradedProvider()
    assert degraded.supports(ProviderCapability.SUMMARIZE) is True
    assert degraded.supports(ProviderCapability.REASON) is False
    summary = await degraded.generate_summary("Long evidence text detailing hemgenix readout...")
    assert len(summary) > 0


@pytest.mark.asyncio
async def test_case_f_reasoning_requested_from_bart():
    degraded = DegradedProvider()
    result = await degraded.generate_intelligence(
        evidence=["Trial text"],
        task="Reason about efficacy",
        classification=DataClassification.PUBLIC
    )
    meta = result["model_metadata"]
    assert meta["mode"] == "degraded_factual"
    assert meta["reasoning_available"] is False
    assert meta["actions_available"] is False
