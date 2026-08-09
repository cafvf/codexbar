# REQ-ALERT-001 — Target validation procedure

Status: pending target validation
Target: Ubuntu / GNOME / Wayland
Release: v1.2

## Transport prerequisite

Check the revised notification transport:

```bash
command -v notify-send
notify-send --app-name=CodexBar --urgency=normal   "CodexBar control test" "This confirms the host notification client works."
```

If `notify-send` is missing on Ubuntu/Debian:

```bash
sudo apt update
sudo apt install libnotify-bin
```

## Automated gate

```bash
uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
```

## Adapter diagnostic

```bash
uv run python scripts/diagnose_notifications.py
```

Expected: return code 0 and a visible `CodexBar diagnostic` notification.

## Controlled scenarios

Run individually:

```bash
uv run python scripts/validate_alerts.py low --delay 1
uv run python scripts/validate_alerts.py exhausted --delay 1
uv run python scripts/validate_alerts.py dedupe --delay 1
uv run python scripts/validate_alerts.py rearm --delay 1
uv run python scripts/validate_alerts.py disabled --delay 1
uv run python scripts/validate_alerts.py restart --delay 1
uv run python scripts/validate_alerts.py multi-window --delay 1
uv run python scripts/validate_alerts.py failure --delay 1
```

AC-ALERT-026 passes only when the target desktop visibly presents distinguishable LOW and EXHAUSTED
notifications identifying the affected window.
