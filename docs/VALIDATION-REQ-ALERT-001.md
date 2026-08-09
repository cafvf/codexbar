# REQ-ALERT-001 — Target validation record

Status: validated
Target: Ubuntu / GNOME / Wayland
Release: v1.2
Date: 2026-08-08/09

## Automated evidence

The complete repository gate passed during v1.2 development:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```

Acceptance, unit, architecture and regression coverage included baseline semantics, LOW/EXHAUSTED
transitions, deduplication, recovery/re-arm, disabled/re-enabled notifications, stale/error behavior,
restart baseline, multi-window events, schema stability and delivery-failure isolation.

## Transport discovery

The initial PySide6.QtDBus adapter reached the GNOME notification service but was rejected because Python
values were marshalled with the wrong D-Bus signature. GNOME reported:

- actual: `(sisssava{sv}i)`;
- expected: `(susssasa{sv}i)`.

This exposed two binding-level mismatches: INT32 vs UINT32 for `replaces_id`, and array-of-variant vs
array-of-string for empty actions.

ADR-006 was revised. The final production transport uses distro-native `notify-send` / `libnotify-bin`.

## Final transport validation

Diagnostic:

```bash
uv run python scripts/diagnose_notifications.py
```

Observed on target:
- `/usr/bin/notify-send` found;
- return code `0`;
- positive notification id returned;
- visible GNOME notification presented.

## Physical alert validation

Controlled production-path validation used `scripts/validate_alerts.py`.

Confirmed:
- silent initial baseline;
- visible LOW notification;
- visible EXHAUSTED notification;
- LOW and EXHAUSTED are distinguishable;
- affected usage window is identified;
- transition generation and delivery use the production `AlertService` and final notification adapter.

Additional automated scenarios cover deduplication, re-arm, disabled/re-enabled behavior, restart baseline,
multi-window behavior, stale/provider failures and delivery-failure isolation.

## AC-ALERT-026

PASS.

The target desktop visibly presented distinguishable LOW and EXHAUSTED notifications identifying the
affected window.

## Final disposition

REQ-ALERT-001 is validated and closed. TASK-211 is complete.

Any future change from `notify-send`, change in alert retry/cooldown policy, or persisted deduplication state
requires a new compatibility/behavior decision rather than an implicit modification of v1.2 semantics.
