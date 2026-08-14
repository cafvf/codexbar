# CodexBar v1.7.0 — Release Checklist

Status: release prep

## Code and behavior

- [x] TASK-780 final validation harness completed.
- [x] TASK-781 real Doctor text/JSON read-only validation passed.
- [x] TASK-782 real History/Context/System Health state validated.
- [x] TASK-783 final performance characterization passed.
- [x] TASK-784 physical single-instance/Open Details/System Health lifecycle passed.
- [x] TASK-785 physical Context/native integration validation passed.
- [x] TASK-786 redeem responsiveness covered; real mutation capability SKIP allowed when unsafe/unavailable.
- [x] System Health refresh-semantics defect corrected and physically retested.

## Persistence and compatibility

- [x] History remains schema v1 and 180-day retention remains active.
- [x] reset ledger remains independent.
- [x] settings schema compatibility remains green.
- [x] Context v1.6 semantics remain unchanged.
- [x] no automatic redeem exists.
- [x] no forecasting/predictive wording is introduced.
- [x] no WAL/schema migration/prune-cadence/native-backend replacement was introduced without evidence.

## Performance

- [x] Doctor local p95 1.516 ms <= 500 ms.
- [x] Context cache-hit p95 0.0047 ms <= 5 ms.
- [x] Context Qt-sync p95 0.0408 ms <= 50 ms.
- [x] Context cold p95 17.383 ms <= 150 ms engineering target.
- [x] SHOW_DETAILS IPC p95 7.853 ms <= 250 ms.

## Release metadata

- [x] `pyproject.toml` version is `1.7.0`.
- [x] `uv.lock` regenerated after the version bump.
- [x] runtime package version derives from package metadata.
- [x] `uv run` version mode reports `1.7.0`.
- [x] editable version mode reports `1.7.0`.
- [x] isolated `uv tool` version mode reports `1.7.0`.
- [x] README release semantics updated without discarding unrelated local edits.
- [x] PRODUCT_SPEC records v1.7 — Diagnose.
- [x] CHANGELOG contains the v1.7.0 entry.
- [x] `docs/TRACEABILITY-v1.7.md` prepared.
- [x] `docs/VALIDATION-v1.7.0.md` prepared.

## Local gate

- [x] H1 pre-bump gate: 718 tests passed.
- [x] H1 pre-bump Ruff passed.
- [x] H1 pre-bump strict mypy passed.
- [x] H1 pre-bump compileall passed.
- [x] H1 pre-bump `git diff --check` passed.
- [x] final post-bump global gate passed.

## Hosted gate

- [ ] Python 3.12 job green on release-prep commit.
- [ ] Python 3.13 job green on release-prep commit.
- [ ] Python 3.14 job green on release-prep commit.
- [ ] isolated uv-tool version-mode job green on release-prep commit.

## Git closure

- [ ] final release-prep commit created and pushed.
- [ ] remote `main` verified at release-prep commit.
- [ ] hosted CI conclusion is success.
- [ ] working tree clean apart from intentionally excluded user-local work, if any.
- [ ] annotated tag `v1.7.0` created at the verified release commit.
- [ ] tag pushed to `origin`.
- [ ] remote tag verified.
