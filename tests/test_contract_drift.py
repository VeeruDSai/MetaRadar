import pytest
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app


def test_contract_sync_drift():
    openapi_schema = app.openapi()
    assert openapi_schema is not None
    assert "paths" in openapi_schema
    assert "/api/v1/health" in openapi_schema["paths"]
    assert "/api/v1/signals" in openapi_schema["paths"]
    assert "/api/v1/confluence" in openapi_schema["paths"]
    assert "/api/v1/lifecycles" in openapi_schema["paths"]
    assert "/api/v1/red-team" in openapi_schema["paths"]
    assert "/api/v1/missing-signals" in openapi_schema["paths"]
    assert "/api/v1/developments" in openapi_schema["paths"]
    assert "/api/v1/sources" in openapi_schema["paths"]
    assert "/api/v1/cache/clear" in openapi_schema["paths"]

    canonical_ts_path = base_dir / "frontend" / "types" / "api.ts"
    assert canonical_ts_path.exists()
    
    with open(canonical_ts_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "export interface Signal" in content
    assert "export interface HealthResponse" in content
    assert "export interface ModelMetadata" in content
    assert "export interface ConfluenceAlertItem" in content
    assert "export interface LifecycleTimelineItem" in content
    assert "export interface ContradictionItem" in content
    assert "export interface MissingSignalWatchItem" in content
    assert "export interface DevelopmentSummary" in content
    assert "export interface SourceRegistryItem" in content
    assert "export interface CacheClearResponse" in content
    assert "export interface SignalFilterParams" in content
