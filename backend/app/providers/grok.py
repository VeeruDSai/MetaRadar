import logging
import time
from typing import Any, Dict, List
from app.providers.base import LLMProvider, ProviderCapability, DataClassification
from app.core.config import settings
from app.schemas import ModelMetadataSchema

logger = logging.getLogger(__name__)


class GrokProvider(LLMProvider):
    name = "grok"
    capabilities = [
        ProviderCapability.SUMMARIZE,
        ProviderCapability.CLASSIFY,
        ProviderCapability.REASON,
        ProviderCapability.GENERATE_ACTIONS,
        ProviderCapability.STRUCTURED_OUTPUT
    ]

    def __init__(self, api_key: str = settings.XAI_API_KEY or ""):
        self.api_key = api_key
        self.model_name = "grok-beta"

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

    async def generate_summary(self, text: str) -> str:
        # Mocked structure for local test
        return f"[Grok Summary]: {text[:200]}..."

    async def generate_intelligence(
        self,
        evidence: List[str],
        task: str,
        classification: DataClassification = DataClassification.UNKNOWN
    ) -> Dict[str, Any]:
        if not self.validate_privacy_gate(classification):
            raise PermissionError(f"Privacy gate rejected external API transmission for classification '{classification}'")

        start_time = time.time()
        # Simulated Grok JSON Schema structured output
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

        return {
            "what_changed": f"External market development detected from {len(evidence)} evidence sources.",
            "why_it_matters": f"Pertains to competitor strategy: {task}",
            "primary_function": "MEDICAL_AFFAIRS",
            "suggested_action": "Suggested — requires human review: Prepare scientific FAQ for Medical Affairs.",
            "model_metadata": metadata.model_dump()
        }
