# CodexBar v1.8 — Release Traceability

Status: release-prep hosted gate green; final evidence-closure/tag sequence pending
Theme: Plan
Target release: v1.8.0
Validated baseline: v1.7.0 — Diagnose

The normative acceptance-level matrix is `docs/specs/v1.8/TRACEABILITY.md`. This release-level record summarizes the evidence chain used to decide whether v1.8.0 is tag-ready.

## Release evidence map

| Area | Product contracts | Implementation evidence | Release evidence |
|---|---|---|---|
| Plan policy | REQ-PLAN-001, AC-1801..1804 | checkpoint domain/settings tests | full suite + Settings target validation |
| Plan evaluation | REQ-PLAN-002, AC-1805..1812 | P01..P14 in `tests/unit/test_plan.py` | full suite |
| Settings schema v3 | REQ-PLAN-003, AC-1813..1817 | schema v1/v2/v3 + repository + CLI tests | full suite + Save/reopen target validation |
| Plan configuration | REQ-PLAN-004, AC-1801..1804/1816..1817 | `test_plan_settings_ui.py`, Settings GUI tests | target Save/Cancel/Reset validation |
| Current Details Plan | REQ-PLAN-005, AC-1818..1821 | presenter/text/Qt PlanPanel tests | target PlanPanel/live-update validation |
| Plan alerts | REQ-PLAN-006, AC-1822..1830 | A01..A10 in `test_plan_alerts.py` | physical breach/rearm/disabled/activation harness |
| Runtime integration | REQ-PLAN-007, AC-1831..1832 | controller/adopt-snapshot + redeem regressions | full suite |
| Protected boundaries | REQ-PLAN-008, AC-1833..1838, INV-PLAN-001..007 | architecture + v1.0–v1.7 regressions | full local gate + hosted CI |
| Version authority | TASK-864 | `pyproject.toml`, release-neutral version-mode validator | uv-run/editable/uv-tool validation + hosted CI |
| Desktop contract | TASK-861 | existing native/Qt/single-instance tests | target smoke; no destructive package removal required |

## Pre-release-prep evidence

The implementation baseline at commit `b8b83abe4fae33ed873e33cb1a3c5462366266dd` passed:

- 815 pytest tests;
- Ruff;
- strict mypy over 89 source files;
- compileall;
- `git diff --check`.

Physical v1.8 behavior on Ubuntu/GNOME/Wayland also passed before the version bump:

- Settings Plan editing and persistence;
- PlanPanel rendering and live Settings application;
- Budget/Plan independence with materially different reserve/checkpoint floors;
- Plan notification breach, rearm, disabled/no-replay and activation scenarios;
- released usage-alert LOW/dedupe/disabled/multi-window scenarios.

These are implementation-completion evidence.

## Final local release-prep evidence

After release metadata and documentation integration:

- `uv.lock` reflects local project version 1.8.0 with no dependency churn;
- 819 pytest tests passed;
- Ruff, strict mypy, compileall and `git diff --check` passed;
- uv-run, editable and isolated uv-tool modes all reported metadata/runtime 1.8.0;
- the pre-existing expanded root README was preserved and reconciled with v1.8 Plan documentation;
- the final concise Ubuntu/GNOME/Wayland release-candidate smoke passed.

## Hosted release-prep evidence

Release-prep commit:

`dd87b4716fe29c5d433704079b729338c42e33c4`

Remote `main` was verified at the same SHA.

GitHub Actions run `31858424480` completed with conclusion **SUCCESS**.

Jobs:

- Python 3.12 — SUCCESS;
- Python 3.13 — SUCCESS;
- Python 3.14 — SUCCESS;
- isolated uv-tool version mode — SUCCESS.

The Python jobs each completed pytest, Ruff, strict mypy, compileall, architecture gates and project/editable release-version checks. The uv-tool job completed the isolated release-version validation.

The release-prep hosted blocker is therefore closed.

## Remaining tag blockers

Only the final evidence-closure/tag sequence remains:

- create and push the documentation-only evidence-closure commit;
- verify remote `main` at that exact commit;
- require the same hosted CI workflow to succeed on that exact commit;
- create annotated tag `v1.8.0` only on that verified green commit;
- push and remotely verify the tag.

No further code, settings schema, version, lock, Plan behavior or README mutation is required before tagging.

The future CI run ID of the evidence-closure commit is verified externally rather than embedded through another pre-tag documentation mutation. This keeps the tag target stable and avoids an infinite evidence-update loop.

## Exclusions preserved

Release closure does not introduce forecasting, time-to-exhaustion, exhaustion probability, automatic redeem, Plan-specific persistence/concurrency, History/Context Plan authority or reset-credit evidence as Plan authority.
