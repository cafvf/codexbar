# CodexBar v1.7 Phase E — Asynchronous Redeem Evidence

Status: **validated / complete**
Tasks: TASK-750..759
Base: Phase C commit `979a672718735af1c55f017729bda60b376ba65e`

## Scope validated

Phase E moves manual Redeem execution off the Qt interaction thread without changing the existing durable Redeem semantics.

Validated implementation characteristics:

- framework-independent `RedeemExecutionController`;
- explicit idle / running / result / error execution state;
- existing `RedeemProcessManager.redeem()` / `retry()` execute in a worker;
- duplicate starts are rejected while an execution awaits UI adoption;
- late completion is suppressed after controller close/obsolete generation;
- durable begin, coordinator serialization, idempotent retry, refetch and reset-ledger semantics remain unchanged;
- Qt performs confirmation, submit and poll only;
- no automatic Redeem path is introduced.

## Automated validation

Final target-workstation global gate: **PASS**.

The final stabilized worktree passed:

- `uv run ruff check src tests scripts --fix`;
- `uv run pytest -ra`;
- `uv run ruff check src tests scripts`;
- `uv run mypy`;
- `uv run python -m compileall -q src scripts`;
- `git diff --check`.

The post-stabilization static consistency audit reported `HIGH=0`.

## Characterization

Delayed-fake characterization with a 200 ms worker delay:

```text
redeem.ui_submit
n=20
p50=0.028 ms
p95=0.083 ms
min=0.018 ms
max=0.254 ms

redeem.background_total
n=20
p50=200.835 ms
p95=201.296 ms
```

Result: **PASS**.

The approximately 200 ms background operation does not propagate to Qt submission latency; the UI-side submission remains sub-millisecond at p95.

## Physical validation

Target-workstation manual Redeem smoke using `--mock`:

| Check | Result |
|---|---|
| Manual Redeem starts only after explicit user action | PASS |
| Redeem controls are disabled appropriately while execution is active | PASS |
| GUI remains responsive during worker execution | PASS |
| Result is adopted after background completion | PASS |
| No automatic Redeem occurs | PASS |
| Retry of unresolved attempt | SKIP |

Retry was skipped because the physical mock session had no unresolved Redeem attempt and the retry control was correctly disabled. This is a justified non-applicable physical case; automated recovery/idempotency coverage remained green.

## Validation conclusion

**Phase E complete.**

Manual Redeem is separated from the Qt interaction thread, duplicate/late-result protections remain in place, durable Redeem semantics are preserved, and no automatic execution path was introduced.
