"""GemmaProvider — real Ollama-backed Gemma 3 4B inference (D-09, D-12).

Calls the Ollama sidecar over HTTP (POST /api/generate) instead of simulating
local inference. Never-crash contract (D-12): any exception raises
``OllamaUnavailableError`` so ProviderFactory falls through to Grok -> BART
degraded mode. ``is_available()`` probes GET /api/tags and never raises.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from app.providers.base import LLMProvider, ProviderCapability, DataClassification
from app.core.config import settings
from app.schemas import ModelMetadataSchema

logger = logging.getLogger(__name__)


class OllamaUnavailableError(Exception):
    """Raised when the Ollama sidecar cannot complete a request.

    Caught by ProviderFactory which falls through to Grok -> BART degraded.
    """


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

    def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily creates the Ollama HTTP client (connect=5s, read=30s).

        Lazy so tests can inject a mocked client before the first request
        without constructing an unused real client.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.OLLAMA_HOST,
                timeout=httpx.Timeout(connect=5.0, read=30.0)  # Gemma inference can be slow
            )
        return self._client

    async def _generate(self, prompt: str) -> str:
        """POST /api/generate to Ollama; returns the completion text.

        Any exception (connection refused, timeout, HTTP error, malformed
        response) is wrapped in ``OllamaUnavailableError`` — never swallowed.
        """
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
        """Sends text as the prompt and returns the raw Ollama completion."""
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

        metadata = ModelMetadataSchema(
            provider="local_gemma",
            mode="reasoning",
            model=settings.OLLAMA_MODEL,
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
        """True if the Ollama sidecar reports settings.OLLAMA_MODEL in /api/tags.

        Never raises — returns False on any error (connection, timeout, HTTP,
        or model missing) so health reporting stays honest and non-blocking.
        """
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