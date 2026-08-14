# CodexBar v1.7 Phase G — Hosted CI Corrections

Status: **second hosted correction prepared**
Related tasks: TASK-770 / TASK-771

## CI #1 — missing headless Qt runtime

Phase G commit:
`9d23679d3bb64423ced2842ea925f24045176920`

The first hosted matrix failed during pytest collection on Python 3.12, 3.13 and
3.14 because PySide6 could not load:

`libEGL.so.1`

The separate `uv tool version mode` job passed.

Correction:

- install Ubuntu package `libegl1` in the hosted quality matrix;
- retain `QT_QPA_PLATFORM=offscreen`;
- add an architecture assertion that the workflow preserves this runtime library.

No CodexBar production dependency changed.

## CI #2 — settings test environment isolation

Hosted correction commit:
`ee4fdbf753099eaac63fc5b3574a75b2331d3da9`

The `libEGL` correction succeeded: all three matrix jobs installed the headless Qt
runtime and completed test collection/execution.

Each Python matrix entry then failed in the same single acceptance test:

`tests/acceptance/test_settings_v2_cli.py::test_settings_reset_still_removes_schema_2_file`

Observed matrix behavior included `711 passed, 1 failed` for Python 3.12 and
Python 3.14; the failing assertion expected a settings file under the temporary
`HOME` to be removed.

The test set `HOME` but did not clear `XDG_CONFIG_HOME`. The production settings
path contract intentionally gives a non-empty `XDG_CONFIG_HOME` precedence over
`HOME/.config`. Therefore an ambient hosted-runner XDG setting can cause the test
to create one path while the repository correctly resets another.

The adjacent schema-v2 settings-show test already performs the required isolation:

`monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)`

Correction:

- add the same environment isolation to the reset acceptance test;
- make no production settings-path change.

This is a test-fixture portability correction, not a behavior change.

## Validation required

After applying this correction:

1. the focused settings-v2 acceptance file must pass locally;
2. the full local gate must remain green;
3. the correction must be committed and pushed;
4. the next hosted run must show Python 3.12, 3.13 and 3.14 green;
5. `uv tool version mode` must remain green.

Gate G remains open until all hosted jobs are green.
