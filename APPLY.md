# v1.3 TASK-312 — canonical XDG history path

Tests and implementation are delivered together.

Adds:
- XDG_DATA_HOME-based history database path resolution;
- fallback to `$HOME/.local/share`;
- Snap-scoped XDG_DATA_HOME rejection;
- no filesystem creation during path resolution;
- explicit tracking of the remaining AC-HISTORY-037 traceability gap.

No runtime wiring or CLI behavior is introduced yet.

Run:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```
