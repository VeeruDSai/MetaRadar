import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field


class DiseaseConfig(BaseModel):
    id: str
    name: str
    icd10: str
    deficiency: str
    description: str


class AssetConfig(BaseModel):
    id: str
    brand_name: str
    generic_name: str
    company: str
    mechanism: str
    modality: str
    indication: str
    approval_status: str
    approval_date: Optional[str] = None
    jurisdiction: Optional[str] = None
    is_novo_nordisk: bool = False


class ConfluenceConfig(BaseModel):
    emerging_threshold: int = 2
    minimum_independent_signals: int = 3
    time_window_hours: int = 48


class FunctionConfig(BaseModel):
    id: str
    name: str


class ConnectorQueryProfile(BaseModel):
    """A single config-driven query profile for a source connector.

    Connectors execute config — they never invent queries (D-08/D-10).
    Field set is the union across the five Phase 1 sources; unused fields
    are simply omitted per source.
    """

    id: str
    queries: Optional[List[str]] = None          # PubMed: boolean queries
    conditions: Optional[List[str]] = None       # ClinicalTrials.gov: condition terms
    interventions: Optional[List[str]] = None    # ClinicalTrials.gov: intervention terms
    sponsor_keywords: Optional[List[str]] = None # ClinicalTrials.gov: sponsor keywords
    query: Optional[str] = None                  # NewsAPI: single query string
    language: Optional[str] = None               # NewsAPI: language code
    search_terms: Optional[List[str]] = None     # OpenFDA: substance/search terms
    keywords: Optional[List[str]] = None         # EMA / FDA RSS: keyword filter
    rss_url: Optional[str] = None                # Profile-specific RSS URL override


class ConnectorConfig(BaseModel):
    """Per-source connector configuration (query blocks + window/quota policy)."""

    freshness_class: str
    tier: int = 1
    backfill_days: int
    rolling_window_days: int
    max_results_per_profile: Optional[int] = None
    quota_per_day: Optional[int] = None
    base_url: Optional[str] = None
    rss_url: Optional[str] = None
    profiles: List[ConnectorQueryProfile]


class CrossSourceGroupConfig(BaseModel):
    """Rules for the cross-source source-independence classifier (D-17)."""

    title_similarity_threshold: float
    date_window_hours: int
    entity_overlap_min: int


class CrossSourceConfig(BaseModel):
    group_assignment: CrossSourceGroupConfig


class DomainConfig(BaseModel):
    domain_config_version: str = "v5.1.0"
    disease_area: str
    pilot_area: str
    diseases: List[DiseaseConfig]
    factor_classifications: List[str]
    inhibitor_categories: List[str]
    patient_segments: List[str]
    assets: List[AssetConfig]
    signal_types: List[Dict[str, str]]
    lifecycle_stages: List[str]
    confluence: ConfluenceConfig
    functions: List[FunctionConfig]
    baseline_routing_matrix: Dict[str, Dict[str, Any]]
    source_tiers: Dict[str, List[str]] = Field(default_factory=dict)
    # Phase 1 ingestion extensions — optional & backward compatible:
    # existing configs without these keys load without error.
    connectors: Dict[str, ConnectorConfig] = Field(default_factory=dict)
    cross_source: Optional[CrossSourceConfig] = None
    # Phase 2 intelligence extensions:
    lag_thresholds: Dict[str, int] = Field(default_factory=lambda: {
        "announced": 120,
        "in_trial": 180,
        "interim_result": 120,
        "final_result": 180,
        "congress_publication": 90,
        "regulatory_development": 270,
        "approved": 365,
        "post_market": 365,
        "discontinued": 730,
    })


_domain_config_cache: Optional[DomainConfig] = None


def get_domain_config(config_path: Optional[str] = None) -> DomainConfig:
    global _domain_config_cache
    if _domain_config_cache is not None and config_path is None:
        return _domain_config_cache

    if config_path is None:
        # Default path relative to workspace
        base_dir = Path(__file__).resolve().parents[3]
        config_path = os.getenv("DOMAIN_CONFIG_PATH", str(base_dir / "config" / "haemophilia.yaml"))

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Domain configuration file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)

    _domain_config_cache = DomainConfig(**raw_data)
    return _domain_config_cache
