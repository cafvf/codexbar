# CodexBar

CodexBar is a Linux tray application that reads Codex usage/rate-limit information from the locally authenticated Codex app-server and presents current and retained observational usage data.

## Current project status

Current release: **1.4.0 — Understand**.

Validated on Ubuntu/GNOME/Wayland through v1.4:
- verified current Codex usage and CURRENT/STALE fallback;
- Linux tray/Ayatana integration and Qt fallback contract;
- persistent settings and LOW/EXHAUSTED notifications;
- schema-v1 bounded local history;
- descriptive historical analytics;
- History UI with 24h/7d/30d periods and explicit observation-time axis;
- richer CURRENT details with classification, age, reset metadata and stable current-to-history navigation;
- GUI composition/lifecycle stabilization.

Final v1.4 target gate: **353 tests passed**, Ruff PASS, strict mypy PASS, compileall PASS, native indicator diagnostics PASS, mandatory physical checks PASS.

## Prerequisites

Required: Linux, authenticated local Codex, compatible Python from `pyproject.toml`, `uv`, and `notify-send`.

Ubuntu/Debian:
```bash
sudo apt update
sudo apt install libnotify-bin
```

Optional native Ayatana menu/label:
```bash
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 gir1.2-gtk-3.0
```
PyGObject remains outside the uv-managed environment.

## Install and run
```bash
git clone https://github.com/cafvf/codexbar.git
cd codexbar
./scripts/install.sh
"$(uv tool dir --bin)/codexbar" desktop status
"$(uv tool dir --bin)/codexbar" --gui
```

## Current details
Current Details displays each reported window with its current whole-percent presentation, visual remaining indicator, AVAILABLE/LOW/EXHAUSTED state, freshness/observation age, and reset metadata when supplied. `Reset: not reported` means the source did not provide a reset timestamp; CodexBar does not invent one.

Each current card can open History using the same stable `UsageWindowId`. Historical data never substitutes for missing current data.

## Historical insight
History retains the v1.3 schema-v1 30-day observational store and adds read-only descriptive analysis. The v1.4 History surface exposes **Period** (`24h`, `7d`, `30d`) as its visible selector. When opened from a current card, its stable window identity remains focused internally across period changes.

History shows observation count, first/latest observation, first/latest remaining, observed min/max/change, and discrete points positioned by actual `observed_at` timestamps. Gaps remain gaps: no interpolation, forecasting, ETA or authoritative token-consumption accounting is performed.

History maintenance CLI:
```bash
codexbar history inspect
codexbar history clear
```

## Settings and alerts
Settings: LOW threshold, automatic refresh interval, notification enablement. Alerts remain transition-based and ignore STALE/error outcomes.

```bash
codexbar settings show
codexbar settings reset
```

## Development and release checks
```bash
uv sync --extra dev --extra gui --extra native-indicator
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```

v1.4 target validation:
```bash
uv run python scripts/validate_v1_4.py
```

## Documentation map
- `PRODUCT_SPEC.md` — product baseline and release evolution.
- `CHANGELOG.md` — release history.
- `docs/specs/v1.4/` — v1.4 requirements/tasks/release contract.
- `docs/TRACEABILITY-v1.4.md` — v1.4 release traceability index.
- `docs/TRACEABILITY-REQ-ANALYTICS-001.md` — analytics closure.
- `docs/TRACEABILITY-REQ-HISTORY-UI-001.md` — History UI closure.
- `docs/TRACEABILITY-REQ-UI-003.md` — richer current UI closure.
- `docs/TRACEABILITY-REQ-UI-LIFECYCLE-001.md` — GUI lifecycle closure.
- `docs/VALIDATION-v1.4.0.md` — final target-system evidence.
- `docs/RELEASE-CHECKLIST-v1.4.0.md` — final local gate/tag procedure.
- `docs/FUTURE-TASKS.md` — explicitly deferred maintenance warnings/tasks.

## Security and semantic boundary
CodexBar does not manage Codex credentials. Raw provider payloads and credentials do not cross history, notification or native-helper boundaries. History is observational and is never a fallback source for CURRENT usage.
