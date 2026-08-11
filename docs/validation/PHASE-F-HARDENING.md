# CodexBar v1.6 — Phase F Performance + Hardening

Status: implementation ready for local Gate F
Tasks: TASK-660..669

## Scope

Phase F adds no user-facing feature and introduces no schema migration. It closes the
performance and hardening requirements using the production schema-v1 repository,
the production `HistoricalContextService`, deterministic domain fixtures, and the
protected v1.5 regression suite.

## Task mapping

| Task | Evidence |
|---|---|
| TASK-660 | 180-day deterministic SQLite fixture and storage-size report |
| TASK-661 | production `HistoricalContextService.evaluate()` p50/p95 |
| TASK-662 | History 30-day and window 180-day query p50/p95 |
| TASK-663 | candidate-SQL vs production-Context timing + no speculative schema/index change |
| TASK-664 | corrupt SQLite classification + Context read-failure isolation |
| TASK-665 | irregular sampling-gap regression: 5/11 min accepted; 13/30 min rejected at h*=4h |
| TASK-666 | equivalent UTC/offset instants produce identical time-to-reset |
| TASK-667 | 63 high-frequency observations collapse to 3 independent cycles |
| TASK-668 | full pytest gate + architecture checks for the protected v1.5 baseline |
| TASK-669 | machine-readable tolerance and coverage diagnostic matrices |

## Phase-specific evidence command

Run from the repository root:

```bash
uv run python scripts/validate_phase_f_v16.py \
  --days 180 \
  --poll-minutes 15 \
  --repeats 25 \
  --output docs/validation/PHASE-F-HARDENING.local.md
```

The local report is intentionally ignored by git. Performance numbers vary by
machine and are characterization evidence, not hard CI thresholds.

The command exits non-zero if deterministic Phase F hardening checks fail.

## Global Gate F

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
git diff --check
```

## Persistence decision

Phase F retains schema v1. No migration or speculative index is introduced by this
implementation. Any index change requires measured evidence from the target
workstation and a separately reviewed schema/query decision.

## Exit condition

Gate F is green when:

1. the 180-day local evidence command exits zero and records p50/p95/storage data;
2. corruption, gap, timezone and pseudoreplication regressions are green;
3. the full protected baseline remains green;
4. no unexplained P0 regression exists;
5. schema remains v1.
