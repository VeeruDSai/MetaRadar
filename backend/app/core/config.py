import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ROOT_DIR = _BACKEND_DIR.parent
_ENV_FILES = [
    str(_ROOT_DIR / ".env"),
    str(_BACKEND_DIR / ".env"),
    ".env",
    "../.env",
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Metadata
    PROJECT_NAME: str = "MetaRadar"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "5.1.0"

    # Database & Redis
    # Local-dev defaults only. Override via .env for any shared or deployed environment.
    DATABASE_URL: str = "postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & CORS
    SECRET_KEY: str = "dev-secret-change-in-production"
    SESSION_LIFETIME_SECONDS: int = 28800      # 8 hours absolute
    SESSION_IDLE_TIMEOUT_SECONDS: int = 3600   # 1 hour idle
    SESSION_COOKIE_SECURE: bool = False       # True in HTTPS production
    DEMO_MODE: bool = True                    # Enables /auth/demo-login
    DEMO_AUTO_SEED_USERS: bool = True
    DEMO_USER_PASSWORD: Optional[str] = None
    AUTH_RATE_LIMIT_PER_MINUTE: int = 5
    CORS_ORIGINS: str = "http://localhost:3000"
    METARADAR_API_KEY: Optional[str] = None
    MUTATION_RATE_LIMIT_PER_MINUTE: int = 60

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

    # Hosted Fallback Settings (Grok / xAI)
    ENABLE_GROK_FALLBACK: bool = False
    XAI_API_KEY: Optional[str] = None
    GROK_API_KEY: Optional[str] = None

    @property
    def effective_xai_api_key(self) -> Optional[str]:
        return self.XAI_API_KEY or self.GROK_API_KEY

    # Local Models Directory & GGUF Configuration
    MODELS_DIR: str = str(_ROOT_DIR / "models")
    LOCAL_GGUF_MODEL: Optional[str] = None
    LOCAL_GGUF_PATH: Optional[str] = None

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

    # NewsAPI Key (supports NEWSAPI_KEY or NEWS_API_KEY)
    NEWSAPI_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None

    @property
    def effective_newsapi_key(self) -> Optional[str]:
        return self.NEWSAPI_KEY or self.NEWS_API_KEY

    # NCBI PubMed API Key & Identifiers
    NCBI_API_KEY: Optional[str] = None
    NCBI_TOOL: str = "MetaRadar"
    NCBI_EMAIL: str = "metaradar@example.com"

    # OpenFDA API Key (optional for higher rate limits)
    OPENFDA_API_KEY: Optional[str] = None

    # Autonomous Background Scheduler Settings
    ENABLE_BACKGROUND_SCHEDULER: bool = True
    SCHEDULER_CT_INTERVAL_MINUTES: int = 60
    SCHEDULER_PUBMED_INTERVAL_MINUTES: int = 60
    SCHEDULER_EMA_INTERVAL_MINUTES: int = 30
    SCHEDULER_FDA_INTERVAL_MINUTES: int = 30
    SCHEDULER_NEWS_INTERVAL_MINUTES: int = 15
    SCHEDULER_JITTER_PERCENT: int = 10
    SCHEDULER_MAX_BACKOFF_MINUTES: int = 120
    SCHEDULER_FAILURE_THRESHOLD: int = 3
    SCHEDULER_STALE_MULTIPLIER: float = 2.5


settings = Settings()


def configuration_error_for(source_id: str) -> Optional[str]:
    """Pure, side-effect-free evaluator for connector and model configuration state."""
    src = source_id.lower().strip()
    if src == "newsapi":
        key = (settings.NEWSAPI_KEY or settings.NEWS_API_KEY or "").strip()
        if not key or key.lower() in ("your_newsapi_key_here", "placeholder", "xxx", "none"):
            return "CONFIGURATION_ERROR: NEWSAPI_KEY missing (required) — get a key at https://newsapi.org/register (NewsAPI developer account) and set NEWSAPI_KEY in .env"
    if src in ("grok", "xai") and settings.ENABLE_GROK_FALLBACK:
        key = (settings.effective_xai_api_key or "").strip()
        if not key or key.lower() in ("your_xai_api_key_here", "placeholder", "xxx", "none"):
            return "CONFIGURATION_ERROR: XAI_API_KEY missing (required when ENABLE_GROK_FALLBACK=true) — get a key from https://console.x.ai and set XAI_API_KEY in .env"
    return None

