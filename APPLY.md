# v1.3 runtime test-only fix

No production behavior changes.

Fixes the acceptance test double so it implements the actual `UsageProvider`
contract (`get_usage()`), and applies Ruff's import ordering.

The previous failures all originated before HistoryService was reached, at:

`GetCurrentUsage.execute() -> self._provider.get_usage()`.

Run the complete gate again:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```
