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
- [x] exact release commit hosted CI is green: run 31888631324 on `b449eec205c5a485b15c6f6ef335d3d330caabdb`.

## Release closure

- [ ] release commit pushed;
- [x] annotated `v1.8.1` tag created on validated commit `b040bbd40febeaa6e90dd13a9b3e74661a40d76a`;
- [x] remote tag target verified: annotated tag object `96f781a3487ba9d8d241e59a57a5fb7df2245b8d` points to `b040bbd40febeaa6e90dd13a9b3e74661a40d76a`;
- [x] GitHub Release `CodexBar 1.8.1` published for tag `v1.8.1`;
- [ ] `docs/PRODUCTION-READINESS.md` records Phase D complete.
