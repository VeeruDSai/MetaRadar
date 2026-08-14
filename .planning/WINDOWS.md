---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 0
total_count: 1
last_updated: 2026-08-14T21:17:38.500Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 03 | deviation | backend/app/workflows/state.py |  | validated_signals channel switched to replacement reducer (signal duplication fix) | open |  | 2026-08-14T21:17:38.500Z |  |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "03",
    "file": "backend/app/workflows/state.py",
    "line": null,
    "description": "validated_signals channel switched to replacement reducer (signal duplication fix)",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-14T21:17:38.500Z",
    "resolved_at": null
  }
]
````
