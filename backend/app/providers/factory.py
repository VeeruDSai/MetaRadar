import logging
import os
from typing import Any, Dict, List, Optional
from app.providers.base import LLMProvider, ProviderCapability, DataClassification
from app.providers.gemma import GemmaProvider
from app.providers.grok import GrokProvider
from app.providers.degraded import DegradedProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProviderFactory:
    def __init__(self):
        self.gemma = GemmaProvider()
        self.grok = GrokProvider()
        self.degraded = DegradedProvider()

    async def execute_task(
        self,
        required_capability: ProviderCapability,
        evidence: List[str],
        task: str,
        classification: DataClassification = DataClassification.PUBLIC
    ) -> Dict[str, Any]:
        """
        Executes an intelligence task using the configured fallback chain:
        Local Gemma -> Grok (if enabled & permitted) -> BART Degraded Mode (summarize ONLY).
        """
        # 1. Try Local Gemma
        if settings.LLM_PROVIDER in ["local", "auto"] and self.gemma.supports(required_capability):
            try:
                return await self.gemma.generate_intelligence(evidence, task, classification)
            except Exception as e:
                logger.warning(f"Gemma execution failed: {e}. Falling back...")

        # 2. Try Grok Hosted Fallback (if key is present / xai selected / fallback enabled)
        has_grok_key = bool(settings.effective_xai_api_key or os.environ.get("XAI_API_KEY") or os.environ.get("GROK_API_KEY"))
        if has_grok_key and (settings.ENABLE_GROK_FALLBACK or settings.LLM_PROVIDER in ["xai", "auto", "local"]) and self.grok.supports(required_capability):
            try:
                if self.grok.validate_privacy_gate(classification):
                    return await self.grok.generate_intelligence(evidence, task, classification)
            except Exception as e:
                logger.warning(f"Grok fallback failed: {e}. Falling back to degraded BART...")

        # 3. Fallback to Degraded BART Mode (Summarize ONLY)
        logger.info("Delegating task to BART Degraded Factual Summary provider...")
        return await self.degraded.generate_intelligence(evidence, task, classification)


provider_factory = ProviderFactory()
