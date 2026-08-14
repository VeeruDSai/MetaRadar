"""Hermetic retrieval & provider tests — no live services, no network calls (D-16).

All embedding/model behavior is mocked at the module boundary so the suite is
deterministic and CI-safe. Live external calls live in test_providers_live.py
(opt-in via the ``live`` marker + LIVE_XAI_KEY).
"""

import asyncio
import sys
from pathlib import Path

import httpx
import numpy as np
import pytest
from httpx import AsyncClient, MockTransport

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

import app.services.embeddings as embeddings_module
from app.services.embeddings import EmbeddingService, EmbeddingError
from app.services.vector_query import SearchFilters
from app.workflows.nodes.embed import node_embed
from app.workflows.state import create_initial_state
from app.providers.gemma import GemmaProvider, OllamaUnavailableError
from app.providers.grok import GrokProvider, GrokUnavailableError
from app.providers.base import DataClassification
from app.core.config import settings


class FakeTextEmbedding:
    """Minimal stand-in for fastembed TextEmbedding yielding 384-dim vectors."""

    def __init__(self, model_name):
        self.model_name = model_name
        self.embed_call_count = 0
        self.last_documents = []

    def embed(self, documents, batch_size=256, **kwargs):
        self.embed_call_count += 1
        self.last_documents = list(documents)
        for _ in documents:
            yield np.array([0.1] * 384, dtype=np.float32)


# ---------------------------------------------------------------------------
# EmbeddingService
# ---------------------------------------------------------------------------

def test_embed_text_returns_384_dims(monkeypatch):
    fake = FakeTextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    monkeypatch.setattr(embeddings_module, "TextEmbedding", lambda name: fake)

    service = EmbeddingService()
    vector = asyncio.run(service.embed_text("haemophilia trial"))
    assert len(vector) == 384


def test_embed_signal_composites_text(monkeypatch):
    fake = FakeTextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    monkeypatch.setattr(embeddings_module, "TextEmbedding", lambda name: fake)

    service = EmbeddingService()
    vector = asyncio.run(service.embed_signal({
        "title": "mim8 phase 3",
        "content": "haemophilia A trial results",
        "signal_type": "CLINICAL_TRIAL",
    }))
    assert len(vector) == 384
    # Composed text = title + content + signal_type, in that order
    assert fake.last_documents[0] == "mim8 phase 3 haemophilia A trial results CLINICAL_TRIAL"


def test_embed_batch_calls_model_once(monkeypatch):
    fake = FakeTextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    monkeypatch.setattr(embeddings_module, "TextEmbedding", lambda name: fake)

    service = EmbeddingService()
    vectors = asyncio.run(service.embed_batch(["text one", "text two"]))
    assert len(vectors) == 2
    assert all(len(v) == 384 for v in vectors)
    # Batch is passed to the model together — a single embed() call with both docs
    assert fake.embed_call_count == 1
    assert fake.last_documents == ["text one", "text two"]


# ---------------------------------------------------------------------------
# node_embed
# ---------------------------------------------------------------------------

class FakeEmbeddingService:
    """Stand-in for the module-level embedding_service used by node_embed."""

    async def embed_signal(self, signal):
        return [0.5] * 384


def test_node_embed_attaches_embedding_to_signal(monkeypatch):
    monkeypatch.setattr("app.workflows.nodes.embed.embedding_service", FakeEmbeddingService())

    state = create_initial_state()
    state["validated_signals"] = [{
        "id": "sig-1",
        "title": "mim8 trial",
        "content": "haemophilia treatment",
        "signal_type": "CLINICAL_TRIAL",
    }]
    result = asyncio.run(node_embed(state))
    sig = result["validated_signals"][0]
    assert isinstance(sig["embedding"], list)
    assert len(sig["embedding"]) == 384
    assert sig["embedding_model_version"] is not None
    assert result["node_statuses"]["node_embed"] == "SUCCESS"


class PartiallyFailingEmbeddingService:
    """Raises EmbeddingError on the second signal only."""

    def __init__(self):
        self.calls = 0

    async def embed_signal(self, signal):
        self.calls += 1
        if self.calls == 2:
            raise EmbeddingError("mock embedding failure")
        return [0.5] * 384


def test_node_embed_degraded_on_partial_failure(monkeypatch):
    monkeypatch.setattr(
        "app.workflows.nodes.embed.embedding_service", PartiallyFailingEmbeddingService()
    )

    state = create_initial_state()
    state["validated_signals"] = [
        {"id": "sig-1", "title": "a", "content": "content one", "signal_type": "X"},
        {"id": "sig-2", "title": "b", "content": "content two", "signal_type": "X"},
    ]
    result = asyncio.run(node_embed(state))
    signals = result["validated_signals"]
    assert result["node_statuses"]["node_embed"] == "DEGRADED"
    assert len(signals) == 2                      # failed signals are NOT dropped
    assert signals[0]["embedding"] is not None
    assert signals[1]["embedding"] is None        # kept with embedding=None
    assert signals[1]["embedding_model_version"] is None
    assert len(result["errors"]) == 1


def test_node_embed_empty_state_returns_success():
    state = create_initial_state()
    result = asyncio.run(node_embed(state))
    assert result["node_statuses"]["node_embed"] == "SUCCESS"
    assert result["validated_signals"] == []


# ---------------------------------------------------------------------------
# Vector query contracts
# ---------------------------------------------------------------------------

def test_search_filters_pydantic():
    filters = SearchFilters(signal_type="CLINICAL_TRIAL", disease="haemophilia_a", priority="HIGH")
    assert filters.signal_type == "CLINICAL_TRIAL"
    assert filters.disease == "haemophilia_a"
    assert filters.priority == "HIGH"
    # limit was removed from SearchFilters — top_k is the single result limit knob
    assert "limit" not in SearchFilters.model_fields


# ---------------------------------------------------------------------------
# Provider failure behavior
# ---------------------------------------------------------------------------

def _refused_transport():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    return AsyncClient(transport=MockTransport(handler), base_url="http://ollama-test")


def test_gemma_raises_on_connection_refused():
    gemma = GemmaProvider()
    gemma._client = _refused_transport()

    with pytest.raises(OllamaUnavailableError):
        asyncio.run(gemma.generate_intelligence(
            evidence=["Factor IX level stable at 35%"],
            task="Evaluate FIX expression durability",
            classification=DataClassification.PUBLIC,
        ))


def test_gemma_is_available_false_on_error():
    gemma = GemmaProvider()
    gemma._client = _refused_transport()

    assert asyncio.run(gemma.is_available()) is False   # never raises


def test_grok_blocks_without_api_key(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", True)
    grok = GrokProvider(api_key="")

    with pytest.raises(GrokUnavailableError):
        asyncio.run(grok.generate_intelligence(
            evidence=["Factor IX level stable at 35%"],
            task="Evaluate FIX expression durability",
            classification=DataClassification.PUBLIC,
        ))


def test_grok_generate_summary_blocked_by_privacy_gate(monkeypatch):
    """generate_summary transmits with DataClassification.UNKNOWN, so the
    privacy gate must block it before any payload reaches api.x.ai."""
    monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", True)
    grok = GrokProvider(api_key="mock-key")

    with pytest.raises(PermissionError):
        asyncio.run(grok.generate_summary("Patient record user@site.com"))