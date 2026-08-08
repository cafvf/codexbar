# CodexBar v1.1 Release Specification

Status: development
Release: v1.1

## Goal

Make user-visible CodexBar behavior configurable without source-code changes while preserving the
v1.0 domain, provider, desktop-installation, and failure-safety contracts.

## Scoped requirements

- `REQ-SETTINGS-001` — persistent user settings.

## Non-goals

- Notification delivery policy and deduplication; those belong to `REQ-ALERT-001`.
- Usage history, retention, or charts.
- Native package distribution.
- Generic plugin/configuration frameworks.
- Arbitrary CLI mutation of individual settings in the first settings increment.
- Moving desktop autostart ownership into application settings.

## Release gates

- Every `REQ-SETTINGS-001` acceptance criterion has a corresponding acceptance test.
- Unit tests cover value validation, persistence boundaries, corruption handling, and atomic writes.
- Existing v1.0 acceptance tests remain green.
- `ruff`, strict `mypy`, and `compileall` remain green.
- Persistence format and compatibility policy are recorded in an ADR before production persistence is
  considered complete.
- Target GUI validation is required before `REQ-SETTINGS-001` is closed.
