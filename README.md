# CodexBar

CodexBar is a Linux tray application for monitoring Codex usage, retaining bounded observational history, and exposing explicit reset-credit control when the local Codex app-server provides that capability.

Current validated release: **1.7.0 — Diagnose**.
Release candidate: **1.8.0 — Plan**.

## What CodexBar does

CodexBar keeps the tray view intentionally compact and moves detailed inspection into the **Open Details** window.

The application currently provides:

- current Codex usage and CURRENT/STALE fallback;
- desktop tray integration on Linux, with native Ayatana support and Qt fallback;
- configurable LOW threshold, refresh interval, notifications, and per-window usage reserves;
- explicit per-window Plan checkpoints plus optional factual Plan-breach notifications;
- bounded 180-day local usage history with 24h/7d/30d descriptive analysis;
- empirical Historical context at the current time-to-reset using independent prior cycles;
- reset-credit count/details when reported by the app-server;
- an independent reset event ledger;
- deterministic Control/Budget information derived from the currently reported usage windows;
- manual, confirmation-gated reset-credit redemption with durable idempotency and recovery.

CodexBar does **not** forecast consumption, estimate authoritative token use, or automatically redeem reset credits.

## Requirements

CodexBar is designed for Linux. For an Ubuntu installation you need:

- a locally installed and authenticated Codex CLI/app-server;
- Python `>=3.12,<3.15`, as declared by `pyproject.toml`;
- `uv` available on `PATH`;
- `notify-send` for desktop notifications;
- PySide6, installed automatically by the CodexBar installation script.

Install the Ubuntu system packages used by notifications and the recommended
native Ayatana tray backend:

```bash
sudo apt update
sudo apt install -y \
  libnotify-bin \
  python3-gi \
  gir1.2-ayatanaappindicator3-0.1 \
  gir1.2-gtk-3.0
```

The Ayatana packages are optional but recommended on Ubuntu/GNOME. If the native
indicator is unavailable or becomes unhealthy, CodexBar can use its Qt tray
fallback. PyGObject intentionally remains provided by the system Python rather
than the uv-managed application environment.

Check the main prerequisites before installing:

```bash
uv --version
codex --version
notify-send --version
```

## Installing CodexBar on Ubuntu

CodexBar uses a **user-local `uv tool` installation**. Do not use `sudo pip`,
`sudo uv`, or install the Python package into the system interpreter.

### 1. Obtain the source

For the current development branch:

```bash
git clone https://github.com/cafvf/codexbar.git
cd codexbar
```

For a released version, select its tag before installing. For example, once
v1.7.0 is released:

```bash
git fetch --tags
git checkout v1.7.0
```

### 2. Install the application

Run the project installer from the repository root:

```bash
./scripts/install.sh
```

The installer:

- installs CodexBar as a `uv tool`;
- installs the PySide6 GUI dependency;
- uses canonical user-local locations under `~/.local` and `~/.config`;
- installs the CodexBar desktop entry and application icon;
- leaves autostart disabled until explicitly enabled.

No `sudo` is required for this step.

The command-line launcher is normally installed as:

```text
~/.local/bin/codexbar
```

If `~/.local/bin` is not already on your `PATH`, either add it to your shell
configuration or invoke CodexBar through `uv tool dir --bin`, as shown below.

### 3. Verify the installation

```bash
CODEXBAR="$(uv tool dir --bin)/codexbar"

"$CODEXBAR" desktop status
"$CODEXBAR" doctor
"$CODEXBAR" --diagnose-indicator
```

`desktop status` should report the launcher, desktop entry, and icon as installed.
`doctor` provides the broader CodexBar health report. `--diagnose-indicator`
checks the optional native Ayatana path; physical rendering still requires
launching the GUI in the desktop session.

### 4. Start CodexBar

From a terminal:

```bash
"$(uv tool dir --bin)/codexbar" --gui
```

After `desktop install`, CodexBar can also be launched from the Ubuntu/GNOME
application menu.

Normal installation starts only one GUI owner per user/session. Starting
`codexbar --gui` again asks the existing instance to show its UI instead of
creating a second polling runtime.

### 5. Enable autostart (optional)

Autostart is intentionally opt-in:

```bash
"$(uv tool dir --bin)/codexbar" desktop autostart enable
```

Disable it again with:

```bash
"$(uv tool dir --bin)/codexbar" desktop autostart disable
```

### Updating an installed copy

Update the source checkout to the desired release and rerun the installer:

```bash
cd /path/to/codexbar
git fetch --tags
git checkout <release-tag>
./scripts/install.sh
```

The installer uses `uv tool install --force`, so it replaces the installed
application code while preserving normal user data such as settings, usage
history, and the reset event ledger.

### Uninstalling

With the source checkout available:

```bash
./scripts/uninstall.sh
```

Or remove the desktop integration and tool explicitly:

```bash
"$(uv tool dir --bin)/codexbar" desktop uninstall
uv tool uninstall codexbar
```

Application uninstall does not silently delete persistent user data. Clear
History explicitly first if you also want to remove retained usage observations:

