# MetaRadar Definition of Done (DoD)

A task or phase is considered **DONE** only when all applicable quality gates pass with executable evidence:

- [ ] **Requirements**: Understood and aligned with approved architecture.
- [ ] **Implementation**: Clean code written without breaking existing interfaces.
- [ ] **Typecheck**: `pnpm exec tsc --noEmit` passes with 0 errors.
- [ ] **Lint**: `pnpm lint` / `eslint .` passes with 0 errors.
- [ ] **Build**: `pnpm build` / `next build` completes with 0 errors.
- [ ] **Unit Tests**: Pytest / foundation test suite passes with 100% clean output.
- [ ] **Contract Sync**: OpenAPI schema exported & TypeScript types synchronized.
- [ ] **Security**: PII/PHI scrubber verified & privacy gate enforced.
- [ ] **Docker**: `docker compose config` validates cleanly.
- [ ] **CI**: GitHub Actions workflow passes cleanly.
- [ ] **Documentation**: Architecture changes & APIs documented.
- [ ] **Git Safety**: Feature branch used, atomic commit created, NO direct push to main.

> If any gate cannot be verified, the phase status is **BLOCKED**.
