# CodexBar v1.1 Release Specification

Status: release-ready
Release: v1.1.0

## Goal

Make user-visible CodexBar behavior configurable without source-code changes while preserving the
v1.0 domain, provider, desktop-installation and failure-safety contracts.

## Scoped requirements

- `REQ-SETTINGS-001` — persistent user settings: **validated and closed**.

## Non-goals

- Notification delivery policy and deduplication; those belong to `REQ-ALERT-001`.
- Usage history, retention, or charts.
- Native package distribution.
- Generic plugin/configuration frameworks.
- Arbitrary CLI mutation of individual settings in the first settings increment.
- Moving desktop autostart ownership into application settings.

## Release gates

- [x] Every `REQ-SETTINGS-001` acceptance criterion has corresponding automated evidence.
- [x] Unit tests cover value validation, persistence boundaries, corruption handling and atomic writes.
- [x] Existing v1.0 acceptance tests remained green during implementation.
- [x] `ruff`, strict `mypy` and `compileall` passed at the implementation gate.
- [x] Persistence format and compatibility policy are recorded in accepted ADR-005.
- [x] Target GUI validation covered open/edit/save/cancel/reset and live runtime application.
- [x] Target validation discovered and closed the Ayatana Settings-menu parity defect.
- [x] `REQ-SETTINGS-001` traceability and validation records are closed.

## Release disposition

The v1.1 functional and target-system gates are closed. The release candidate is ready for the repository
release procedure:

```bash
uv lock
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests
uv run mypy
uv run python -m compileall -q src
git status
git diff
```

After the final gates pass, commit the release metadata/documentation from a reviewed working tree and create
annotated tag `v1.1.0`.

The tag SHALL point to the release commit and SHALL agree with the `1.1.0` version in `pyproject.toml` and
the regenerated `uv.lock`.
