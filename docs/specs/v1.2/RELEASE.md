# CodexBar v1.2 Release Specification

Status: release candidate
Release target: v1.2.0
Change taxonomy: EVOLUTION

## Scope

`REQ-ALERT-001` is validated and closed.

v1.2.0 adds transition-based LOW/EXHAUSTED desktop alerts while preserving v1.0/v1.1 provider, settings,
tray and failure-safety contracts.

## Final release gates

- [x] Acceptance/unit/architecture/regression coverage complete.
- [x] Ubuntu/GNOME/Wayland physical validation complete.
- [x] Final Linux transport recorded in ADR-006.
- [x] REQ-ALERT-001 traceability and validation records closed.
- [x] Public documentation updated for v1.2.0.
- [ ] Package metadata, `__version__`, release metadata test and `uv.lock` all report 1.2.0.
- [ ] Repository-wide pytest, ruff, strict mypy, compileall and `git diff --check` pass after final bump.
- [ ] Working tree is reviewed and release commit is created.
- [ ] Annotated `v1.2.0` tag is created and pushed.

## Release disposition

The product scope is complete. Only the final release gate, commit and tag remain.
