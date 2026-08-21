import pytest
from app.core.config import configuration_error_for, settings
from app.connectors.newsapi import NewsAPIConnector
from app.connectors.base import ProfileRunResult


def test_configuration_error_for_newsapi_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "NEWSAPI_KEY", "")
    err = configuration_error_for("newsapi")
    assert err is not None
    assert "NEWSAPI_KEY" in err
    assert "https://newsapi.org/register" in err


def test_configuration_error_for_newsapi_placeholder_key(monkeypatch):
    monkeypatch.setattr(settings, "NEWSAPI_KEY", "your_newsapi_key_here")
    err = configuration_error_for("newsapi")
    assert err is not None
    assert "NEWSAPI_KEY" in err


def test_configuration_error_for_newsapi_valid_key(monkeypatch):
    monkeypatch.setattr(settings, "NEWSAPI_KEY", "real_valid_key_12345678")
    err = configuration_error_for("newsapi")
    assert err is None


def test_configuration_error_for_grok_when_disabled(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", False)
    monkeypatch.setattr(settings, "XAI_API_KEY", "")
    err = configuration_error_for("grok")
    assert err is None


def test_configuration_error_for_grok_when_enabled_and_missing(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", True)
    monkeypatch.setattr(settings, "XAI_API_KEY", "")
    err = configuration_error_for("grok")
    assert err is not None
    assert "XAI_API_KEY" in err
    assert "https://console.x.ai" in err


def test_configuration_error_for_unauthenticated_sources():
    # PubMed, ClinicalTrials, OpenFDA, EMA do not require mandatory private API keys
    assert configuration_error_for("pubmed") is None
    assert configuration_error_for("clinical_trials") is None
    assert configuration_error_for("openfda") is None
    assert configuration_error_for("ema") is None


@pytest.mark.asyncio
async def test_newsapi_connector_missing_key_status(monkeypatch):
    monkeypatch.setattr(settings, "NEWSAPI_KEY", "")
    connector = NewsAPIConnector()
    
    # Run single profile
    res = await connector.run_profile(None, "commercial_monitoring")
    assert res.status == "CONFIGURATION_ERROR"
    assert "NEWSAPI_KEY" in res.error_detail
    assert res.fetched == 0
