# CodexBar v1.6.0 — Validation

Status: PASS
Release theme: Context
Target desktop: Ubuntu/GNOME/Wayland
Validation date: 2026-08-10

## Automated evidence

Target validator:

```bash
uv run python scripts/validate_v1_6.py --real-read --full-gate
```

Result:

- validator failures: 0
- validator skips: 0
- validator manual items: 9
- validator automated passes: 16
- pytest: 603 passed
- Ruff: PASS
- strict mypy: PASS
- compileall: PASS
- `git diff --check`: PASS

## Real persistence/account validation

History:

- path: `/home/christiano/.local/share/codexbar/history.sqlite3`
- state: `ready_non_empty`
- schema: 1
- snapshots: 1591

Current-account Context:

- real authenticated read: PASS
- window: `window_10080m`
- state: `unavailable`
- comparable cycles: 0
- behavior accepted: factual unavailable state with no predictive fallback

The real-account check is read-only and performed no reset-credit redemption.

## Phase F target-workstation evidence

- schema v1 retained;
- 180-day fixture: 17,280 snapshots / 34,560 window rows;
- database size: 7,868,416 bytes;
- History 30d p50/p95: 4.006 / 5.587 ms;
- window 180d p50/p95: 27.490 / 34.130 ms;
- Context candidate SQL p50/p95: 23.446 / 27.156 ms;
- production Context p50/p95: 187.852 / 201.475 ms;
- no History schema-v2 migration or speculative index introduced;
- fault, gap, timezone and pseudoreplication diagnostics: PASS.

Performance values are target-workstation characterization evidence, not CI thresholds.

## Physical validation

All required Phase G physical checks passed:

1. Open Details opens once without duplicate windows/widgets — PASS.
2. Historical context is visually separate from Current usage — PASS.
3. Real unavailable/insufficient Context wording is factual and non-predictive — PASS.
4. View history opens the correct History window — PASS.
5. History hide/show and period switching remain stable — PASS.
6. Current refresh works with History visible — PASS.
7. Closing/reopening Open Details produces no duplicate or stale widgets — PASS.
8. Tray/native glance remains usage-only — PASS.
9. Reset/Control/Redeem surfaces remain unchanged by Context — PASS.

No Context-driven notification, automatic redeem, or Control/Budget authority was observed.

## Release decision

**PASS — CodexBar v1.6.0 is ready for final release commit and annotated tag preparation.**

Tag creation remains a separate Git closure step after the release commit is pushed
and remote `main` is verified at that commit.
