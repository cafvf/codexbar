# CodexBar v1.5.0 — Control

Status: **VALIDATED — READY FOR TAG**

## Release theme

v1.5 extends the validated Observe / Configure / Notify / Remember / Understand stack with explicit **Control**.

## Delivered scope

- composed account read for usage plus reset-credit current state;
- reset-credit capability kept separate from `UsageSnapshot`;
- independent append-only reset event ledger;
- settings schema v2 with backward-readable schema v1;
- per-window reserves keyed by stable `UsageWindowId`;
- reserve configuration based on windows currently reported by the source;
- deterministic budget/headroom and reset-opportunity policy;
- factual reset-credit expiry monitoring;
- generic notification transport while preserving LOW/EXHAUSTED semantics;
- durable, idempotent manual reset-credit redemption;
- recovery for `REQUESTED` and `OUTCOME_UNKNOWN`;
- explicit GUI confirmation and repeated-action protection;
- redeem disabled when no current reset credit is available;
- Control/Budget, reset-credit, and redeem surfaces integrated into Current Details;
- deterministic mock/fault-injection validation path.

## Release invariants

- no automatic redeem;
- history remains observational and schema 1;
- reset ledger never substitutes for current account state;
- Control/Budget never forecasts;
- reserve policy remains independent of current remaining quota;
- no fixed 5h or Weekly quota-window assumption is embedded in the UI;
- native indicator remains usage-focused;
- History lifecycle remains compatible with v1.4.

## Validation

Gate G is complete.

- automated validation: PASS;
- full pytest gate: PASS;
- Ruff: PASS;
- strict mypy: PASS;
- compileall: PASS;
- `git diff --check`: PASS;
- mandatory physical GUI validation: PASS;
- real account read-only behavior: PASS;
- real destructive redeem: justified SKIP.

See:

- `docs/VALIDATION-v1.5.0.md`;
- `docs/TRACEABILITY-v1.5.md`;
- `docs/RELEASE-CHECKLIST-v1.5.0.md`.

## Release action

Create tag `v1.5.0` only from the final release-closure commit after confirming a clean working tree.
