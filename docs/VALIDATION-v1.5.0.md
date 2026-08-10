# CodexBar v1.5.0 Validation Evidence

Status: **PASS — release gate satisfied**

Validation date: 2026-08-10
Target environment: Ubuntu / GNOME / Wayland

## Automated Gate G

The v1.5 validation script completed with no automated failures.

Observed baseline before final physical close:

```text
PASS: 9
SKIP: 2
MANUAL: 9
FAIL: 0
```

The two automated SKIPs were intentional:

- real account read-only validation was not part of the first default invocation;
- real redeem was not requested because it spends a real reset credit.

The full global gate subsequently passed after all validation findings were corrected:

```bash
uv run ruff check src tests scripts --fix
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
git diff --check
```

Final automated status:

- pytest: PASS;
- Ruff: PASS;
- strict mypy: PASS;
- compileall: PASS;
- `git diff --check`: PASS.

## Physical GUI validation

The following target-system checks passed:

- Current refresh;
- Current -> History navigation;
- History show/hide lifecycle;
- History period switching;
- Current refresh while History is visible;
- reset-credit panel rendering;
- Control/Budget rendering;
- settings save/apply;
- redeem confirmation surface;
- native Ayatana / applicable GUI path.

## Validation findings resolved before release

### Redeem availability

Finding: the **Redeem reset credit** button was initially enabled even when no reset credits were available.

Resolution: the action now requires a positive current `available_count`. When no credit is available, the UI reports that state and keeps the redeem action disabled.

Result: PASS after re-test.

### Dynamic usage windows and reserves

Finding: the first v1.5 Settings UI assumed fixed 5h and Weekly reserve fields.

Resolution:

- reserve fields now follow usage windows actually reported by the current account source;
- no fixed 5h window is assumed;
- reserves remain keyed by stable `UsageWindowId`;
- reserve configuration is allowed even when current remaining quota is 0%;
- Control/Budget presentation was rewritten using `Remaining`, `Reserved`, `Available to use`, and `Status`.

Result: PASS after re-test.

## Real account read-only validation

Target-system use of the real authenticated account was exercised during physical validation. The observed source currently exposed the active weekly usage state and did not require a fixed 5h window assumption.

Result: **PASS** for the read-only current-state behavior relevant to the release.

## Real redeem

Result: **SKIP — explicitly justified**.

A real redeem spends a real reset credit. The release does not require that destructive validation because consume outcomes, idempotency, unknown-outcome handling, retry, recovery, authoritative refetch, and UI confirmation are covered by automated protocol fixtures, mocks, fault injection, and target GUI validation.

## Release conclusion

All mandatory v1.5 Gate G criteria are satisfied.

Release status: **READY FOR v1.5.0 TAG**.
