import pytest
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.core.config import settings
from app.core.domain_config import get_domain_config


def test_domain_config_loading():
    config = get_domain_config()
    assert config.domain_config_version == "v5.1.0"
    assert len(config.assets) >= 7
    assert config.confluence.minimum_independent_signals == 3
    assert config.confluence.emerging_threshold == 2


def test_app_settings_defaults():
    assert settings.PROJECT_NAME == "MetaRadar"
    assert settings.VERSION == "5.1.0"
    assert settings.EMBEDDING_DIMENSION == 384
