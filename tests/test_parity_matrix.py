import json
import pytest
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
manifest_path = base_dir / "docs" / "manifests" / "feature_parity_manifest.json"
openapi_path = base_dir / "contracts" / "openapi.json"
matrix_doc_path = base_dir / "docs" / "FEATURE_PARITY_MATRIX.md"


def test_parity_manifest_structure():
    assert manifest_path.exists(), "Manifest file does not exist"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "version" in data
    assert "features" in data
    assert len(data["features"]) >= 10

    valid_statuses = {"WIRED", "PARTIAL", "NOT_WIRED", "DEFERRED"}
    for item in data["features"]:
        assert "doc_spec" in item and item["doc_spec"].strip()
        assert "feature" in item and item["feature"].strip()
        assert "component" in item and item["component"].strip()
        assert "endpoint" in item and item["endpoint"].strip()
        assert item["status"] in valid_statuses, f"Invalid status {item['status']} for {item['feature']}"


def test_wired_endpoints_exist_in_openapi():
    assert openapi_path.exists(), "OpenAPI contract does not exist"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open(openapi_path, "r", encoding="utf-8") as f:
        openapi = json.load(f)

    openapi_paths = openapi.get("paths", {})

    for item in manifest["features"]:
        if item["status"] == "WIRED":
            # parse METHOD /path
            parts = item["endpoint"].split(" ")
            assert len(parts) == 2, f"Malformed endpoint '{item['endpoint']}' in manifest"
            method, path = parts[0].lower(), parts[1]
            
            # Check path exists in openapi
            assert path in openapi_paths, f"WIRED path '{path}' not found in OpenAPI contract"
            assert method in openapi_paths[path], f"WIRED method '{method}' not found for path '{path}' in OpenAPI contract"


def test_parity_matrix_is_synced():
    assert matrix_doc_path.exists(), "FEATURE_PARITY_MATRIX.md does not exist"
    with open(matrix_doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "MetaRadar: Feature Parity Matrix" in content
    assert "Executive Parity Summary" in content
    assert "In-Scope Parity Coverage" in content
