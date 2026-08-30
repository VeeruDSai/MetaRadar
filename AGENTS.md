# MetaRadar Agent Operating Standard (AGENTS.md)

This file governs all AI agents working on the MetaRadar codebase.

## Non-Negotiable Global Process Standards

All rules defined in `docs/rules/` and `.agents/rules/` are mandatory global process standards:

1. **[ENGINEERING_STANDARDS.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/ENGINEERING_STANDARDS.md)**: Absolute non-negotiable software quality, type safety, and honest execution telemetry.
2. **[DEFINITION_OF_DONE.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/DEFINITION_OF_DONE.md)**: Complete DoD verification matrix required before declaring any task done.
3. **[DEVELOPMENT_WORKFLOW.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/DEVELOPMENT_WORKFLOW.md)**: Strict branch workflow (`feature/*`, `fix/*`), atomic commits, and pull requests.
4. **[ARCHITECTURE_RULES.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/ARCHITECTURE_RULES.md)**: Approved Next.js 16 + FastAPI + PostgreSQL 16 + Local Gemma stack.
5. **[TESTING_STRATEGY.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/TESTING_STRATEGY.md)**: Mandatory executable testing gates (TSC, ESLint, Next build, pytest, contract sync).
6. **[SECURITY_STANDARDS.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/SECURITY_STANDARDS.md)**: Zero secret leaks, PII/PHI scrubbing, and Grok privacy gate.
7. **[CI_CD_STANDARDS.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/CI_CD_STANDARDS.md)**: Automated CI pipeline standards.
8. **[RELEASE_PROCESS.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/RELEASE_PROCESS.md)**: Release verification and deployment readiness.

## Core Rules

1. **Inspect Before Editing**: Always inspect exact file contents and repository context before modifying code.
2. **Preserve Architecture**: Do not silently rewrite or alter approved MetaRadar architecture.
3. **No Direct Push to Main**: Always create feature branches (`feature/*`, `fix/*`). Never push directly to `main`.
4. **No Fabricated Telemetry or Behavior**: Never fabricate test output, health status, or mock data without explicit labeling.
5. **No Disabling Tests or Suppressing Warnings**: Never use `ignoreBuildErrors`, `@ts-ignore`, or silent `try...except` to hide compilation/test failures.
6. **Executable Verification Required**: A phase is complete ONLY when executable evidence exists.
7. **Zero Secrets**: Never commit `.env` secrets, API keys, credentials, or private keys.
