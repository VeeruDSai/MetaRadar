import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.domain_config import get_domain_config
from app.api.v1.endpoints import health, signals, pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing MetaRadar v5.1 Backend Service...")
    try:
        domain_cfg = get_domain_config()
        logger.info(f"Loaded Domain Config: '{domain_cfg.disease_area}' (v{domain_cfg.domain_config_version})")
    except Exception as e:
        logger.error(f"Failed to load DomainConfig: {e}")

    yield

    # Shutdown
    logger.info("Shutting down MetaRadar v5.1 Backend Service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware Setup
if settings.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Router Registrations
app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health & Diagnostics"])
app.include_router(signals.router, prefix=f"{settings.API_V1_STR}", tags=["Signals & Intelligence"])
app.include_router(pipeline.router, prefix=f"{settings.API_V1_STR}", tags=["Pipeline Execution"])



@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }
