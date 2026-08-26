"""Connector registry — the five Phase 1 source adapters (plan §4.11).

Importing this module instantiates one connector per source; instances load
their per-source query blocks from the haemophilia domain config.
"""

from app.connectors.pubmed import PubMedConnector
from app.connectors.clinical_trials import ClinicalTrialsConnector
from app.connectors.newsapi import NewsAPIConnector
from app.connectors.fda import OpenFDAConnector
from app.connectors.ema import EMARSSConnector
from app.connectors.fierce_pharma import FiercePharmaRSSConnector
from app.connectors.et_pharma import ETPharmaRSSConnector

ALL_CONNECTORS = [
    PubMedConnector(),
    ClinicalTrialsConnector(),
    NewsAPIConnector(),
    OpenFDAConnector(),
    EMARSSConnector(),
    FiercePharmaRSSConnector(),
    ETPharmaRSSConnector(),
]

__all__ = [
    "PubMedConnector",
    "ClinicalTrialsConnector",
    "NewsAPIConnector",
    "OpenFDAConnector",
    "EMARSSConnector",
    "FiercePharmaRSSConnector",
    "ETPharmaRSSConnector",
    "ALL_CONNECTORS",
]