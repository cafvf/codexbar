# notify-send housekeeping fix

No production behavior changes.

Fixes:
- narrows the alert-specific architecture invariant so it does not conflict with the pre-existing,
  legitimate subprocess usage in ui/native_indicator.py;
- still proves that alert core/controller/launcher/tray do not depend on subprocess or the concrete
  notification adapter;
- removes unused sys imports from validation scripts.

Run:

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```
