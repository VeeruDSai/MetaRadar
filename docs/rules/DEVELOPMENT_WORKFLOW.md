# MetaRadar Development Workflow

## Workflow Lifecycle

```
PLAN → BRANCH → IMPLEMENT → TEST → VERIFY → DOCUMENT → COMMIT → PR → CI → MERGE
```

### Branching Convention
- `feature/*`: New functional feature
- `fix/*`: Bug resolution
- `refactor/*`: Code optimization without structural change
- `security/*`: Security patches or scrubber rules
- `docs/*`: Architectural documentation updates

> **NEVER PUSH DIRECTLY TO `main`.** Always submit pull requests from short-lived feature branches.
