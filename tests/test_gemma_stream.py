import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.providers.gemma import GemmaProvider, OllamaUnavailableError


def _chunk(text: str) -> dict:
    return {"choices": [{"text": text}]}


@pytest.mark.asyncio
async def test_generate_stream_yields_native_gguf_deltas():
    provider = GemmaProvider()

    fake_llama = MagicMock()
    fake_llama.create_completion.return_value = iter(
        [_chunk("Hello"), _chunk(" world"), _chunk("")]
    )

    with patch.object(GemmaProvider, "_load_llama_instance", return_value=fake_llama), patch(
        "app.providers.gemma.find_local_gguf_model", return_value=Path("fake.gguf")
    ):
        deltas = [delta async for delta in provider.generate_stream("test prompt")]

    assert deltas == ["Hello", " world"]
    kwargs = fake_llama.create_completion.call_args.kwargs
    assert kwargs["stream"] is True
    assert fake_llama.create_completion.call_args.args[0].startswith("<start_of_turn>user\n")
    assert kwargs["stop"] == GemmaProvider._GGUF_STOP_SEQUENCES


@pytest.mark.asyncio
async def test_generate_stream_wraps_engine_failure_in_unavailable_error():
    provider = GemmaProvider()

    fake_llama = MagicMock()
    fake_llama.create_completion.side_effect = RuntimeError("boom")

    with patch.object(GemmaProvider, "_load_llama_instance", return_value=fake_llama), patch(
        "app.providers.gemma.find_local_gguf_model", return_value=Path("fake.gguf")
    ):
        with pytest.raises(OllamaUnavailableError):
            async for _ in provider.generate_stream("test prompt"):
                pass


@pytest.mark.asyncio
async def test_generate_stream_surfaces_mid_stream_failure_after_partial_deltas():
    provider = GemmaProvider()

    def flaky_stream():
        yield _chunk("partial ")
        raise RuntimeError("engine died mid-stream")

    fake_llama = MagicMock()
    fake_llama.create_completion.return_value = flaky_stream()

    with patch.object(GemmaProvider, "_load_llama_instance", return_value=fake_llama), patch(
        "app.providers.gemma.find_local_gguf_model", return_value=Path("fake.gguf")
    ):
        generator = provider.generate_stream("test prompt")
        first = await generator.__anext__()
        assert first == "partial "
        with pytest.raises(OllamaUnavailableError):
            async for _ in generator:
                pass


@pytest.mark.asyncio
async def test_generate_stream_early_exit_does_not_hang_event_loop():
    provider = GemmaProvider()

    def endless_stream():
        i = 0
        while True:
            yield _chunk(f"tok{i} ")
            i += 1

    fake_llama = MagicMock()
    fake_llama.create_completion.return_value = endless_stream()

    with patch.object(GemmaProvider, "_load_llama_instance", return_value=fake_llama), patch(
        "app.providers.gemma.find_local_gguf_model", return_value=Path("fake.gguf")
    ):
        generator = provider.generate_stream("test prompt")
        first = await generator.__anext__()
        assert first == "tok0 "
        await asyncio.wait_for(generator.aclose(), timeout=5)
