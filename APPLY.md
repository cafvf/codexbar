# TASK-115 native Settings menu correction — v2

This package is self-contained. No patch script is required.

It fixes:
1. native Ayatana menu missing Settings;
2. parent helper contract missing on_settings callback;
3. the existing AC-UI-023 literal protocol test by preserving explicit
   `_emit("refresh")`, `_emit("details")`, and `_emit("quit")` calls;
4. import ordering in the added test;
5. TrayShell wiring to `on_settings=self.show_settings`.

Extract over the repository root, then run:

```bash
uv run pytest -ra
uv run ruff check src tests
uv run mypy
uv run python -m compileall -q src
```

If green:

```bash
uv run python -m codexbar --mock --gui
```

The active Ayatana menu should include Settings.
