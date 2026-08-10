# CodexBar v1.4.0 release checklist

Status: validated; release-close commit/tag ready
Theme: Understand
Target validation: PASS on Ubuntu/GNOME/Wayland, 2026-08-10

## Specification and traceability

- [x] REQ-ANALYTICS-001 implemented and traceable.
- [x] REQ-HISTORY-UI-001 reconciled to Period-only as-built UX and validated.
- [x] REQ-UI-003 implemented and traceable.
- [x] REQ-UI-LIFECYCLE-001 implemented after target-discovered lifecycle defects.
- [x] history schema remains version 1; settings schema remains version 1.
- [x] final target validation archived in `docs/VALIDATION-v1.4.0.md`.
- [x] target result: 353 tests + Ruff + strict mypy + compileall + native diagnostic PASS.
- [x] final mandatory physical checks PASS.
- [x] Qt fallback final physical re-run recorded as conditional SKIP; automated compatibility remains guarded.

## Deferred non-blocking maintenance

- [x] Ayatana deprecation warning captured as `FUTURE-001`.
- [x] `canberra-gtk-module` warning captured as `FUTURE-002`.

## Metadata transition

- [x] set `[project].version = "1.4.0"` in `pyproject.toml`.
- [x] set `codexbar.__version__ = "1.4.0"`.
- [x] update `tests/unit/test_release_metadata.py` expected version.
- [x] CHANGELOG/README/Product Spec prepared for v1.4.0.
- [ ] run `uv lock` and verify local project version is 1.4.0.

## Final local release gate

```bash
uv lock
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
git diff --check
git status
git diff
```

- [ ] all tests pass after metadata/documentation close;
- [ ] Ruff passes;
- [ ] strict mypy passes;
- [ ] compileall passes;
- [ ] `git diff --check` passes;
- [ ] `uv.lock` reports local CodexBar 1.4.0;
- [ ] intended diff only.

## Commit and tag

```bash
git add -A
git diff --cached --check
git diff --cached
git commit -m "release: close v1.4.0"
git status
git tag -a v1.4.0 -m "CodexBar 1.4.0"
git show --stat v1.4.0
git push origin main
git push origin v1.4.0
```

- [ ] release-close commit created;
- [ ] clean working tree verified;
- [ ] annotated tag `v1.4.0` created and inspected;
- [ ] main and tag pushed.
