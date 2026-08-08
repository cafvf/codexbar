# Validation record — 2026-08-08

## Scope
REQ-USAGE-001 core implementation and repository bootstrap.

## Executed checks
- `python -m pytest -q` -> 27 passed.
- `python -m compileall -q src` -> passed.
- editable install using locally available build tooling -> passed with
  `python -m pip install --no-build-isolation -e .`.
- installed CLI smoke test `codexbar --mock` -> passed.

## Environment limitations
- `codex` is not installed in the validation container, therefore the production provider could not be
  exercised against a real authenticated Codex account here. Its protocol behavior is covered by
  deterministic transport tests and documented JSON fixtures.
- `ruff` and `mypy` are not installed in this container, so those optional quality checks were not run.

## Release interpretation
REQ-USAGE-001's headless/core vertical slice is implemented and test-green. v1.0 is not complete:
REQ-UI-001 (Linux tray, nonblocking refresh, GUI smoke tests, packaging/autostart) remains open.
