# MetaRadar Gemini Process Standards (GEMINI.md)

All AI development processes in this repository are governed by the standards in `docs/rules/` and `.agents/rules/`:

- [ENGINEERING_STANDARDS.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/ENGINEERING_STANDARDS.md)
- [DEFINITION_OF_DONE.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/DEFINITION_OF_DONE.md)
- [DEVELOPMENT_WORKFLOW.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/DEVELOPMENT_WORKFLOW.md)
- [ARCHITECTURE_RULES.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/ARCHITECTURE_RULES.md)
- [TESTING_STRATEGY.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/TESTING_STRATEGY.md)
- [SECURITY_STANDARDS.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/SECURITY_STANDARDS.md)
- [CI_CD_STANDARDS.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/CI_CD_STANDARDS.md)
- [RELEASE_PROCESS.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/rules/RELEASE_PROCESS.md)

## Enforcement Rules
1. Never push directly to `main`. Use feature branches (`feature/*`, `fix/*`).
2. Every phase requires executable verification (TSC, ESLint, Next build, pytest, contract sync).
3. No suppressing build errors (`ignoreBuildErrors`) or fabricating test outputs.
