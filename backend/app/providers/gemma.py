import logging
import time
from typing import Any, Dict, List
from app.providers.base import LLMProvider, ProviderCapability, DataClassification
from app.core.config import settings
from app.schemas import ModelMetadataSchema

logger = logging.getLogger(__name__)


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
        self.model_name = settings.LOCAL_LLM_MODEL
        self.device = settings.LLM_DEVICE
        self.dtype = settings.LLM_DTYPE
        self.max_context = settings.MAX_CONTEXT_TOKENS
        self.max_output = settings.MAX_OUTPUT_TOKENS

    async def generate_summary(self, text: str) -> str:
        truncated = text[:self.max_context]
        return f"[Gemma 3 4B Summary]: {truncated[:200]}..."

    async def generate_intelligence(
        self,
        evidence: List[str],
        task: str,
        classification: DataClassification = DataClassification.UNKNOWN
    ) -> Dict[str, Any]:
        start_time = time.time()
        # Simulated local Gemma 3 4B execution
        latency = int((time.time() - start_time) * 1000)

        metadata = ModelMetadataSchema(
            provider="local_gemma",
            mode="reasoning",
            model=self.model_name,
            fallback_used=False,
            fallback_reason=None,
            reasoning_available=True,
            actions_available=True,
            latency_ms=latency
        )

        return {
            "what_changed": f"Significant haemophilia signal identified across {len(evidence)} evidence excerpts.",
            "why_it_matters": f"Directly impacts therapeutic landscape regarding {task}.",
            "primary_function": "MEDICAL_AFFAIRS",
            "suggested_action": "Suggested — requires human review: Escalate trial readout to Medical Affairs lead.",
            "model_metadata": metadata.model_dump()
        }
