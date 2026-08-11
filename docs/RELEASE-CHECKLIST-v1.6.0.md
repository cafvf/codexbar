# CodexBar v1.6.0 — Release Checklist

Status: ready for release commit

## Code and behavior

- [x] Phase F committed and present on `main`.
- [x] `scripts/validate_v1_6.py --real-read --full-gate` exits 0.
- [x] No automated validation reports FAIL.
- [x] No real-capability SKIP was required.
- [x] Physical Context/Open Details smoke passes.
- [x] Tray/native glance remains usage-only.
- [x] Context causes no alert, Control/Budget, or redeem side effect.

## Persistence and compatibility

- [x] History remains schema v1.
- [x] Reset ledger remains independent.
- [x] Settings schema v1/v2 compatibility remains green.
- [x] 180-day retention is active.
- [x] No schema-v2 History migration was introduced.

## Release metadata

- [x] `pyproject.toml` version is `1.6.0`.
- [x] package `__version__` is `1.6.0`.
- [x] `uv.lock` regenerated after version bump.
- [x] README describes Context and 180-day retention.
- [x] PRODUCT_SPEC records v1.6 — Context.
- [x] CHANGELOG contains 1.6.0 release entry.
- [x] `docs/TRACEABILITY-v1.6.md` finalized.
- [x] `docs/VALIDATION-v1.6.0.md` finalized.

## Validation evidence

- [x] 603 tests passed.
- [x] Ruff passed.
- [x] strict mypy passed.
- [x] compileall passed.
- [x] `git diff --check` passed.
- [x] real History: `ready_non_empty`, schema 1, 1591 snapshots.
- [x] real CURRENT Context check passed.
- [x] all 9 physical smoke checks passed.

## Git closure

- [ ] final release commit created and pushed.
- [ ] remote `main` verified at release commit.
- [ ] working tree clean.
- [ ] annotated tag `v1.6.0` created.
- [ ] tag pushed to `origin`.
- [ ] remote tag verified.
