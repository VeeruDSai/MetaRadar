import pytest
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.services.pii import PIIPHIScrubber
from app.providers.grok import GrokProvider
from app.providers.base import DataClassification
from app.core.config import settings


def test_pii_scrubber_patterns():
    # Raw email
    s1, p1, _ = PIIPHIScrubber.scrub("Contact doc@hospital.org for details")
    assert p1 is True
    assert "[EMAIL_REDACTED]" in s1

    # Phone number
    s2, p2, _ = PIIPHIScrubber.scrub("Call 555-123-4567 immediately")
    assert p2 is True
    assert "[PHONE_REDACTED]" in s2

    # SSN & MRN & DOB
    s3, p3, c3 = PIIPHIScrubber.scrub("SSN 123-45-6789 MRN: #987654 DOB: 01/01/1990")
    assert p3 is True
    assert "[SSN_REDACTED]" in s3
    assert "[MRN_REDACTED]" in s3
    assert "[PATIENT_DOB_REDACTED]" in s3


def test_classification_logic():
    assert PIIPHIScrubber.classify_payload("Clean text", source_type="pubmed") == DataClassification.PUBLIC
    assert PIIPHIScrubber.classify_payload("Text with user@site.com", source_type="pubmed") == DataClassification.CONFIDENTIAL
    assert PIIPHIScrubber.classify_payload("Demo signal", source_type="synthetic") == DataClassification.SYNTHETIC


@pytest.mark.asyncio
async def test_privacy_gate_external_bypass_prevention(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", True)
    grok = GrokProvider(api_key="mock-key")

    # Public data -> Passes gate
    assert grok.validate_privacy_gate(DataClassification.PUBLIC) is True
    assert grok.validate_privacy_gate(DataClassification.SYNTHETIC) is True

    # Confidential or Unknown data -> Blocked by Privacy Gate
    assert grok.validate_privacy_gate(DataClassification.CONFIDENTIAL) is False
    assert grok.validate_privacy_gate(DataClassification.UNKNOWN) is False

    # Verify generate_intelligence raises PermissionError on Confidential payload
    with pytest.raises(PermissionError):
        await grok.generate_intelligence(
            evidence=["Patient record user@site.com"],
            task="Task",
            classification=DataClassification.CONFIDENTIAL
        )
