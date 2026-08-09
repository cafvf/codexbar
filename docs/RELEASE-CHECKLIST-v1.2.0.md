# CodexBar v1.2.0 Release Checklist

## Metadata
- [ ] `pyproject.toml` version is `1.2.0`.
- [ ] `src/codexbar/__init__.py` version is `1.2.0`.
- [ ] `tests/unit/test_release_metadata.py` expects `1.2.0`.
- [ ] `uv.lock` resolves CodexBar as `1.2.0`.

## Documentation
- [ ] CHANGELOG has a 1.2.0 entry.
- [ ] README identifies 1.2.0 as current release.
- [ ] REQ-ALERT-001 is validated/closed.
- [ ] TASK-211 is closed.
- [ ] ADR-006 records final notify-send transport.
- [ ] installation docs list `libnotify-bin`.
- [ ] validation and traceability records are closed.

## Final gate

```bash
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
git diff --check
```

## Pre-commit checks

```bash
git status
git diff --stat
git diff
grep '^version =' pyproject.toml
grep '__version__' src/codexbar/__init__.py
grep -A4 'name = "codexbar"' uv.lock | head -n 5
```

## Release
After all checks pass, mark TASK-212 complete and commit the release:

```bash
git add CHANGELOG.md README.md docs pyproject.toml src/codexbar/__init__.py   tests/unit/test_release_metadata.py uv.lock
git diff --cached --check
git diff --cached --stat
git commit -m "release: CodexBar v1.2.0"
git push origin main

git tag -a v1.2.0 -m "CodexBar v1.2.0"
git push origin v1.2.0
```

Finally verify:

```bash
git status
git log --oneline --decorate -n 3
git tag --list 'v1.2.0'
```
