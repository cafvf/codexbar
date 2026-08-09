# CodexBar v1.3.0 release-close package

This package applies the approved documentation coherence changes and the atomic source metadata bump
from 1.2.0 to 1.3.0.

It intentionally does NOT include `uv.lock`: regenerate that machine-generated file locally after extraction.

## Apply

Extract over the repository root, then run:

```bash
uv lock
uv sync --extra dev --extra gui --extra native-indicator

uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts

git diff --check
git status
git diff --stat
git diff
```

Verify that `uv.lock` now contains the local `codexbar` project at version `1.3.0`.

Do not commit or tag if any gate fails.

If all gates pass, stage all intended release-close files including `uv.lock`, inspect the staged diff,
commit with `release: close v1.3.0`, then create annotated tag `v1.3.0`.
