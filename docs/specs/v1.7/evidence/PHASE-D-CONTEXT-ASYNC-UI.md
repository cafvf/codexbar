# CodexBar v1.7 Phase D — Asynchronous Context UI Evidence

Status: **validated / complete**
Tasks: TASK-740..749
Base: Phase C commit `979a672718735af1c55f017729bda60b376ba65e`

## Scope validated

Phase D moves Historical Context repository access and summary calculation off the Qt interaction thread while preserving the v1.6 Context semantics.

Validated implementation characteristics:

- framework-independent `ContextController` with executor, generation and revision capture;
- coherent Current observation/revision capture under lock;
- History revision captured with the worker request;
- obsolete result rejection before UI adoption;
- loading / ready / unavailable controller states;
- Qt `HistoricalContextPanel` limited to submit / poll / render responsibilities;
- repository query and full Context summary remain in background work;
- bounded runtime metrics for synchronous UI and background Context work;
- Historical Context is presented through the v1.7 composed Usage History surface while the protected v1.6 `HistoryDialog`/`HistoricalTrayShell` remain Context-UI independent;
- mock runtime wiring resolves the same `ContextController` used by the presenter/runtime composition.

No v1.6 Context selection or statistical semantics were changed.

## Automated validation

Final target-workstation global gate: **PASS**.

The final stabilized worktree passed:

- `uv run ruff check src tests scripts --fix`;
- `uv run pytest -ra`;
- `uv run ruff check src tests scripts`;
- `uv run mypy`;
- `uv run python -m compileall -q src scripts`;
- `git diff --check`.

The post-stabilization static consistency audit reported:

- HIGH: **0**
- MEDIUM: 129
- LOW: 379
- result: `NO HIGH-SEVERITY STATIC FINDINGS`

MEDIUM/LOW findings are tracked as code-smell/debt signals rather than Phase-D blockers.

## Characterization

Target workstation characterization:

```text
context.qt_sync
n=144
p50=0.020 ms
p95=0.046 ms
min=0.003 ms
max=0.305 ms

context.background_cold
n=20
p50=17.628 ms
p95=22.433 ms
min=16.347 ms
max=23.895 ms
```

Acceptance threshold for synchronous Context UI work: `p95 <= 50 ms`.

Result: **PASS** (`0.046 ms <= 50 ms`).

The measurement demonstrates the intended separation: Qt-side submit/poll work remains negligible while repository/context work executes in the background.

## Physical validation

Phase D physical smoke on the target workstation:

| Check | Result |
|---|---|
| Open Details opens promptly, remains compact, and does not contain Historical Context or System Health | PASS |
| Refresh remains responsive | PASS |
| Usage History contains Historical Context | PASS |
| Historical Context calculation does not block the GUI | PASS |
| Closing/reopening does not resurrect obsolete Context results | PASS |

Additional physical confirmation after mock wiring correction:

- Historical Context data is displayed under Usage History in `--mock`;
- System Health reports Context coherently with the Usage History result;
- the initial idle state does not falsely report Context as unavailable.

## Validation conclusion

**Phase D complete.**

The asynchronous boundary is physically responsive, stale-result suppression is retained, mock and real runtime composition use the intended controller path, and protected v1.6 History/Context architecture contracts remain intact.
