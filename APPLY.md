# mypy fix for TASK-306/307 increment

No behavioral change.

Fixes the missing return type annotation on the still-unimplemented
`SqliteHistoryRepository.inspect()` stub:

```python
def inspect(self) -> HistoryInspection:
    raise NotImplementedError("TASK-319")
```

Also imports `HistoryInspection`.

Run:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```
