# TASK-112 — complete implementation

This archive implements the four already-installed RED tests for:

- `codexbar settings show`
- `codexbar settings reset`

Behavior:
- `show` reports defaults vs persisted origin;
- `show` prints LOW threshold, refresh interval, notification flag;
- corrupt settings fall back to defaults while exposing the typed diagnostic;
- `reset` uses the existing application `ResetSettings` use case;
- expected settings failures return exit code 2;
- desktop and usage CLI behavior are preserved.

The task file is advanced to mark TASK-112 complete.

Run:

```bash
uv run pytest -ra
uv run ruff check src tests
uv run mypy
uv run python -m compileall -q src
```

Expected pytest count with the current local suite: 123 passed.

From TASK-113 onward, each delivery will include tests and production implementation
together, per the agreed workflow.
