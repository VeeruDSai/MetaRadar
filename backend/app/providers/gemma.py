"""GemmaProvider — dual-engine local reasoning provider (GGUF & Ollama).

Discovers and executes local quantized reasoning models (.gguf) from the root models/
directory via llama-cpp-python (if installed), or connects to the local Ollama daemon
(http://localhost:11434).

Never-crash contract (D-12): Any failure raises OllamaUnavailableError so ProviderFactory
safely falls through to Grok -> BART degraded mode without crashing.
"""

import asyncio
import json
import logging
import os
import queue
import threading
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from app.providers.base import LLMProvider, ProviderCapability, DataClassification
from app.core.config import settings
from app.schemas import ModelMetadataSchema

logger = logging.getLogger(__name__)


def find_local_gguf_model() -> Optional[Path]:
    """Scans the models/ directory for any .gguf model file."""
    # 1. Check explicit configuration
    if settings.LOCAL_GGUF_PATH and Path(settings.LOCAL_GGUF_PATH).is_file():
        return Path(settings.LOCAL_GGUF_PATH)

    models_dir = Path(settings.MODELS_DIR)
    if settings.LOCAL_GGUF_MODEL:
        explicit_file = models_dir / settings.LOCAL_GGUF_MODEL
        if explicit_file.is_file():
            return explicit_file

    # 2. Scan models/ directory for any .gguf files
    if models_dir.is_dir():
        gguf_candidates = sorted(models_dir.glob("*.gguf"))
        if gguf_candidates:
            return gguf_candidates[0]

    return None


class OllamaUnavailableError(Exception):
    """Raised when local reasoning engine (GGUF / Ollama) cannot complete a request."""


LocalLLMUnavailableError = OllamaUnavailableError


