#!/usr/bin/env bash
set -euo pipefail
python -m pytest -q
python -m compileall -q src
if command -v ruff >/dev/null 2>&1; then ruff check .; else echo 'ruff: not installed (skipped)'; fi
if command -v mypy >/dev/null 2>&1; then mypy src; else echo 'mypy: not installed (skipped)'; fi
