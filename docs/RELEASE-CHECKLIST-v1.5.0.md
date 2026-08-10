# CodexBar v1.5.0 Release Checklist

Status: **READY FOR TAG**

## Repository

- [x] Phase F implementation is present on the release working tree.
- [x] project/package version is 1.5.0.
- [x] `uv lock` completed after the version bump.
- [x] `git diff --check` PASS.

## Automated gates

- [x] `uv run python scripts/validate_v1_5.py` completed with zero automated failures.
- [x] `uv run pytest -ra` PASS.
- [x] `uv run ruff check src tests scripts` PASS.
- [x] `uv run mypy` PASS.
- [x] `uv run python -m compileall -q src scripts` PASS.

## Target validation

- [x] Current refresh PASS.
- [x] Current -> History PASS.
- [x] History hide/show PASS.
- [x] History period switching PASS.
- [x] Current refresh with History visible PASS.
- [x] reset/control surfaces PASS.
- [x] settings schema-v1 compatibility PASS.
- [x] settings schema-v2 reserve persistence PASS.
- [x] reserve UI follows currently reported usage windows.
- [x] reserve can be configured with current remaining quota at 0%.
- [x] redeem is disabled when no reset credit is available.
- [x] explicit redeem confirmation surface PASS.
- [x] native Ayatana / applicable GUI path PASS.
- [x] real account read-only behavior PASS.
- [x] real redeem explicitly SKIPPED because it is destructive.

## Documentation

- [x] `README.md` updated for v1.5.
- [x] `PRODUCT_SPEC.md` updated.
- [x] `CHANGELOG.md` updated.
- [x] `docs/VALIDATION-v1.5.0.md` finalized.
- [x] `docs/TRACEABILITY-v1.5.md` closed.
- [x] `docs/specs/v1.5/RELEASE.md` finalized.

## Release

- [ ] commit release closure.
- [ ] confirm clean working tree.
- [ ] create tag `v1.5.0`.
- [ ] push `main`.
- [ ] push tag `v1.5.0`.
