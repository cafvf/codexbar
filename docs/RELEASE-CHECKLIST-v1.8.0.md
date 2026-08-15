# CodexBar v1.8.0 — Release Checklist

Status: released
Theme: Plan
Release date: 2026-08-14
Tag: `v1.8.0`

## Code and behavior

- [x] TASK-860 protected baseline passed before release metadata changes (815 tests, Ruff, mypy, compileall, diff check).
- [x] REQ-PLAN-001..007 implementation complete.
- [x] REQ-PLAN-008 protected architecture/regression boundaries covered by the existing suite.
- [x] P01..P14 evaluator vectors implemented and green.
- [x] S01..S08 settings/schema vectors implemented and green.
- [x] A01..A10 Plan alert semantics implemented and green.
- [x] Existing LOW/EXHAUSTED notification behavior remains green.
- [x] Budget remains Plan-independent and reserve has one owner.
- [x] No History/Context/reset-ledger/reset-credit authority enters Plan.
- [x] No automatic redeem, forecast, time-to-exhaustion or exhaustion probability exists.

## Physical target validation

- [x] Settings Plan add/edit/remove physically validated.
- [x] Save/reopen, Cancel and Reset physically validated.
- [x] PlanPanel physically validated in Current Details.
- [x] Live Settings Save updates Plan without restart.
- [x] 72h/30d checkpoint presentation validated.
- [x] Budget 15% vs Plan 90% independence physically validated.
- [x] Plan breach/rearm/disabled/activation physical notification scenarios passed.
- [x] Existing usage-alert physical scenarios passed.
- [x] No real reset-credit consume required.
- [x] Final concise native/window lifecycle smoke on release-prep tree passed.
- [x] Qt-fallback regression evidence reviewed; no destructive package removal performed solely for validation.

## Persistence and compatibility

- [x] Settings schema 3 is canonical on explicit Save.
- [x] Settings schemas 1 and 2 remain readable without rewrite-on-load.
- [x] History remains schema 1 and CURRENT-only.
- [x] Reset ledger remains independent.
- [x] Plan alert tracker is in-memory only.
- [x] No Plan-specific repository/cache/revision/worker/scheduler exists.

## Traceability and documentation

- [x] `docs/specs/v1.8/TRACEABILITY.md` maps AC-1801..1838 and INV-PLAN-001..007 to actual evidence.
- [x] `docs/TRACEABILITY-v1.8.md` closed with release evidence.
- [x] `docs/VALIDATION-v1.8.0.md` closed with local, hosted, physical and tag evidence.
- [x] `PRODUCT_SPEC.md` identifies v1.8.0 as the current validated release.
- [x] `docs/ROADMAP.md` marks v1.8 as Released and preserves v1.9 Explore ordering.
- [x] `CHANGELOG.md` identifies 1.8.0 as the validated Plan release.
- [x] v1.8 test matrix names the actual PlanPanel test files.
- [x] Root `README.md` was reconciled deliberately against the pre-existing local expansion without discarding it.

## Release metadata

- [x] `pyproject.toml` release version is `1.8.0`.
- [x] `uv.lock` regenerated; only the local CodexBar package changed from 1.7.0 to 1.8.0.
- [x] runtime package version continues to derive from package metadata.
- [x] hosted CI uses `scripts/validate_release_version_modes.py` rather than a release-number-specific validator.
- [x] uv-run version mode reports 1.8.0.
- [x] editable version mode reports 1.8.0.
- [x] isolated uv-tool version mode reports 1.8.0.

## Final local gate

- [x] pytest passes after version/lock/docs changes: 819 passed.
- [x] Ruff passes after version/lock/docs changes.
- [x] strict mypy passes after version/lock/docs changes (89 source files).
- [x] compileall passes after version/lock/docs changes.
- [x] `git diff --check` passes.
- [x] v1.8 release-contract architecture test passes.

## Hosted release-prep gate

Release-prep commit: `dd87b4716fe29c5d433704079b729338c42e33c4`
GitHub Actions run: `31858424480`

- [x] Python 3.12 job green on exact release-prep commit.
- [x] Python 3.13 job green on exact release-prep commit.
- [x] Python 3.14 job green on exact release-prep commit.
- [x] isolated uv-tool version-mode job green on exact release-prep commit.
- [x] workflow conclusion is SUCCESS.

## Final tag-target hosted gate

Evidence-closure/tag-target commit: `8edf0154f80862c283ea20f5f2e9e5fcbca8e734`
GitHub Actions run: `31858617233`

- [x] Python 3.12 job green on exact tag-target commit.
- [x] Python 3.13 job green on exact tag-target commit.
- [x] Python 3.14 job green on exact tag-target commit.
- [x] isolated uv-tool version-mode job green on exact tag-target commit.
- [x] workflow conclusion is SUCCESS.

## Git and tag closure

- [x] release-prep diff inspected; root README included only after deliberate reconciliation.
- [x] release-prep commit created and pushed.
- [x] remote `main` verified at `dd87b4716fe29c5d433704079b729338c42e33c4`.
- [x] hosted CI succeeded on that exact release-prep commit.
- [x] evidence-closure commit `8edf0154f80862c283ea20f5f2e9e5fcbca8e734` created and pushed.
- [x] remote `main` verified at the evidence-closure commit before tagging.
- [x] hosted CI succeeded on that exact evidence-closure/tag-target commit.
- [x] annotated tag `v1.8.0` created at `8edf0154f80862c283ea20f5f2e9e5fcbca8e734`.
- [x] tag pushed to `origin`.
- [x] remote tag verified.

Remote annotated-tag object:

`47411ee438fdb10745a5bd1fdce1d76067ab4cee`

The annotated tag object points to commit:

`8edf0154f80862c283ea20f5f2e9e5fcbca8e734`

Tag message:

`CodexBar v1.8.0 — Plan`

GitHub reports the tag as unsigned. This is recorded as release metadata, not as a release failure.

The release tag is immutable release evidence. This post-tag documentation synchronization occurs on `main` after the release and does not move or rewrite `v1.8.0`.
