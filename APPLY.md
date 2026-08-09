# v1.3 TASK-308/309 — retention and schema hardening

Tests and implementation are delivered together.

This increment:
- implements `< cutoff` retention with exact-boundary preservation;
- relies on ON DELETE CASCADE and tests orphan prevention;
- validates existing schema-v1 databases instead of silently completing them;
- fails closed on unknown schema versions and corrupt/non-SQLite files;
- normalizes read/write/prune database failures;
- proves history pruning does not mutate settings data.

Important behavior change:
an existing database is never auto-repaired by CREATE TABLE IF NOT EXISTS.
Only an absent database is initialized.

Run:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```
