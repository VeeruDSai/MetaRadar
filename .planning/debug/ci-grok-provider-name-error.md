# Debug Session: CI Grok Provider NameError: name 'os' is not defined

**Session Start:** 2026-08-27
**Status:** Resolved
**Issue:** `NameError: name 'os' is not defined` during pytest collection in CI on Linux

## Symptoms
- **Expected:** `pytest -v` collects and executes all tests cleanly in CI without exceptions.
- **Actual:** Pytest collection failed across 13 test files with `NameError: name 'os' is not defined` in `backend/app/providers/grok.py:44`.
- **Trigger:** When `settings.effective_xai_api_key` is empty/None in headless CI environments without a `.env` file, Python evaluates the boolean fallback `os.environ.get("XAI_API_KEY")`, which failed because `os` was not imported in `backend/app/providers/grok.py` or `backend/app/providers/factory.py`.

## Root Cause
1. `backend/app/providers/grok.py` referenced `os.environ.get(...)` on lines 44, 58, 82, 99, 141 without `import os` at module level.
2. `backend/app/providers/factory.py` referenced `os.environ.get(...)` on line 37 without `import os` at module level.

## Fix
1. Added `import os` to `backend/app/providers/grok.py`.
2. Added `import os` to `backend/app/providers/factory.py`.
3. Verified full codebase with an AST-based undefined import scanner to ensure no other modules have missing standard library imports.

## Verification
- AST import scan verified 0 missing imports across all Python files in `backend/`, `tests/`, and `scripts/`.
- Tested explicit module import with stripped environment (`XAI_API_KEY=None`) in a standalone subprocess.
- `pytest --collect-only -q` successfully collected all 142 tests with 0 collection errors.
- `python scripts/export_openapi.py` executed cleanly with 0 diff on `frontend/types/api.ts`.
