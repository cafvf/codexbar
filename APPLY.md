# v1.2 alert core — tests + implementation

This package implements TASK-201 and the framework-independent core for TASK-203..206.

It deliberately does NOT yet wire alerts into TrayController and does NOT yet implement the QtDBus adapter.

Apply over a checkout that already contains the v1.2 specification files.

Run:

```bash
uv run pytest -ra
uv run ruff check src tests
uv run mypy
uv run python -m compileall -q src
```

Expected behavior added:
- silent initial baseline, including already LOW/EXHAUSTED;
- AVAILABLE→LOW, AVAILABLE→EXHAUSTED, LOW→EXHAUSTED and EXHAUSTED→LOW events;
- same-state deduplication;
- recovery re-arm;
- window absence does not re-arm;
- stale snapshots do not advance state;
- disabled notifications advance state but do not deliver/replay;
- normalized delivery failures are contained.

ADR-006 selects PySide6.QtDBus + org.freedesktop.Notifications for TASK-207.
