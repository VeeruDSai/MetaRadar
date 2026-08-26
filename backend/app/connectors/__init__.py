"""Connector registry — Phase 1, Phase 9 & Phase 10 source adapters.

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
from app.connectors.biopharma_dive import BioPharmaDiveRSSConnector

ALL_CONNECTORS = [
    PubMedConnector(),
    ClinicalTrialsConnector(),
    NewsAPIConnector(),
    OpenFDAConnector(),
    EMARSSConnector(),
    FiercePharmaRSSConnector(),
    ETPharmaRSSConnector(),
    BioPharmaDiveRSSConnector(),
]

__all__ = [
    "PubMedConnector",
    "ClinicalTrialsConnector",
    "NewsAPIConnector",
    "OpenFDAConnector",
    "EMARSSConnector",
    "FiercePharmaRSSConnector",
    "ETPharmaRSSConnector",
    "BioPharmaDiveRSSConnector",
    "ALL_CONNECTORS",
]