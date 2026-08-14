# CodexBar v1.7.0 — Validation

Status: release candidate — final hosted gate pending
Release theme: Diagnose
Target desktop: Ubuntu/GNOME/Wayland
Validation date: 2026-08-14

## Automated local evidence

Final H1 global gate after the System Health semantics correction:

- pytest: 718 passed in 3.07 s;
- Ruff: PASS;
- strict mypy: PASS;
- compileall: PASS;
- `git diff --check`: PASS.

## Real Doctor / persistence evidence

The Phase H validator completed with `overall_pass = true`.

Doctor text and JSON:

- both exited 0;
- `diagnostics_schema_version = 1`;
- overall health: healthy;
- secret-minimization checks passed.

Canonical persistent targets were hashed before and after Doctor:

- settings JSON: unchanged;
- History SQLite: unchanged;
- reset-ledger SQLite: unchanged.

Recorded persisted state:

- History: `ready_non_empty`, schema 1, 2215 snapshots;
- reset ledger: `ready_non_empty`, schema 1, 16 events;
- unresolved redeem attempts: 0;
- desktop integration: installed/launcher/desktop entry/icon healthy;
- autostart disabled.

This is direct target evidence that Doctor is read-only across the stores covered by
the v1.7 contract.

## Performance evidence

Final Phase H characterization completed with all executable hard checks green:

| Metric | p95 | Gate |
|---|---:|---:|
| Doctor local-only | 1.516 ms | <= 500 ms |
| Context cache hit | 0.0047 ms | <= 5 ms |
| Context Qt synchronous | 0.0408 ms | <= 50 ms |
| Context cold | 17.383 ms | <= 150 ms engineering target |
| SHOW_DETAILS IPC | 7.853 ms | <= 250 ms |

Context semantic equivalence passed.

Relative to the frozen Phase A sample, the strongest improvements were:

- Context candidate read: about 37% lower p95;
- cold Context: about 18% lower p95;
- repeated pre-cache Context behavior: about 37% lower p95.

Small sample-to-sample increases in app-server request/total and History 30d did
not violate a frozen release gate and do not overturn the Phase G evidence
decisions.

## Physical validation

The target operator validated:

- one GUI owner and useful second launch;
- Open Details close/reopen and authoritative Refresh;
- History + asynchronous Historical Context responsiveness;
- separate System Health window and technical-details affordance;
- native indicator behavior on Ubuntu/GNOME/Wayland;
- Settings/window close-reopen stability.

One physical defect was found during the release session: System Health exposed a
manual control named `Refresh` even though the window already refreshed its
read-only snapshot every 750 ms and did not own authoritative source refresh.

The final correction removed that button and added:

`Updates automatically while this window is open.`

The corrected target was physically retested successfully.

Qt fallback remains covered by the previously validated native-helper/fallback
evidence; no distro package was destructively removed merely to force fallback.

A real reset-credit consume was an allowed capability SKIP when no safe unresolved
credit was naturally present. No credit was created or spent for test theater.

## Hosted CI

Phase G established the hosted Python 3.12/3.13/3.14 matrix and uv-tool version
mode. The final v1.7.0 release-prep commit must rerun that hosted gate.

Final hosted conclusion: **SUCCESS**.

Release-prep hosted evidence:

- commit: `919de086839910d7d8823aa7b5e5c1d4dbf5bfe9`;
- workflow run: `31831752049`;
- event: push to `main`;
- Python 3.12: SUCCESS;
- Python 3.13: SUCCESS;
- Python 3.14: SUCCESS;
- isolated uv-tool version mode: SUCCESS.

Every Python-matrix job passed Test, Ruff, strict mypy, Compile, architecture
gates and project/editable version-authority validation. The uv-tool job passed
the combined uv-run/editable/isolated-tool mode check.

Remote `main` was verified at the release-prep commit.

A final documentation-only closure commit may follow this record. That exact
closure commit MUST pass the same hosted CI before annotated tag creation; this is
an operational tag gate and does not require another evidence-document rewrite.

## Release decision

Local automated, target performance and physical gates are green.

The release becomes fully PASS/tag-ready only after:

1. release metadata reports 1.7.0 in all three execution modes;
2. the final local gate remains green after the bump;
3. hosted CI is green on the release-prep commit.

## Final local H2 gate

The post-bump release-prep gate is GREEN.

Version authority validation:

- project version: `1.7.0`;
- `uv-run`: metadata/runtime `1.7.0` — PASS;
- editable mode: metadata/runtime `1.7.0` — PASS;
- isolated `uv-tool`: metadata/runtime `1.7.0` — PASS.

The final local global gate after the release metadata bump passed:

- pytest: PASS;
- Ruff: PASS;
- strict mypy: PASS;
- compileall: PASS;
- `git diff --check`: PASS.

TASK-787 and TASK-788 are closed locally.

TASK-789 remains open only for the release-prep Git commit/push, hosted CI on that
exact commit, remote-main verification and annotated tag closure.
