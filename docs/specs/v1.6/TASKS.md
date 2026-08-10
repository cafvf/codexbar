# CodexBar v1.6 — TASKS

Status: frozen for implementation
Release: v1.6.0 — Context
Baseline: v1.5.0
Implementation rule: complete phases in dependency order; do not start a later
phase while the current phase gate is red.

## Global execution contract

Before every full gate:

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

A phase that changes persistence/query behavior, statistics, or GUI lifecycle MUST
run its phase-specific gate before the global gate.

No task may weaken a v1.5 regression merely to make v1.6 pass unless a frozen
v1.6 requirement intentionally supersedes that contract.

## Phase map

| Phase | Theme | Tasks | Exit condition |
|---|---|---|---|
| A | retention + characterization | TASK-610..619 | 180-day schema-v1 retention measured and green |
| B | context domain core | TASK-620..629 | cycle/time/tolerance/reference selection deterministic |
| C | empirical statistics | TASK-630..639 | coverage/median/rank/bands frozen and tested |
| D | context query/application | TASK-640..649 | Current + history -> isolated Context state |
| E | Context UI | TASK-650..659 | distinct Historical Context surface, no lifecycle regression |
| F | performance + hardening | TASK-660..669 | 180-day characterization + fault/regression gates |
| G | validation + release | TASK-670..679 | target PASS, traceability closed, v1.6.0 ready |

## Dependencies

```text
A
└── B
    └── C
        └── D
            └── E
                └── F
                    └── G
```

This release is intentionally sequential because later semantics depend on the
reference-set definition.

## Protected v1.5 baseline

- `UsageSnapshot` remains free of Context/history-derived state.
- Current source remains authoritative.
- History remains discrete observational evidence.
- settings schema-v1/v2 compatibility remains intact.
- reset event ledger remains independent.
- Control/Budget remains deterministic and independent of Context.
- no automatic redeem exists.
- alert semantics do not depend on Context.
- native indicator/tray glance remains usage-focused.
- Current/History lifecycle remains green.
- dynamic quota windows remain supported; no fixed 5h assumption.

## Detailed phase plans

- `tasks/PHASE-A-RETENTION-CHARACTERIZATION.md`
- `tasks/PHASE-B-CONTEXT-DOMAIN.md`
- `tasks/PHASE-C-STATISTICS.md`
- `tasks/PHASE-D-APPLICATION-QUERY.md`
- `tasks/PHASE-E-UI.md`
- `tasks/PHASE-F-HARDENING.md`
- `tasks/PHASE-G-VALIDATION-RELEASE.md`

## Definition of implementation-ready

Implementation may start only when:

- `PRODUCT.md`, `REQUIREMENTS.md`, `DECISIONS.md`, and `ARCHITECTURE.md` are frozen;
- all implementation-blocking decisions are accepted;
- all P0 requirements map to tests in `TRACEABILITY.md`;
- canonical statistical vectors exist;
- every phase has an explicit gate;
- `OPEN-DECISIONS.md` has no blocking item.

This package satisfies those conditions.
