# AGENTS.md — CodexBar

Read `CONSTITUTION.md` before changing code.

## Required workflow
1. Identify affected `REQ-*`, `UC-*`, and `AC-*`.
2. For new behavior, update the spec first.
3. Add/change the smallest test that expresses the behavior.
4. Confirm the test fails for the intended reason.
5. Implement minimally.
6. Run focused tests, then the full suite.
7. Refactor only with tests green.
8. Update `docs/TRACEABILITY.md` and release tasks if scope changed.

## Architectural boundaries
- `domain/`: values, entities, domain policies, domain errors. No Qt, subprocess, filesystem, network.
- `application/`: use cases and ports. Depends on domain only.
- `infrastructure/`: Codex/process/cache adapters. May depend on application/domain.
- `ui/`: presentation/view models/Qt. Must not parse external Codex output.

## Prohibited shortcuts
- Do not map missing quota data to 0.
- Do not use bare `except Exception` at core boundaries without re-raising/normalizing deliberately.
- Do not add hard-coded five-hour/weekly fields to `UsageSnapshot`.
- Do not make an undocumented Codex endpoint or output shape a product guarantee.
- Do not add abstractions for hypothetical v2 modules.
