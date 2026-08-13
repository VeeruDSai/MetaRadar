import time
from typing import Any, Dict, List
from app.providers.base import LLMProvider, ProviderCapability, DataClassification
from app.schemas import ModelMetadataSchema


class DegradedProvider(LLMProvider):
    name = "bart_degraded"
    capabilities = [ProviderCapability.SUMMARIZE]

    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        self.model_name = model_name

    async def generate_summary(self, text: str) -> str:
        # Factual text summarization fallback
        cleaned = text.strip()
        if len(cleaned) > 300:
            return cleaned[:297] + "..."
        return cleaned

    async def generate_intelligence(
        self,
        evidence: List[str],
        task: str,
        classification: DataClassification = DataClassification.UNKNOWN
    ) -> Dict[str, Any]:
        """Degraded factual summary response — REASONING and ACTIONS are explicitly disabled."""
        start_time = time.time()
        summary_text = await self.generate_summary(" ".join(evidence))
        latency = int((time.time() - start_time) * 1000)

        metadata = ModelMetadataSchema(
            provider="bart",
            mode="degraded_factual",
            model=self.model_name,
            fallback_used=True,
            fallback_reason="gemma_unavailable_or_unsupported_capability",
            reasoning_available=False,
            actions_available=False,
            latency_ms=latency
        )

        return {
            "factual_summary": f"Factual Summary: {summary_text}",
            "evidence_count": len(evidence),
            "mode": "degraded_factual",
            "model_metadata": metadata.model_dump()
        }
