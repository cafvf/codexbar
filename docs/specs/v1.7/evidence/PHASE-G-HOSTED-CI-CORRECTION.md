# CodexBar v1.7 Phase G — hosted CI correction note

Status: **hosted CI correction prepared**
Related task: TASK-770 / TASK-771
Failed run: GitHub Actions CI #1 on Phase G commit
`9d23679d3bb64423ced2842ea925f24045176920`

## Observed hosted failure

The first hosted matrix reached dependency sync successfully for Python 3.12,
3.13 and 3.14, then failed during pytest collection.

The common failure was:

`ImportError: libEGL.so.1: cannot open shared object file: No such file or directory`

The separate `uv tool version mode` job passed.

This is a hosted-runner system-library gap rather than an application regression:
the local target gate remained green with 711 tests passing.

## Correction

The quality matrix now installs the minimal Ubuntu runtime package `libegl1` before
project sync/test execution.

No CodexBar project dependency, native-indicator dependency or production runtime
contract is changed.

An architecture test asserts that the hosted workflow retains the required
headless Qt runtime library.

## Validation required

After applying the correction:

1. focused CI-contract test must pass locally;
2. global local gate must remain green;
3. correction commit must be pushed;
4. a new hosted run must show Python 3.12, 3.13 and 3.14 green;
5. the separate `uv tool version mode` job must remain green.

Only then is Gate G remotely complete.
