import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Metadata
    PROJECT_NAME: str = "MetaRadar"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "5.1.0"

    # Database & Redis
    DATABASE_URL: str = "postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # LLM Provider & Hardware Settings
    LLM_PROVIDER: str = "local"  # local | xai | auto
    LOCAL_LLM_MODEL: str = "google/gemma-3-4b-it"
    LLM_DEVICE: str = "auto"
    LLM_DTYPE: str = "int4"
    MAX_CONTEXT_TOKENS: int = 2048
    MAX_OUTPUT_TOKENS: int = 512

    # Hosted Fallback Settings
    ENABLE_GROK_FALLBACK: bool = False
    XAI_API_KEY: Optional[str] = None

    # Ollama Sidecar
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3:4b"   # matches LOCAL_LLM_MODEL name in Ollama registry

    # Embedding Model Settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODEL_REVISION: str = "e4bb823e5956b6277b069d276b978c48a73507c7"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_MAX_SEQ_LENGTH: int = 256

    # Retention
    RAW_SIGNAL_RETENTION_DAYS: int = 30

    # NewsAPI Key
    NEWSAPI_KEY: Optional[str] = None


settings = Settings()


def configuration_error_for(source_id: str) -> Optional[str]:
    """Pure, side-effect-free evaluator for connector and model configuration state."""
    src = source_id.lower().strip()
    if src == "newsapi":
        key = (settings.NEWSAPI_KEY or "").strip()
        if not key or key.lower() in ("your_newsapi_key_here", "placeholder", "xxx", "none"):
            return "CONFIGURATION_ERROR: NEWSAPI_KEY missing (required) — get a key at https://newsapi.org/register (NewsAPI developer account) and set NEWSAPI_KEY in .env"
    if src in ("grok", "xai") and settings.ENABLE_GROK_FALLBACK:
        key = (settings.XAI_API_KEY or "").strip()
        if not key or key.lower() in ("your_xai_api_key_here", "placeholder", "xxx", "none"):
            return "CONFIGURATION_ERROR: XAI_API_KEY missing (required when ENABLE_GROK_FALLBACK=true) — get a key from https://console.x.ai and set XAI_API_KEY in .env"
    return None

