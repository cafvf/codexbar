# Changelog

## 1.0.0 — 2026-08-08

First validated release of CodexBar.

### Included
- authenticated Codex usage/rate-limit retrieval through the local Codex app-server;
- normalized dynamic usage windows with stale/error semantics;
- Linux tray UI with project-owned icon, refresh/detail/quit interaction and Qt fallback;
- optional Ayatana native indicator label through an isolated system-Python helper;
- supervision, diagnostics and Snap/IDE runtime-environment sanitization for the native helper;
- canonical user-local `uv tool` installation with XDG desktop entry and icon;
- opt-in, reversible autostart;
- managed uninstall and checkout-independent installed execution;
- protection against Snap-scoped XDG installation paths;
- repository-wide pytest, ruff, strict mypy and compileall release gates.

### Supported baseline
- Linux;
- Python `>=3.12,<3.15`;
- a locally installed and authenticated Codex;
- `uv` for the supported installation workflow.

See `docs/specs/v1.0/RELEASE.md` and `docs/VALIDATION.md` for the release contract and validation evidence.