class GemmaProvider(LLMProvider):
    name = "gemma_local"
    capabilities = [
        ProviderCapability.SUMMARIZE,
        ProviderCapability.CLASSIFY,
        ProviderCapability.REASON,
        ProviderCapability.GENERATE_ACTIONS,
        ProviderCapability.STRUCTURED_OUTPUT
    ]

    def __init__(self):
        self.model_name = settings.OLLAMA_MODEL
        self.max_context = settings.MAX_CONTEXT_TOKENS
        self.max_output = settings.MAX_OUTPUT_TOKENS
        self._client: Optional[httpx.AsyncClient] = None
        self._llama_instance = None

    def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily creates the Ollama HTTP client (connect=5s, read=30s)."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.OLLAMA_HOST,
                timeout=httpx.Timeout(30.0, connect=5.0)
            )
        return self._client

    async def aclose(self) -> None:
        """Close the lazily-created HTTP client, if one was created."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    _GGUF_STOP_SEQUENCES = ["<end_of_turn>", "</s>", "<eos>", "HUMAN:", "SYSTEM:"]
    _STREAM_QUEUE_MAXSIZE = 1024

    def _load_llama_instance(self, gguf_path: Path):
        """Lazily loads the GGUF model via llama-cpp-python with hardware-aware defaults."""
        try:
            from llama_cpp import Llama
        except ImportError:
            raise OllamaUnavailableError(
                f"Local GGUF model found at {gguf_path.name}, but 'llama-cpp-python' is not installed. "
                "Install with: pip install llama-cpp-python"
            )

        if self._llama_instance is None:
            gpu_layers_env = os.environ.get("LLM_GPU_LAYERS")
            if settings.LLM_DEVICE in ("cuda", "gpu", "auto"):
                if gpu_layers_env and gpu_layers_env.strip():
                    try:
                        n_gpu = int(gpu_layers_env.strip())
                    except ValueError:
                        n_gpu = -1
                else:
                    n_gpu = -1
            else:
                n_gpu = 0

            n_threads = min(os.cpu_count() or 8, 12)
            logger.info(
                f"Loading local GGUF reasoning model from {gguf_path.name} "
                f"(n_gpu_layers={n_gpu}, n_threads={n_threads}, n_ctx={self.max_context})..."
            )
            self._llama_instance = Llama(
                model_path=str(gguf_path),
                n_ctx=self.max_context,
                n_gpu_layers=n_gpu,
                n_threads=n_threads,
                n_batch=512,
                f16_kv=True,
                verbose=False,
            )
        return self._llama_instance

    @staticmethod
    def _format_gemma_prompt(prompt: str) -> str:
        """Formats the prompt with Gemma instruction turn markers."""
        return f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"

    @staticmethod
    def _best_effort_put(delta_queue: "queue.Queue", item: object) -> None:
        """Enqueues a terminal item without ever blocking or raising (the consumer may be gone)."""
        try:
            delta_queue.put_nowait(item)
        except queue.Full:
            pass

    def _generate_with_local_gguf(self, gguf_path: Path, prompt: str) -> str:
        """Executes hardware-optimized buffered inference using local GGUF model via llama-cpp-python."""
        llama = self._load_llama_instance(gguf_path)
        output = llama(
            self._format_gemma_prompt(prompt),
            max_tokens=self.max_output,
            temperature=0.2,
            top_p=0.95,
            stop=self._GGUF_STOP_SEQUENCES,
        )
        choices = output.get("choices", [])
        if choices and "text" in choices[0]:
            return str(choices[0]["text"]).strip()
        return ""

    def _iter_local_gguf_stream(self, gguf_path: Path, prompt: str, cancel: threading.Event):
        """Synchronous token-stream generator over llama-cpp-python create_completion(stream=True).

        Designed to run inside a worker thread; checks `cancel` between chunks so the
        async consumer can abort generation early (e.g. client disconnect).
        """
        llama = self._load_llama_instance(gguf_path)
        stream = llama.create_completion(
            self._format_gemma_prompt(prompt),
            max_tokens=self.max_output,
            temperature=0.2,
            top_p=0.95,
            stop=self._GGUF_STOP_SEQUENCES,
            stream=True,
        )
        for chunk in stream:
            if cancel.is_set():
                break
            choices = chunk.get("choices") or []
            delta = str(choices[0].get("text", "")) if choices else ""
            if delta:
                yield delta

    async def _stream_local_gguf_deltas(self, gguf_path: Path, prompt: str) -> AsyncGenerator[str, None]:
        """Bridges the synchronous GGUF token stream onto the asyncio loop via a worker thread.

        The producer thread blocks on native llama-cpp-python generation while the event
        loop stays free; deltas cross a bounded queue so a slow consumer applies natural
        backpressure instead of unbounded memory growth.
        """
        loop = asyncio.get_running_loop()
        delta_queue: "queue.Queue" = queue.Queue(maxsize=self._STREAM_QUEUE_MAXSIZE)
        cancel = threading.Event()
        sentinel = object()

        def _produce() -> None:
            try:
                for delta in self._iter_local_gguf_stream(gguf_path, prompt, cancel):
                    while not cancel.is_set():
                        try:
                            delta_queue.put(delta, timeout=0.1)
                            break
                        except queue.Full:
                            continue
                    if cancel.is_set():
                        break
            except BaseException as exc:
                self._best_effort_put(delta_queue, exc)
            finally:
                cancel.set()
                self._best_effort_put(delta_queue, sentinel)

        producer = threading.Thread(target=_produce, name="gguf-stream-producer", daemon=True)
        producer.start()
        try:
            while True:
                item = await loop.run_in_executor(None, delta_queue.get)
                if item is sentinel:
                    break
                if isinstance(item, BaseException):
                    raise item
                yield item
        finally:
            cancel.set()
            while True:
                try:
                    delta_queue.get_nowait()
                except queue.Empty:
                    break

    async def _generate(self, prompt: str) -> str:
        """Executes prompt via local GGUF file or Ollama daemon (buffered)."""
        start_time = time.time()
        # 1. Try local GGUF file from models/ directory
        gguf_model = find_local_gguf_model()
        if gguf_model is not None:
            try:
                logger.info(f"[LLM] Gemma generation started via GGUF engine ({gguf_model.name})...")
                text = self._generate_with_local_gguf(gguf_model, prompt)
                logger.info(
                    f"[LLM] Gemma generation succeeded via GGUF ({len(text)} chars, "
                    f"{int((time.time() - start_time) * 1000)} ms)."
                )
                return text
            except Exception as e:
                logger.warning(f"[LLM] Gemma generation FAILED via GGUF engine: {e}. Trying Ollama sidecar...")

        # 2. Try Ollama daemon
        try:
            logger.info(f"[LLM] Gemma generation started via Ollama (model={settings.OLLAMA_MODEL})...")
            client = self._ensure_client()
            payload = {
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": self.max_output,
                    "num_ctx": self.max_context,
                    "temperature": 0.2,
                    "top_p": 0.95,
                },
            }
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            text = str(data.get("response", ""))
            eval_metrics = data.get("eval_count")
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"[LLM] Gemma generation succeeded via Ollama ({len(text)} chars"
                + (f", {eval_metrics} tokens" if isinstance(eval_metrics, int) and eval_metrics > 0 else "")
                + f", {latency_ms} ms)."
            )
            return text
        except Exception as e:
            logger.warning(f"[LLM] Gemma generation FAILED via Ollama: {e}")
            raise OllamaUnavailableError(f"Ollama generate failed: {e}") from e

    async def generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """Streams completion deltas token-by-token from either local engine.

        GGUF engine: native llama-cpp-python create_completion(stream=True) bridged onto
        the asyncio loop via a worker thread. Ollama engine: NDJSON token stream from
        /api/generate with stream=true. Raises OllamaUnavailableError so callers can
        fall back to degraded mode.
        """
        start_time = time.time()
        gguf_model = find_local_gguf_model()
        if gguf_model is not None:
            logger.info(f"[LLM] Gemma streaming generation started via GGUF engine ({gguf_model.name})...")
            produced_chars = 0
            try:
                async for delta in self._stream_local_gguf_deltas(gguf_model, prompt):
                    produced_chars += len(delta)
                    yield delta
            except Exception as e:
                logger.warning(f"[LLM] Gemma streaming generation FAILED via GGUF engine: {e}")
                raise OllamaUnavailableError(f"GGUF stream generate failed: {e}") from e
            logger.info(
                f"[LLM] Gemma streaming generation succeeded via GGUF ({produced_chars} chars, "
                f"{int((time.time() - start_time) * 1000)} ms)."
            )
            return

        logger.info(f"[LLM] Gemma streaming generation started via Ollama (model={settings.OLLAMA_MODEL})...")
        client = self._ensure_client()
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": True,
            "options": {
                "num_predict": self.max_output,
                "num_ctx": self.max_context,
                "temperature": 0.2,
                "top_p": 0.95,
            },
        }
        produced_chars = 0
        try:
            async with client.stream("POST", "/api/generate", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        chunk = json.loads(stripped)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("response", "")
                    if delta:
                        produced_chars += len(delta)
                        yield delta
                    if chunk.get("done"):
                        break
        except Exception as e:
            logger.warning(f"[LLM] Gemma streaming generation FAILED via Ollama: {e}")
            raise OllamaUnavailableError(f"Ollama stream generate failed: {e}") from e

        latency_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[LLM] Gemma streaming generation succeeded via Ollama ({produced_chars} chars, {latency_ms} ms)."
        )

    async def generate_summary(self, text: str) -> str:
        """Sends text as the prompt and returns the raw completion."""
        return await self._generate(text)

    def _parse_intelligence_json(self, raw: str) -> Dict[str, Any]:
        """Robustly extracts JSON from raw LLM output even with markdown blocks."""
        import re
        cleaned = raw.strip()
        
        # 1. Direct JSON parse
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # 2. Extract markdown ```json ... ``` block
        md_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if md_match:
            try:
                parsed = json.loads(md_match.group(1))
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

        # 3. Extract outermost { ... }
        brace_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if brace_match:
            try:
                parsed = json.loads(brace_match.group(1))
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

        return {}

    async def generate_intelligence(
        self,
        evidence: List[str],
        task: str,
        classification: DataClassification = DataClassification.UNKNOWN
    ) -> Dict[str, Any]:
        start_time = time.time()

        evidence_block = "\n".join(f"- {e}" for e in evidence)
        prompt = (
            "You are a competitive intelligence analyst for a haemophilia "
            "market team. Produce a structured signal assessment based strictly on "
            "the provided evidence. Return ONLY a valid JSON object with exactly "
            "these keys: what_changed, why_it_matters, primary_function, suggested_action.\n\n"
            f"Evidence:\n{evidence_block}\n\n"
            f"Task: {task}\n\n"
            "Return the JSON object only."
        )

        try:
            raw = await self._generate(prompt)
        except OllamaUnavailableError:
            raise

        latency = int((time.time() - start_time) * 1000)
        gguf_model = find_local_gguf_model()
        model_tag = gguf_model.name if gguf_model else settings.OLLAMA_MODEL

        metadata = ModelMetadataSchema(
            provider="local_gemma",
            mode="reasoning",
            model=model_tag,
            fallback_used=False,
            reasoning_available=True,
            actions_available=True,
            latency_ms=latency
        )

        parsed = self._parse_intelligence_json(raw)

        return {
            "what_changed": parsed.get("what_changed", raw)
            if isinstance(parsed, dict)
            else raw,
            "why_it_matters": parsed.get("why_it_matters", "") if isinstance(parsed, dict) else "",
            "primary_function": parsed.get("primary_function", "MEDICAL_AFFAIRS")
            if isinstance(parsed, dict)
            else "MEDICAL_AFFAIRS",
            "suggested_action": parsed.get(
                "suggested_action", "Suggested — requires human review: review signal with Medical Affairs lead."
            ) if isinstance(parsed, dict) else "Suggested — requires human review: review signal with Medical Affairs lead.",
            "model_metadata": metadata.model_dump()
        }

    async def is_available(self) -> bool:
        """True if a local .gguf file exists in models/ or Ollama reports the model in /api/tags."""
        if find_local_gguf_model() is not None:
            return True

        try:
            client = self._ensure_client()
            response = await client.get("/api/tags")
            response.raise_for_status()
            models = response.json().get("models", [])
            model_names = {m.get("name") for m in models}
            return settings.OLLAMA_MODEL in model_names
        except Exception as e:
            logger.debug(f"Gemma is_available check failed: {e}")
            return False