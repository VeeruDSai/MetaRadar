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
        
        # Structure evidence items into clean factual bullet points
        points = []
        for idx, item in enumerate(evidence, 1):
            cleaned = item.strip()
            if len(cleaned) > 280:
                cleaned = cleaned[:277] + "..."
            points.append(f"• {cleaned}")
        
        summary_body = "\n\n".join(points) if points else "No evidence records available."
        formatted_summary = f"**Source-Grounded Factual Summary** *(AI reasoning fallback active)*:\n\n{summary_body}"
        
        latency = int((time.time() - start_time) * 1000)

        metadata = ModelMetadataSchema(
            provider="bart",
            mode="degraded_factual",
            model=self.model_name,
            fallback_used=True,
            fallback_reason="gemma_offline_grok_fallback",
            reasoning_available=False,
            actions_available=False,
            latency_ms=latency
        )

        return {
            "factual_summary": formatted_summary,
            "evidence_count": len(evidence),
            "mode": "degraded_factual",
            "model_metadata": metadata.model_dump()
        }
