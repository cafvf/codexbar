# CodexBar v1.2 Release Specification

Status: functional gates closed; release preparation pending
Release target: v1.2.0
Change taxonomy: EVOLUTION

## Goal

Add transition-based desktop usage alerts without repeated notification noise and without weakening the
v1.0/v1.1 provider, domain, settings, desktop or failure-safety contracts.

## Scoped requirements

- `REQ-ALERT-001` — transition-based desktop usage alerts: **validated and closed**.

## Release-level decisions

- normalized usage state drives alerts;
- `UsagePolicy` remains the single classifier;
- alert state is runtime-only;
- startup/restart baseline is silent;
- stale/error outcomes do not create transitions;
- delivery failures are non-fatal;
- `notifications_enabled` controls delivery without replay on re-enable;
- Linux delivery uses `notify-send` / `libnotify-bin` behind `NotificationPort`;
- settings schema remains version 1.

## Release gates

- [x] Every `REQ-ALERT-001` acceptance criterion has evidence.
- [x] Transition/deduplication logic is framework-independent and unit tested.
- [x] Notification delivery is isolated behind an application-facing port.
- [x] Existing v1.0/v1.1 acceptance suites remain green.
- [x] Architecture tests protect dependency boundaries and classifier reuse.
- [x] Disabled notifications suppress delivery while tracking remains deterministic.
- [x] Stale/error paths cannot fabricate alert transitions.
- [x] Notification-delivery failures cannot break refresh/tray behavior.
- [x] Repository-wide pytest, ruff, strict mypy and compileall passed.
- [x] Ubuntu/GNOME/Wayland target validation confirmed LOW and EXHAUSTED delivery.
- [x] ADR-006 records the final Linux transport and the rejected QtDBus path.
- [x] REQ-ALERT-001 validation and traceability records are closed.
- [ ] v1.2.0 release metadata/version files are updated and the final release gate is rerun.
- [ ] release commit and annotated `v1.2.0` tag are created from a clean working tree.

## Release disposition

The functional scope of v1.2 is closed. Remaining work is release engineering only:

1. advance package/version metadata from 1.1.0 to 1.2.0;
2. update changelog/current-release documentation;
3. regenerate `uv.lock`;
4. rerun the complete release gate;
5. create the release commit;
6. create and push annotated tag `v1.2.0`.
