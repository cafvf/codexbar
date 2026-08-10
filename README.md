# CodexBar

CodexBar is a Linux tray application for monitoring Codex usage, retaining bounded observational history, and exposing explicit reset-credit control when the local Codex app-server provides that capability.

Current release: **1.5.0 — Control**.

## What CodexBar does

CodexBar keeps the tray view intentionally compact and moves detailed inspection into the **Open Details** window.

The application currently provides:

- current Codex usage and CURRENT/STALE fallback;
- desktop tray integration on Linux, with native Ayatana support and Qt fallback;
- configurable LOW threshold, refresh interval, notifications, and per-window usage reserves;
- bounded local usage history with 24h/7d/30d descriptive analysis;
- reset-credit count/details when reported by the app-server;
- an independent reset event ledger;
- deterministic Control/Budget information derived from the currently reported usage windows;
- manual, confirmation-gated reset-credit redemption with durable idempotency and recovery.

CodexBar does **not** forecast consumption, estimate authoritative token use, or automatically redeem reset credits.

## Requirements

Required:

- Linux;
- a locally authenticated Codex installation;
- a Python version supported by `pyproject.toml`;
- `uv`;
- `notify-send`.

On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install libnotify-bin
```

For native Ayatana tray support:

```bash
sudo apt install python3-gi gir1.2-ayatanaappindicator3-0.1 gir1.2-gtk-3.0
```

PyGObject intentionally remains outside the uv-managed environment.

## Installation

Clone the repository and install CodexBar:

```bash
git clone https://github.com/cafvf/codexbar.git
cd codexbar
./scripts/install.sh
```

Check the desktop integration:

```bash
"$(uv tool dir --bin)/codexbar" desktop status
```

Run the GUI:

```bash
"$(uv tool dir --bin)/codexbar" --gui
```

## Daily use

### Tray

The tray remains usage-focused. It exposes the current usage state and opens the detailed window without trying to compress reset/control information into the indicator itself.

### Open Details

Open Details contains four conceptual areas.

#### Current usage

Each currently reported usage window shows:

- remaining percentage;
- AVAILABLE / LOW / EXHAUSTED classification;
- freshness and observation age;
- reset timestamp when the source reports one.

The set of usage windows is not assumed to be fixed. CodexBar follows the windows actually reported by the current account source.

#### Reset credits

When the app-server exposes reset-credit capability, CodexBar shows:

- available credit count;
- count-only, partial-detail, or complete-detail coverage;
- known per-credit details;
- known expiry, non-expiring status, or unavailable expiry information.

If no reset credit is available, the **Redeem reset credit** action remains disabled.

#### Control / Budget

Control/Budget is a user-policy view, not a Codex limit.

For each currently reported usage window, CodexBar displays:

- **Remaining** — the current fraction reported by Codex;
- **Reserved** — the fraction you chose to preserve;
- **Available to use** — `max(Remaining - Reserved, 0)`;
- **Status** — relation between current remaining quota and the configured reserve.

Example:

```text
Weekly
  Remaining: 42%
  Reserved: 20%
  Available to use: 22%
  Status: Within budget
```

A reserve may be configured even when the current remaining quota is 0%. It becomes relevant after the quota resets.

Reserve configuration is tied to the usage windows currently reported by the source. CodexBar does not hard-code a 5-hour window or any other fixed quota window.

#### Reset recommendation

The reset recommendation is deterministic and based on current factual state plus configured policy. It does not use historical slope, forecasting, or predicted time-to-exhaustion.

### History

History stores only eligible CURRENT observations and provides read-only descriptive analysis over:

- 24 hours;
- 7 days;
- 30 days.

It shows observation count, first/latest observation, observed min/max, observed change, and the discrete samples at their actual observation times.

Gaps remain gaps. CodexBar does not interpolate or reconstruct unobserved states.

History maintenance:

```bash
codexbar history inspect
codexbar history clear
```

## Settings

The Settings window currently controls:

- LOW remaining threshold;
- automatic refresh interval;
- desktop notification enablement;
- per-window usage reserves for usage windows currently reported by Codex.

CLI inspection/reset:

```bash
codexbar settings show
codexbar settings reset
```

Settings schema v2 stores usage reserves. Existing schema-v1 settings remain readable and are migrated in memory; simply reading an old settings file does not rewrite it.

## Reset ledger and redeem safety

Reset-credit history is intentionally separate from usage history.

Inspect the reset event ledger with:

```bash
codexbar reset-ledger inspect
```

Redeem safety rules:

- redemption is never automatic;
- every normal redeem requires explicit user confirmation;
- one logical attempt has one durable idempotency key;
- retries reuse the original attempt identity;
- ambiguous transport outcomes remain `OUTCOME_UNKNOWN`;
- successful or already-redeemed outcomes trigger authoritative refetch;
- monitoring, notifications, refresh, and History never trigger redeem.

## Development

Install development dependencies:

```bash
uv sync --extra dev --extra gui --extra native-indicator
```

Standard local gate:

```bash
uv run ruff check src tests scripts --fix

uv run pytest -ra
uv run ruff check src tests scripts
uv run mypy
uv run python -m compileall -q src scripts
git diff --check
```

v1.5 target validation:

```bash
uv run python scripts/validate_v1_5.py
```

Optional read-only validation against the authenticated real account:

```bash
uv run python scripts/validate_v1_5.py --real-read
```

Real redeem validation is intentionally not automated because it spends a real reset credit.

## Persistence

CodexBar maintains independent local persistence responsibilities:

- usage history: schema-v1 SQLite, CURRENT-only observational history;
- reset event ledger: append-only reset/redeem evidence;
- application settings: schema v2 JSON with backward-readable schema v1.

No persistence store is allowed to fabricate or replace current authoritative account state.

## Release documentation

Release-specific documents:

- `PRODUCT_SPEC.md` — product model and release evolution;
- `CHANGELOG.md` — release history;
- `docs/specs/v1.5/` — v1.5 requirements, tasks, architecture, and release contract;
- `docs/TRACEABILITY-v1.5.md` — v1.5 implementation traceability;
- `docs/VALIDATION-v1.5.0.md` — final validation evidence;
- `docs/RELEASE-CHECKLIST-v1.5.0.md` — release/tag checklist;
- `docs/FUTURE-TASKS.md` — deferred maintenance.

## Security and semantic boundaries

CodexBar does not manage Codex credentials.

Raw credentials and raw provider payloads do not cross into History, notifications, the reset event ledger, or native-helper boundaries.

History and the reset event ledger are evidence stores. Neither is a fallback source for current account state.
