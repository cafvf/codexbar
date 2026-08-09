# CodexBar v1.3.0 release checklist

Status: metadata prepared; final gate/tag pending
Requirement: REQ-HISTORY-001
Release metadata: 1.3.0

## Documentation

- [x] REQ-HISTORY-001 behavior and ACs implemented/validated.
- [x] ADR-007 reconciled with as-built architecture.
- [x] `docs/TRACEABILITY-REQ-HISTORY-001.md` created.
- [x] target validation recorded in `docs/VALIDATION-REQ-HISTORY-001.md`.
- [x] README/Product Spec/Installation/Git workflow reviewed against current code.
- [x] CHANGELOG contains an unreleased v1.3.0 release-candidate section.
- [x] release specification gates updated to the validated implementation state.

## Metadata transition

Perform together in the release-close commit:
- [x] set `[project].version = "1.3.0"` in `pyproject.toml`;
- [x] set `codexbar.__version__ = "1.3.0"`;
- [x] update `tests/unit/test_release_metadata.py` expected version;
- [ ] run `uv lock` and verify local project version is 1.3.0;
- [x] convert CHANGELOG v1.3 heading from `Unreleased` to the release date;
- [x] change README/Product Spec from release-candidate wording to current release 1.3.0;
- [x] mark `TASK-332` complete.

## Final release gate

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

- [ ] all tests pass;
- [ ] Ruff passes;
- [ ] strict mypy passes;
- [ ] compileall passes;
- [ ] `git diff --check` passes;
- [ ] intended diff only;
- [ ] metadata sources all report 1.3.0.

## Commit and tag

- [ ] stage intended release files;
- [ ] inspect `git diff --cached --check`;
- [ ] inspect `git diff --cached`;
- [ ] commit release close;
- [ ] verify clean working tree;
- [ ] create annotated tag `v1.3.0`;
- [ ] inspect tag;
- [ ] push `main`;
- [ ] push `v1.3.0`.

Suggested release commit:

```bash
git commit -m "release: close v1.3.0"
```

Tag:

```bash
git tag -a v1.3.0 -m "CodexBar 1.3.0"
git show --stat v1.3.0
git push origin main
git push origin v1.3.0
```
