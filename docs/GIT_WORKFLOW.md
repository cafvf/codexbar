# Git workflow and repository hygiene

## Files that belong in Git

Commit:

- source under `src/`;
- tests;
- specifications, ADRs, tasks and validation records;
- `pyproject.toml`;
- `uv.lock`;
- project-owned static assets required at runtime.

Do not commit:

- `.venv/`;
- `__pycache__/`;
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`;
- `dist/`, `build/`, `*.egg-info/`;
- local logs, crash dumps or diagnostic captures unless intentionally sanitized and added as fixtures;
- credentials, Codex authentication material or raw provider payloads containing account data.

## Clone / update

```bash
git clone <repository-url>
cd codexbar
uv sync --extra dev --extra gui --extra native-indicator
```

Before starting new work:

```bash
git status
git pull --ff-only
```

## Before a commit

Run the release-relevant checks:

```bash
uv run pytest -ra
uv run python -m compileall -q src
git status
```

Stage intentionally:

```bash
git add <files-or-directories>
git diff --cached
```

Then commit:

```bash
git commit -m "type: concise description"
```

Suggested conventional prefixes: `feat`, `fix`, `test`, `docs`, `refactor`, `build`, `chore`.

## Lockfile policy

`uv.lock` is versioned because CodexBar is an application and reproducible development/CI resolution is a
project requirement. When `pyproject.toml` changes dependency resolution, regenerate/sync and commit the
corresponding `uv.lock` change.

## Specification-first rule

A behavior change is not complete merely because code and tests pass. Follow `AGENTS.md`:

1. identify the affected `REQ-*`, `UC-*`, and `AC-*`;
2. update normative specification first when behavior changes;
3. add/change the acceptance or regression test;
4. implement;
5. run focused and full tests;
6. update traceability, tasks and validation evidence.

## Target-system evidence

Manual target-system validation belongs in `docs/VALIDATION.md`. Record what was actually observed and
distinguish it from automated evidence. Never claim a desktop capability was validated merely because a
mock or headless test passed.

## v1.0 release-candidate checks

Before tagging the first desktop-installable release, run:

```bash
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests
uv run mypy
uv run python -m compileall -q src
```

Then perform the target-system REQ-DESKTOP-001 validation from `docs/specs/v1.0/REQ-DESKTOP-001.md`.
Do not create the v1.0 tag while that validation gate is still open.

## Release tagging

For a release candidate, first run all committed gates:

```bash
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests
uv run mypy
uv run python -m compileall -q src
```

Then review and commit all intended release changes. Create a release tag only from a clean working tree:

```bash
git status
git log --oneline --decorate -n 10
git tag -a v1.0.0 -m "CodexBar 1.0.0"
git show --stat v1.0.0
git push origin main
git push origin v1.0.0
```

The annotated tag version SHALL agree with `pyproject.toml` and `codexbar.__version__`.
