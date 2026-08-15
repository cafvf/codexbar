# Git workflow and repository hygiene

## Files that belong in Git

Commit:
- source under `src/`;
- tests;
- scripts that are part of diagnostics, validation, installation or release workflows;
- specifications, ADRs, tasks and validation records;
- `pyproject.toml`;
- `uv.lock`;
- project-owned static assets required at runtime.

Do not commit:
- `.venv/`;
- `.omx/` local runtime/session state;
- `__pycache__/`;
- `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`;
- `dist/`, `build/`, `*.egg-info/`;
- local logs, crash dumps or diagnostic captures unless intentionally sanitized and added as fixtures;
- credentials, Codex authentication material or raw provider payloads containing account data;
- local history databases (`history.sqlite3`) or user settings.

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
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
git diff --check
git status
```

Stage intentionally:

```bash
git add <files-or-directories>
git diff --cached --check
git diff --cached
git commit -m "type: concise description"
```

Suggested prefixes: `feat`, `fix`, `test`, `docs`, `refactor`, `build`, `chore`, `release`.

## Lockfile policy

`uv.lock` is versioned because CodexBar is an application and reproducible development/CI resolution is a
project requirement. After changing package metadata or dependencies in `pyproject.toml`, run:

```bash
uv lock
```

Review and commit the corresponding lockfile change.

## Specification-first rule

A behavior change is not complete merely because code and tests pass. Follow `AGENTS.md` and the engineering
constitution:

1. identify affected `REQ-*`, `UC-*` and `AC-*`;
2. update normative specification first when behavior changes;
3. add/change acceptance or regression tests;
4. implement;
5. run focused and full tests;
6. update traceability, tasks and validation evidence.

Implementation-only guards use explicit `INV-*` identifiers.

## Target-system evidence

Manual target-system validation belongs in a requirement-specific validation record and may also be indexed
from `docs/VALIDATION.md`. Record what was actually observed and distinguish it from automated evidence.

Current history validation record:

`docs/VALIDATION-REQ-HISTORY-001.md`

## Release tagging

Before every release tag:

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

Review and commit all intended release changes. Create an annotated tag only from a clean working tree.

For release `X.Y.Z`:

```bash
git status
git log --oneline --decorate -n 10
git tag -a vX.Y.Z -m "CodexBar X.Y.Z"
git show --stat vX.Y.Z
git push origin main
git push origin vX.Y.Z
```

The annotated tag version SHALL agree with all committed version sources:
- `[project].version` in `pyproject.toml`;
- `codexbar.__version__` in `src/codexbar/__init__.py`;
- the local `codexbar` project entry in `uv.lock`.

`tests/unit/test_release_metadata.py` guards project/package metadata; regenerate `uv.lock` after metadata
changes so the lockfile remains aligned.

## v1.3.0 release-close ordering

For `TASK-332`, keep the release transition atomic:

1. close traceability/release documentation;
2. set `pyproject.toml` and `codexbar.__version__` to `1.3.0`;
3. update the release-metadata test;
4. run `uv lock`;
5. run the complete release gate above;
6. review `git diff --check`, status and staged diff;
7. commit the release close;
8. verify a clean tree;
9. create and push annotated tag `v1.3.0`.

Do not tag while metadata still reports 1.2.0.
