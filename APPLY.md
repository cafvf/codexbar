# v1.3 TASK-326/327 — history CLI and concrete composition

Tests and implementation are delivered together.

Important runtime refinement:
SQLite history I/O is moved out of `TrayController.poll()` and into a
`HistoryCapturingUsageProvider`, so persistence/pruning run in the existing
refresh worker thread. This avoids blocking the GUI thread.

Adds:
- `codexbar history inspect`;
- `codexbar history clear`;
- non-destructive inspect of absent history;
- clear of absent history succeeds without creating a database;
- unsupported/corrupt history refuses destructive clear;
- concrete canonical-XDG SQLite history composition for normal CLI/tray usage;
- fail-open startup if the history repository itself cannot be initialized.

Run:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```
