from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.schemas import ModelMetadataSchema


class ProviderCapability(str, Enum):
    SUMMARIZE = "summarize"
    CLASSIFY = "classify"
    REASON = "reason"
    GENERATE_ACTIONS = "generate_actions"
    STRUCTURED_OUTPUT = "structured_output"


class DataClassification(str, Enum):
    PUBLIC = "public"
    SYNTHETIC = "synthetic"
    CONFIDENTIAL = "confidential"
    INTERNAL = "internal"
    PATIENT_IDENTIFIABLE = "patient_identifiable"
    UNKNOWN = "unknown"


class LLMProvider:
    name: str = "base"
    capabilities: List[ProviderCapability] = []

    def supports(self, capability: ProviderCapability) -> bool:
        return capability in self.capabilities

    async def generate_summary(self, text: str) -> str:
        raise NotImplementedError

    async def generate_intelligence(
        self,
        evidence: List[str],
        task: str,
        classification: DataClassification = DataClassification.UNKNOWN
    ) -> Dict[str, Any]:
        raise NotImplementedError
