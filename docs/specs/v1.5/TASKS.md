# CodexBar v1.5 — TASKS

Status: frozen for implementation
Release: v1.5.0 — Control
Baseline: v1.4.0
Implementation rule: complete phases in dependency order; do not start a later phase while the current
phase gate is red.

## Global execution contract

Every implementation increment SHALL finish with:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```

A task that changes persistence, protocol parsing, process recovery or GUI lifecycle SHALL additionally run
its phase-specific tests before the global gate.

When the global gate is fully green, implementation MAY continue to the next ready task without a separate
scope-confirmation step.

No task may weaken an existing v1.4 acceptance/architecture test merely to make a new design pass. Tests may
be changed only when a reviewed v1.5 requirement intentionally supersedes the old contract.

## Phase map

| Phase | Theme | Tasks | Exit condition |
|---|---|---|---|
| A | composed account read | TASK-510..519 | one read -> usage + reset state; v1.4 usage/history intact |
| B | reset Event Store | TASK-520..529 | durable event ledger + projection + inspect |
| C | settings v2 + budget core | TASK-530..539 | schema-1 migration + schema-2 reserve + pure budget |
| D | redeem Process Manager | TASK-540..549 | durable/idempotent serialized redeem with recovery |
| E | monitor + notifications | TASK-550..559 | factual expiry monitor + deterministic policy |
| F | UI integration | TASK-560..569 | reset/control/redeem surfaces integrated without lifecycle regressions |
| G | validation + release | TASK-570..579 | target PASS, traceability closed, v1.5.0 ready |

## Phase dependencies

```text
A
├── B
│   └── D
├── C
│   └── E
└── B ──> E

D + E
  └── F
       └── G
```

Phase C may begin after Phase A is green and can be developed independently of Phase B, but the default
execution order remains A -> B -> C -> D -> E -> F -> G to minimize concurrent architectural change.

## Protected baseline

The following remain regression gates throughout all phases:

- `UsageSnapshot` contains no reset-credit state.
- `UsageProvider` remains usable by existing CLI/tests.
- `history.sqlite3` remains schema 1.
- only CURRENT usage enters usage history.
- v1.4 history analytics and History UI remain functional.
- settings v1 behavior is preserved through migration.
- LOW/EXHAUSTED alert semantics remain unchanged.
- GUI render-on-state-transition and History lifecycle stabilization remain intact.
- native indicator fallback behavior remains intact.
- no automatic redeem exists.

## Detailed phase plans

- `tasks/PHASE-A-ACCOUNT-GATEWAY.md`
- `tasks/PHASE-B-RESET-LEDGER.md`
- `tasks/PHASE-C-SETTINGS-BUDGET.md`
- `tasks/PHASE-D-REDEEM.md`
- `tasks/PHASE-E-MONITOR.md`
- `tasks/PHASE-F-UI.md`
- `tasks/PHASE-G-VALIDATION-RELEASE.md`

## Definition of implementation-ready

Implementation may start only when:

- all five REQs are reviewed;
- ADR-008..010 are accepted;
- `ARCHITECTURE.md` is frozen;
- all acceptance criteria appear in `TRACEABILITY.md`;
- every P0 criterion has at least one planned automated test;
- every phase has an explicit gate;
- no unresolved architectural question is marked blocking in `OPEN-DECISIONS.md`.

This package satisfies those conditions.
