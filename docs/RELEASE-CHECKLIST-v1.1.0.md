# v1.1.0 release checklist

This checklist is the final repository/tag procedure after all v1.1 functional gates have closed.

## Metadata
- [ ] `pyproject.toml` reports `1.1.0`.
- [ ] `codexbar.__version__` reports `1.1.0`.
- [ ] `uv lock` has been run and the `codexbar` entry in `uv.lock` reports `1.1.0`.
- [ ] `CHANGELOG.md` contains the 1.1.0 release entry.
- [ ] README/Product Spec/Release Spec present v1.1 as the current validated baseline.

## Final automated gates

```bash
uv lock
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests
uv run mypy
uv run python -m compileall -q src
```

- [ ] pytest green.
- [ ] ruff green.
- [ ] mypy green.
- [ ] compileall green.

## Repository review

```bash
git status
git diff
git diff --check
```

- [ ] only intended release files changed.
- [ ] no cache/build/diagnostic artifacts staged.
- [ ] lockfile change matches package metadata.

## Release commit

Suggested staging:

```bash
git add pyproject.toml uv.lock src/codexbar/__init__.py tests/unit/test_release_metadata.py \
  CHANGELOG.md README.md PRODUCT_SPEC.md docs
git diff --cached
git commit -m "release: prepare CodexBar 1.1.0"
```

Do not stage temporary package-application notes such as `APPLY.md`.

Do not tag until the release commit is pushed and the working tree is clean.
