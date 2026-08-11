# CodexBar v1.7 — TASKS

Status: frozen for implementation
Release: v1.7.0 — Diagnose
Baseline: v1.6.0 — Context

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

## Phase map

| Phase | Theme | Tasks | Exit |
|---|---|---|---|
| A | baseline + diagnostics domain | 710..719 | health model/Doctor + baseline evidence green |
| B | instance ownership | 720..729 | one-owner IPC contract green |
| C | Context runtime | 730..739 | revision/cache/lean query green |
| D | Context async UI | 740..749 | Context off Qt + lifecycle green |
| E | redeem async | 750..759 | external redeem work off Qt, safety green |
| F | System Health + hardening | 760..769 | health UI/native/Budget hardening green |
| G | CI + metadata + evidence | 770..779 | hosted gate + evidence decisions closed |
| H | validation + release | 780..789 | target/physical/release closure |

## Dependencies

```text
A -> B -> C -> D -> E -> F -> G -> H
```

C must precede D so cache/revision semantics are deterministic before concurrency.

## Protected v1.6 baseline

- Current source remains authoritative.
- `UsageSnapshot` remains free of History/Context diagnostic authority.
- History remains observational and schema v1.
- 180-day retention remains valid.
- Context frozen v1.6 semantics remain unchanged.
- settings schema compatibility remains intact.
- reset ledger remains independent.
- Control remains deterministic.
- no automatic redeem.
- alert semantics remain independent of Context.
- native/Qt fallback remains.
- dynamic UsageWindowId remains supported.
- no predictive wording/behavior is introduced.

## Phase plans

- `tasks/PHASE-A-BASELINE-DIAGNOSTICS.md`
- `tasks/PHASE-B-INSTANCE-OWNERSHIP.md`
- `tasks/PHASE-C-CONTEXT-RUNTIME.md`
- `tasks/PHASE-D-CONTEXT-ASYNC-UI.md`
- `tasks/PHASE-E-REDEEM-ASYNC.md`
- `tasks/PHASE-F-HEALTH-UI-HARDENING.md`
- `tasks/PHASE-G-CI-METADATA-EVIDENCE.md`
- `tasks/PHASE-H-VALIDATION-RELEASE.md`

## Definition of implementation-ready

This package is implementation-ready because:

- Product/Decisions/Requirements/Architecture are frozen;
- no blocking item remains in OPEN-DECISIONS;
- evidence-gated work has an explicit default no-change outcome;
- P0 requirements map to tests;
- canonical vectors exist;
- every phase has an explicit gate.