```bash
"$(uv tool dir --bin)/codexbar" history clear
```

## Daily use

### Tray

The tray remains usage-focused. It exposes the current usage state and opens the detailed window without trying to compress reset/control information into the indicator itself.

### Open Details

Open Details contains five conceptual areas.

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

#### Plan

Plan compares the captured **Current** observation with explicit operating targets
configured by the user for each reported usage window. A checkpoint contains a
time-to-reset coordinate and a minimum remaining fraction. The applicable Plan
floor is the maximum of the existing reserve and the currently active checkpoint
floor.

For CURRENT data, the Plan panel can show:

- whether Plan is configured for the window;
- whether a checkpoint is active;
- reset-unavailable/invalid checkpoint capability states;
- the effective floor and whether reserve, checkpoint, or both determine it;
- signed margin in percentage points;
- ABOVE / AT / BELOW compliance.

Example:

```text
Weekly
  Current: 63%
  Active checkpoint: 72h -> minimum 55%
  Effective floor: 55% (checkpoint)
  Margin: +8 pp
  Status: On plan
```

Plan is deterministic and factual. It uses the same captured Current observation
and explicit Settings only. History, Historical Context, reset-credit inventory,
consumption-rate inference, forecasting, exhaustion probability, and automatic
redeem have no Plan authority. STALE data is not presented as current Plan
compliance.

#### Reset recommendation

The reset recommendation is deterministic and based on current factual state plus configured policy. It does not use historical slope, forecasting, or predicted time-to-exhaustion.

### Historical context

Usage History also exposes **Historical context** for a current usage window when
authoritative reset metadata and comparable retained cycles are available.

Context compares the current remaining fraction with at most one real retained
observation from each prior authoritative cycle at a similar time-to-reset. It
uses the exact tolerance `min(0.05*h*, 2 hours)` and adapts presentation to the
number of independent comparable cycles.

Context is descriptive only. It does not forecast exhaustion, estimate probability
of future usage, influence alerts, alter Control/Budget policy, or trigger redeem.

### System Health

**System Health** is a separate read-only window for runtime diagnostics. It
updates automatically while open and summarizes Current, History, Historical
Context, account-history scope, desktop backend state and bounded runtime timing
metrics.

Technical details are hidden by default. System Health does not initiate an
authoritative usage read or mutate History, settings, the reset ledger or reset
credits. Use **Refresh** in Open Details when you want CodexBar to request new
authoritative usage data.

`codexbar doctor` exposes the same diagnostic model in text form, while
`codexbar doctor --json` provides machine-readable diagnostics schema version 1.

### History

History retains eligible CURRENT observations for 180 days and provides read-only descriptive analysis over:

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
- per-window usage reserves for usage windows currently reported by Codex;
- per-window Plan checkpoints for currently reported usage windows;
- explicit Plan breach-notification opt-in.

CLI inspection/reset:

```bash
codexbar settings show
codexbar settings reset
```

Settings schema v3 stores usage reserves, Plan checkpoints, and the Plan breach-notification opt-in. Existing schema-v1 and schema-v2 settings remain readable; simply reading a legacy settings file does not rewrite it. The next explicit valid Save writes canonical schema v3.

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

Release-version authority validation:

```bash
uv run python scripts/validate_release_version_modes.py
```

Plan notification validation scenarios are available through the existing
notification harness, for example:

```bash
uv run python scripts/validate_alerts.py plan-breach --delay 1
uv run python scripts/validate_alerts.py plan-rearm --delay 1
```

Machine-readable Doctor:

```bash
uv run python -m codexbar doctor --json
```

Real redeem validation is intentionally capability-gated because it may spend a real reset credit.

## Persistence

CodexBar maintains independent local persistence responsibilities:

- usage history: schema-v1 SQLite, CURRENT-only observational history;
- reset event ledger: append-only reset/redeem evidence;
- application settings: schema v3 JSON with backward-readable schemas v1 and v2.

No persistence store is allowed to fabricate or replace current authoritative account state.

## Release documentation

Release-specific documents:

- `docs/specs/v1.8/` — frozen v1.8 Plan requirements, tasks, architecture, and test matrix;
- `docs/TRACEABILITY-v1.8.md` — v1.8 release traceability;
- `docs/VALIDATION-v1.8.0.md` — v1.8 target/release evidence;
- `docs/RELEASE-CHECKLIST-v1.8.0.md` — v1.8 release/tag checklist;
- `docs/specs/v1.7/` — frozen v1.7 Diagnose requirements, tasks and architecture;
- `docs/TRACEABILITY-v1.7.md` — v1.7 release traceability;
- `docs/VALIDATION-v1.7.0.md` — v1.7 target/release evidence;
- `docs/RELEASE-CHECKLIST-v1.7.0.md` — v1.7 release/tag checklist;

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

History and Historical Context currently assume one local ChatGPT account at a time. After intentionally switching accounts, clear local History before relying on cross-cycle Context. CodexBar does not decode private auth/JWT material to manufacture an account identifier.
