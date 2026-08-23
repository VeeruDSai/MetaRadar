"""GemmaProvider — dual-engine local reasoning provider (GGUF & Ollama).

Discovers and executes local quantized reasoning models (.gguf) from the root models/
directory via llama-cpp-python (if installed), or connects to the local Ollama daemon
(http://localhost:11434).

Never-crash contract (D-12): Any failure raises OllamaUnavailableError so ProviderFactory
safely falls through to Grok -> BART degraded mode without crashing.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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

    def _generate_with_local_gguf(self, gguf_path: Path, prompt: str) -> str:
        """Executes inference using local GGUF model via llama-cpp-python."""
        try:
            from llama_cpp import Llama
        except ImportError:
            raise OllamaUnavailableError(
                f"Local GGUF model found at {gguf_path.name}, but 'llama-cpp-python' is not installed. "
                "Install with: pip install llama-cpp-python"
            )

        if self._llama_instance is None:
            n_gpu = -1 if settings.LLM_DEVICE in ("cuda", "gpu", "auto") else 0
            logger.info(f"Loading local GGUF reasoning model from {gguf_path} (n_gpu_layers={n_gpu})...")
            self._llama_instance = Llama(
                model_path=str(gguf_path),
                n_ctx=self.max_context,
                n_gpu_layers=n_gpu,
                verbose=False,
            )

        output = self._llama_instance(
            prompt,
            max_tokens=self.max_output,
            temperature=0.2,
            stop=["</s>", "<end_of_turn>", "HUMAN:", "SYSTEM:"],
        )
        choices = output.get("choices", [])
        if choices and "text" in choices[0]:
            return str(choices[0]["text"]).strip()
        return ""

    async def _generate(self, prompt: str) -> str:
        """Executes prompt via local GGUF file or Ollama daemon."""
        # 1. Try local GGUF file from models/ directory
        gguf_model = find_local_gguf_model()
        if gguf_model is not None:
            try:
                return self._generate_with_local_gguf(gguf_model, prompt)
            except Exception as e:
                logger.warning(f"Local GGUF execution failed: {e}. Trying Ollama sidecar...")

        # 2. Try Ollama daemon
        try:
            client = self._ensure_client()
            payload = {
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": self.max_output,
                    "num_ctx": self.max_context,
                },
            }
            response = await client.post("/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            return str(data.get("response", ""))
        except Exception as e:
            logger.warning(f"Gemma/Ollama request failed: {e}")
            raise OllamaUnavailableError(f"Ollama generate failed: {e}") from e

    async def generate_summary(self, text: str) -> str:
        """Sends text as the prompt and returns the raw completion."""
        return await self._generate(text)

    async def generate_intelligence(
        self,
        evidence: List[str],
        task: str,
        classification: DataClassification = DataClassification.UNKNOWN
    ) -> Dict[str, Any]:
        start_time = time.time()

        evidence_block = "\n".join(f"- {e}" for e in evidence)
        prompt = (
            "SYSTEM: You are a competitive intelligence analyst for a haemophilia "
            "market team. Produce a structured signal assessment based strictly on "
            "the provided evidence. Return ONLY a valid JSON object with exactly "
            "these keys: what_changed, why_it_matters, primary_function, suggested_action.\n\n"
            f"HUMAN: Evidence:\n{evidence_block}\n\n"
            f"Task: {task}\n\n"
            "Respond with the JSON object only."
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

        parsed: Dict[str, Any] = {}
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Gemma response was not valid JSON; falling back to raw text.")

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