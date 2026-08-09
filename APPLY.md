# v1.3 TASK-328/329 — architecture and regression evidence

Tests only; no production behavior changes.

Adds:
- direct automated evidence for INV-HISTORY-001..008;
- GUI-thread/performance guard preventing history storage from returning to TrayController;
- confinement test for the concrete SQLite adapter;
- explicit v1.1 settings schema-v1 regression checks;
- settings default/policy regression checks;
- v1.0 CURRENT -> STALE snapshot contract regression;
- proof that history projection does not mutate current UsageSnapshot semantics.

Run the complete gate:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```
