# CodexBar v1.8.1 Release Checklist

Release type: **production-readiness maintenance / bugfix**

## Scope

- [x] no new product feature;
- [x] no settings schema change;
- [x] no History schema change;
- [x] no reset-ledger schema change;
- [x] no forecasting or predictive behavior;
- [x] no automatic redeem;
- [x] fix is confined to local Codex executable discovery and app-server spawn
      environment.

## Phase C evidence

- [x] upgrade from historical installation validated;
- [x] persistent data preservation validated;
- [x] fresh CodexBar state validated;
- [x] reinstall idempotence validated;
- [x] uninstall data preservation validated;
- [x] final reinstall validated;
- [x] first session-login test reproduced the graphical-session PATH defect;
- [x] corrected build passed physical GNOME/Wayland session-login validation.

## Regression gates before release

- [x] full pytest suite passes: 827 tests;
- [x] Ruff passes;
- [x] strict mypy passes: 89 source files;
- [x] compileall passes;
- [x] `git diff --check` passes;
- [x] release-version mode validation reports 1.8.1 in uv-run, editable and uv-tool modes;
- [x] installed v1.8.1 Doctor is healthy;
- [x] physical GNOME/Wayland login tray/Open Details smoke passed with the executable-resolution fix;
- [ ] exact release commit hosted CI is green.

## Release closure

- [ ] release commit pushed;
- [ ] annotated `v1.8.1` tag created on the validated commit;
- [ ] remote tag target verified;
- [ ] GitHub Release published;
- [ ] `docs/PRODUCTION-READINESS.md` records Phase D complete.
