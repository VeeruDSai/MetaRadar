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
