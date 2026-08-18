import json
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
manifest_path = base_dir / "docs" / "manifests" / "feature_parity_manifest.json"
output_path = base_dir / "docs" / "FEATURE_PARITY_MATRIX.md"


def generate_matrix():
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    total = len(features)
    wired = sum(1 for item in features if item["status"] == "WIRED")
    partial = sum(1 for item in features if item["status"] == "PARTIAL")
    not_wired = sum(1 for item in features if item["status"] == "NOT_WIRED")
    deferred = sum(1 for item in features if item["status"] == "DEFERRED")
    compliance_pct = round((wired / (total - deferred)) * 100, 1) if (total - deferred) > 0 else 100.0

    md = f"""# MetaRadar: Feature Parity Matrix

**Version:** {data.get("version", "5.1.0")}  
**Last Updated:** {data.get("generated_at", "2026-08-18")}  
**Generated From:** `docs/manifests/feature_parity_manifest.json`  
**Status Vocabulary:** `WIRED` (Implemented & Gated) · `PARTIAL` (Partially Wired) · `NOT_WIRED` (Planned/Unwired) · `DEFERRED` (Explicitly Deferred)

---

## Executive Parity Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Specifications Audited** | **{total}** | **100.0%** |
| **Active In-Scope Features** | **{total - deferred}** | **{round(((total - deferred)/total)*100, 1)}%** |
| **WIRED & Verified Features** | **{wired}** | **{round((wired/total)*100, 1)}%** |
| **PARTIAL Implementations** | **{partial}** | **{round((partial/total)*100, 1)}%** |
| **NOT_WIRED (Deferred Gaps)** | **{not_wired}** | **{round((not_wired/total)*100, 1)}%** |
| **DEFERRED (Out of Scope)** | **{deferred}** | **{round((deferred/total)*100, 1)}%** |
| **In-Scope Parity Coverage** | **{wired}/{total - deferred}** | **{compliance_pct}%** |

---

## Feature Parity Specification & Verification Matrix

| Doc Spec | Control / Feature | Component | Endpoint | Status | Notes |
|:---|:---|:---|:---|:---:|:---|
"""
    for item in features:
        status_badge = f"**{item['status']}**" if item['status'] == "WIRED" else f"`{item['status']}`"
        md += f"| `{item['doc_spec']}` | {item['feature']} | `{item['component']}` | `{item['endpoint']}` | {status_badge} | {item['notes']} |\n"

    md += """
---

## Verification & Audit Governance

This matrix is validated by automated contract tests in `tests/test_parity_matrix.py`:
1. Every row marked `WIRED` has an active route in `contracts/openapi.json`.
2. Every component referenced is exported from `frontend/components/metaradar.tsx`.
3. Every test gate in `docs/rules/TESTING_STRATEGY.md` passes without warnings.
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Generated Feature Parity Matrix to: {output_path}")


if __name__ == "__main__":
    generate_matrix()
