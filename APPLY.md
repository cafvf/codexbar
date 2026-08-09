# v1.3 TASK-310/311 + TASK-319/320

Tests and implementation are delivered together.

This increment adds:
- non-destructive path inspection for ABSENT / UNSUPPORTED / UNREADABLE;
- repository inspection for READY_EMPTY / READY_NON_EMPTY;
- schema version, count, oldest and newest observation metadata;
- transactional history clear preserving schema/meta;
- clear idempotency;
- explicit refusal to treat corrupt/unsupported storage as clear/repair.

No XDG path resolution, CLI commands, or refresh/runtime wiring is introduced yet.

Run:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```
