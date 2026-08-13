---
status: testing
phase: 01-ingestion-connectors-data-pipeline
source: [01-VERIFICATION.md]
started: 2026-08-13T12:30:00Z
updated: 2026-08-13T12:30:00Z
---

## Current Test

number: 1
name: Live end-to-end connector run against real upstream APIs with PostgreSQL
expected: |
  Each connector fetches real data, persists verbatim payloads to raw_signals_bronze,
  updates connector_state (last_success/cursor), and /health/connectors reports accurate
  quota_remaining/last_success from live ConnectorState.
awaiting: user response

## Tests

### 1. Live end-to-end connector run against real upstream APIs with PostgreSQL
expected: |
  Each connector fetches real data, persists verbatim payloads to raw_signals_bronze,
  updates connector_state (last_success/cursor), and /health/connectors reports accurate
  quota_remaining/last_success from live ConnectorState.
result: [pending]

### 2. Live alembic migration on PostgreSQL
expected: |
  Migration chain (001 -> 002) applies head with no drift; connector_state table and
  raw_signals_bronze.cross_source_group_id column exist in the live schema.
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps