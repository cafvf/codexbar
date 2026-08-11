# CodexBar v1.7 — Implementation Plan

Status: frozen for implementation

## Strategy

Implement from observability and ownership toward interaction:

1. establish baseline metrics and diagnostic domain;
2. establish single-instance ownership before adding new runtime work;
3. optimize Context cache/query while semantics remain easy to compare;
4. move Context execution off Qt;
5. move redeem external work off Qt;
6. expose System Health and selected hardening;
7. establish CI/version/evidence decisions;
8. perform target validation and release.

## Why this order

Phase A makes subsequent optimization measurable.

Phase B ensures only one runtime owns polling/mutation before additional controllers
exist.

Phase C changes data access/cache without UI concurrency changes.

Phase D adds concurrency only after cache/revision semantics are frozen.

Phase E applies the proven async pattern to destructive-operation orchestration
without modifying the process manager.

Phase F consumes diagnostic primitives in UI only after backend state is stable.

## Expected additions

Likely areas:

- `domain/diagnostics.py`;
- `application/diagnostics.py`;
- runtime metric collector;
- instance coordinator;
- Current/History revision tracker/envelope;
- Context cache/controller;
- redeem execution controller;
- System Health view model/panel;
- source-contract fixtures;
- GitHub workflow;
- generic validation/release tooling.

## Expected modifications

- composition root;
- app-server rate-limit response selection;
- Context SQLite adapter;
- History runtime mutation result/revision signaling;
- Open Details composition;
- native indicator helper supervision;
- Budget domain/view state;
- package version derivation;
- README/PRODUCT_SPEC/CHANGELOG at release.

## Avoid unless an evidence gate explicitly authorizes it

- History schema migration;
- persistent app-server session;
- SQLite WAL;
- reduced prune cadence;
- Ayatana backend replacement;
- broad UI hierarchy rewrite;
- new notification policy;
- new persistent diagnostics store.

## Delivery workflow

For every phase:

1. implement the whole phase;
2. produce root-ready ZIP;
3. user applies locally;
4. run phase-specific gate;
5. run global gate;
6. correct all failures;
7. perform physical smoke where the phase requires it;
8. only then commit/push that phase.

Before full gate:

```bash
uv run ruff check src tests scripts --fix
```

Then:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
git diff --check
```

CI changes begin in Phase G, but local gates remain authoritative during earlier
phases until the workflow itself is validated.
