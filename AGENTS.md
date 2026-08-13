# MetaRadar Agent Operating Standard (AGENTS.md)

This file governs all AI agents working on the MetaRadar codebase.

## Non-Negotiable Agent Rules

1. **Inspect Before Editing**: Always inspect exact file contents and repository context before modifying code.
2. **Preserve Architecture**: Do not silently rewrite or alter approved MetaRadar v5.1 architecture.
3. **No Direct Push to Main**: Always create feature branches (`feature/*`, `fix/*`). Never push directly to `main`.
4. **No Fabricated Telemetry or Behavior**: Never fabricate test output, health status, or mock data without explicit labeling.
5. **No Disabling Tests or Suppressing Warnings**: Never use `ignoreBuildErrors`, `@ts-ignore`, or silent `try...except` to hide compilation/test failures.
6. **Executable Verification Required**: A phase is complete ONLY when executable evidence exists (TSC, ESLint, Next build, pytest, contract sync).
7. **Zero Secrets**: Never commit `.env` secrets, API keys, credentials, or private keys.
