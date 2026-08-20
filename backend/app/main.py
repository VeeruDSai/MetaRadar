import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.core.domain_config import get_domain_config
from app.core.logging import configure_structlog
from app.core.middleware import CorrelationIdMiddleware
from app.api.v1.endpoints import (
    health,
    signals,
    pipeline,
    search,
    feedback,
    intelligence,
    registry,
    cache,
    observability,
)

# Initialize structured JSON logging
configure_structlog(json_logs=True)
logger = structlog.get_logger("metaradar.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("service_startup", message="Initializing MetaRadar v5.1 Backend Service...")
    try:
        domain_cfg = get_domain_config()
        logger.info(
            "domain_config_loaded",
            disease_area=domain_cfg.disease_area,
            version=domain_cfg.domain_config_version,
        )
    except Exception as e:
        logger.error("domain_config_load_failed", error=str(e))

    yield

    # Shutdown
    logger.info("service_shutdown", message="Shutting down MetaRadar v5.1 Backend Service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Correlation ID & Observability Tracing Middleware (must be added first to wrap outer request)
app.add_middleware(CorrelationIdMiddleware)

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
app.include_router(intelligence.router, prefix=f"{settings.API_V1_STR}", tags=["Intelligence Views"])
app.include_router(registry.router, prefix=f"{settings.API_V1_STR}", tags=["Registry"])
app.include_router(observability.router, prefix=f"{settings.API_V1_STR}", tags=["Observability & System Health"])
app.include_router(cache.router, prefix=f"{settings.API_V1_STR}", tags=["Cache Management"])
app.include_router(pipeline.router, prefix=f"{settings.API_V1_STR}", tags=["Pipeline Execution"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["Search & Retrieval"])
app.include_router(feedback.router, prefix=f"{settings.API_V1_STR}", tags=["Stakeholder Calibration & Feedback"])


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }
