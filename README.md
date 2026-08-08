# CodexBar

Specification-first Linux monitor for Codex usage limits.

## Current state
REQ-USAGE-001 core is implemented. CodexBar queries the documented local `codex app-server` JSON-RPC
API, normalizes dynamic rate-limit windows, and exposes a CLI surface. The Linux tray UI is the next
vertical slice.

## Requirements
- Python 3.12+
- Codex CLI installed and authenticated for real usage reads

## Run
```bash
python -m codexbar
```

Diagnostic/demo mode without Codex:
```bash
python -m codexbar --mock
```

## Development
```bash
python -m pytest
python -m compileall -q src
```

With development tools installed:
```bash
ruff check .
mypy src
```

## Design
Read, in order:
1. `CONSTITUTION.md`
2. `PRODUCT_SPEC.md`
3. `docs/specs/v1.0/REQ-USAGE-001.md`
4. `docs/adr/ADR-002-codex-source.md`
5. `docs/TRACEABILITY.md`
6. `docs/tasks/v1.0/TASKS.md`
