"""GrokProvider — real xAI Grok API client (D-13, D-14, D-16).

Strict privacy gate (``validate_privacy_gate``) is enforced before ANY external
transmission: only PUBLIC / SYNTHETIC payloads may reach api.x.ai. When no
XAI_API_KEY is configured, ``GrokUnavailableError`` is raised so ProviderFactory
falls through to BART degraded mode — CI stays green without a key (D-16).
"""

import json
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.base import LLMProvider, ProviderCapability, DataClassification
from app.schemas import ModelMetadataSchema

logger = get_logger("grok_provider")

XAI_API_URL = "https://api.x.ai/v1/chat/completions"
XAI_MODEL = "grok-beta"


class GrokUnavailableError(Exception):
    """Raised when the Grok provider cannot execute (no key, or API failure).

    Caught by ProviderFactory which falls through to BART degraded mode.
    """


class GrokProvider(LLMProvider):
    name = "grok"
    capabilities = [
        ProviderCapability.SUMMARIZE,
        ProviderCapability.CLASSIFY,
        ProviderCapability.REASON,
        ProviderCapability.GENERATE_ACTIONS,
        ProviderCapability.STRUCTURED_OUTPUT
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key is not None else (settings.XAI_API_KEY or "")
        self.model_name = XAI_MODEL
        self._client: Optional[httpx.AsyncClient] = None

    def _ensure_client(self) -> httpx.AsyncClient:
        """Lazily creates the xAI HTTP client (connect=5s, read=60s)."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(connect=5.0, read=60.0)
            )
        return self._client

    def validate_privacy_gate(self, classification: DataClassification) -> bool:
        """Mandatory Privacy Gate immediately before transmission."""
        if not settings.ENABLE_GROK_FALLBACK:
            logger.warning("Grok execution blocked: ENABLE_GROK_FALLBACK is False")
            return False

        if not self.api_key:
            logger.warning("Grok execution blocked: Missing XAI_API_KEY")
            return False

        if classification in [DataClassification.PUBLIC, DataClassification.SYNTHETIC]:
            return True

        logger.warning(f"Grok execution BLOCKED by Privacy Gate. Data classification: '{classification}' rejected.")
        return False

    async def _chat(
        self,
        messages: List[Dict[str, str]],
        classification: DataClassification = DataClassification.UNKNOWN,
    ) -> str:
        """POST /v1/chat/completions; returns the assistant content text.

        Privacy gate (validate_privacy_gate) is enforced before ANY external
        transmission: only PUBLIC / SYNTHETIC payloads may reach api.x.ai.

        Raises GrokUnavailableError on any API failure (auth, timeout, HTTP,
        malformed response) — never swallowed silently.
        """
        if not self.api_key:
            raise GrokUnavailableError("No XAI_API_KEY configured")

        if not self.validate_privacy_gate(classification):
            raise PermissionError(
                f"Privacy gate rejected external API transmission for classification '{classification}'"
            )

        try:
            client = self._ensure_client()
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 1024,
                "response_format": {"type": "json_object"},
            }
            response = await client.post(
                XAI_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return str(content)
        except Exception as e:
            logger.warning(f"Grok API request failed: {e}")
            raise GrokUnavailableError(f"Grok API call failed: {e}") from e

    async def generate_summary(
        self,
        text: str,
        classification: DataClassification = DataClassification.UNKNOWN,
    ) -> str:
        """Summarizes text via the Grok chat completions API.

        Unclassified text defaults to DataClassification.UNKNOWN, which the
        privacy gate blocks. Callers must pass PUBLIC or SYNTHETIC to transmit.
        """
        messages = [
            {"role": "system", "content": "You are a precise medical intelligence summarizer."},
            {"role": "user", "content": f"Summarize the following evidence concisely:\n\n{text}"},
        ]
        return await self._chat(messages, classification=classification)

    async def generate_intelligence(
        self,
        evidence: List[str],
        task: str,
        classification: DataClassification = DataClassification.UNKNOWN
    ) -> Dict[str, Any]:
        # Mocked CI path (D-16): no key configured -> GrokUnavailableError so
        # the factory falls through to BART. Checked BEFORE the privacy gate so
        # a missing key reads as provider unavailability, not a data violation.
        if not self.api_key:
            raise GrokUnavailableError("No XAI_API_KEY configured")

        if not self.validate_privacy_gate(classification):
            raise PermissionError(f"Privacy gate rejected external API transmission for classification '{classification}'")

        start_time = time.time()

        evidence_block = "\n".join(f"- {e}" for e in evidence)
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a competitive intelligence analyst for a haemophilia market team. "
                    "Analyze the provided public evidence and return STRICT JSON with exactly these "
                    "keys: what_changed, why_it_matters, suggested_action."
                ),
            },
            {
                "role": "user",
                "content": f"Evidence:\n{evidence_block}\n\nTask: {task}\n\nReturn the JSON object only.",
            },
        ]

        raw = await self._chat(messages, classification=classification)
        latency = int((time.time() - start_time) * 1000)

        metadata = ModelMetadataSchema(
            provider="xai",
            mode="reasoning",
            model=self.model_name,
            fallback_used=True,
            fallback_reason="gemma_unavailable",
            reasoning_available=True,
            actions_available=True,
            latency_ms=latency
        )

        parsed: Dict[str, Any] = {}
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Grok response was not valid JSON; falling back to raw text.")

        if not isinstance(parsed, dict):
            parsed = {}

        return {
            "what_changed": parsed.get("what_changed", raw),
            "why_it_matters": parsed.get("why_it_matters", ""),
            "primary_function": parsed.get("primary_function", "MEDICAL_AFFAIRS"),
            "suggested_action": parsed.get(
                "suggested_action",
                "Suggested — requires human review: Prepare scientific FAQ for Medical Affairs.",
            ),
            "model_metadata": metadata.model_dump()
        }