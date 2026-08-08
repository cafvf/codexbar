# CodexBar

Specification-first Linux monitor for Codex usage limits.

## Current state
REQ-USAGE-001 is implemented and has been validated against an authenticated Codex installation on the
target Linux workstation. REQ-UI-001 now provides the first PySide6 system-tray implementation; its
controller tests are green and its target-desktop Qt validation is the next gate.

## Requirements
- Python 3.12+
- `uv` recommended for development
- Codex CLI installed and authenticated for real usage reads
- PySide6 only when using the tray UI

## Setup with uv
Core + development tests:

```bash
uv sync --extra dev
```

Tray UI + development tests:

```bash
uv sync --extra dev --extra gui
```

## Run
One-shot real usage read:

```bash
uv run python -m codexbar
```

Deterministic diagnostic mode:

```bash
uv run python -m codexbar --mock
```

Linux tray using the authenticated Codex provider:

```bash
uv run python -m codexbar --gui
```

Tray with deterministic mock data:

```bash
uv run python -m codexbar --mock --gui
```

## Development

```bash
uv run pytest -ra
uv run python -m compileall -q src
```

With optional quality tools installed by the `dev` extra:

```bash
uv run ruff check .
uv run mypy src
```

## Design
Read, in order:
1. `CONSTITUTION.md`
2. `PRODUCT_SPEC.md`
3. `docs/specs/v1.0/REQ-USAGE-001.md`
4. `docs/specs/v1.0/REQ-UI-001.md`
5. `docs/adr/ADR-002-codex-source.md`
6. `docs/TRACEABILITY.md`
7. `docs/tasks/v1.0/TASKS.md`
8. `docs/VALIDATION.md`
