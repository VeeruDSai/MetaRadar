"""Connector registry — the five Phase 1 source adapters (plan §4.11).

Importing this module instantiates one connector per source; instances load
their per-source query blocks from the haemophilia domain config.
"""

from app.connectors.pubmed import PubMedConnector
from app.connectors.clinical_trials import ClinicalTrialsConnector
from app.connectors.newsapi import NewsAPIConnector
from app.connectors.fda import OpenFDAConnector
from app.connectors.ema import EMARSSConnector

ALL_CONNECTORS = [
    PubMedConnector(),
    ClinicalTrialsConnector(),
    NewsAPIConnector(),
    OpenFDAConnector(),
    EMARSSConnector(),
]

__all__ = [
    "PubMedConnector",
    "ClinicalTrialsConnector",
    "NewsAPIConnector",
    "OpenFDAConnector",
    "EMARSSConnector",
    "ALL_CONNECTORS",
]