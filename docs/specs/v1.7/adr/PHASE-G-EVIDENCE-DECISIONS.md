# Phase G ADR — Evidence-gated maintenance decisions

Status: **closed for v1.7**
Release: v1.7.0 — Diagnose
Tasks: TASK-774..779
Target evidence recorded: 2026-08-14

## Decision rule

The frozen v1.7 default is **retain current behavior** unless measured evidence
justifies a change. A warning or a plausible optimization is not sufficient by
itself.

## Persistent app-server session

Outcome: **RETAIN one-shot app-server lifecycle in v1.7.**

Phase A measured meaningful lifecycle overhead, but request latency remained the
dominant single phase and no supervised reconnect/lifecycle recovery design was
validated. The evidence rule therefore does not authorize a persistent session.

No production change is made in Phase G.

## History prune cadence

Outcome: **RETAIN the current prune cadence.**

Target characterization used 30 maintenance cycles on an isolated schema-v1
database.

Measured append cost:

- p50: `0.294 ms`;
- p95: `0.400 ms`;
- max: `0.474 ms`;
- errors: `0`.

Measured prune cost:

- p50: `0.171 ms`;
- p95: `0.274 ms`;
- max: `0.383 ms`;
- errors: `0`.

The first prune removed 12 intentionally expired rows. The remaining 29 of 30
successful prune calls removed zero rows, giving a zero-effect frequency of
`0.9667`.

Although zero-effect prune frequency is high, the absolute cost is sub-millisecond
and no operational failure was observed. The evidence does not justify changing
the cadence or redefining the 180-day retention edge.

Production behavior remains unchanged.

## SQLite journal mode / WAL

Outcome: **RETAIN the current journal behavior; do not enable WAL in v1.7.**

Thirty concurrent rounds were run for both DELETE and WAL, each combining:

- one writer performing append + prune;
- one History reader;
- one lean Context reader.

DELETE results:

| Operation | p50 (ms) | p95 (ms) | max (ms) | Errors |
|---|---:|---:|---:|---:|
| writer | 1.922 | 2.276 | 3.194 | 0 |
| History read | 3.895 | 5.547 | 5.855 | 0 |
| Context read | 0.918 | 1.138 | 1.223 | 0 |

WAL results:

| Operation | p50 (ms) | p95 (ms) | max (ms) | Errors |
|---|---:|---:|---:|---:|
| writer | 0.749 | 1.053 | 1.300 | 0 |
| History read | 2.197 | 2.748 | 4.005 | 0 |
| Context read | 0.958 | 1.203 | 1.558 | 0 |

WAL reduced writer and History-read latency in this synthetic concurrent fixture,
but DELETE already completed every operation without lock errors and with low
single-digit-millisecond p95 latency. Context-read latency was effectively similar.

The frozen decision requires meaningful lock/contention impact before changing
journal mode. That condition was not met. WAL therefore remains an unneeded
production migration for v1.7.

## Ayatana replacement path

Outcome: **RETAIN the validated Ayatana helper + Qt fallback for v1.7.**

Target diagnostic result:

- exit code: `0`;
- system Python: PASS;
- helper: PASS;
- environment: PASS (`ubuntu:GNOME`, Wayland);
- GI import: PASS;
- Ayatana import: PASS;
- GTK import: PASS;
- indicator creation: PASS;
- menu binding: PASS;
- label set: PASS;
- active status: PASS;
- GLib loop: PASS.

The diagnostic emitted a deprecation warning recommending
`libayatana-appindicator-glib`. This identifies a future migration candidate, not a
v1.7 failure.

A replacement still requires a separate prototype, automated diagnostics and
physical target validation before the current helper is removed. No migration is
authorized in v1.7.

## canberra GTK warning

Outcome: **NO hard canberra dependency in v1.7.**

The target diagnostic emitted:

`Failed to load module "canberra-gtk-module"`

while the full native-indicator API diagnostic completed successfully with exit
code `0`.

No missing CodexBar behavior was observed. The warning is therefore classified as
non-blocking environment noise for v1.7. A hard dependency would only silence a
cosmetic warning and is not justified.

## Property-based testing

Outcome: **NO new property-based testing dependency in v1.7.**

The release already has deterministic canonical Context vectors plus explicit
cache, revision, stale-result, controller, redeem and architecture coverage. No
unique release-blocking state-space gap has been demonstrated that requires a new
dependency.

Property-based testing remains a future enhancement if a concrete defect class or
larger runtime state space justifies it.

## Final Phase G maintenance decisions

| Item | v1.7 decision |
|---|---|
| Persistent app-server | Retain one-shot |
| History prune cadence | Retain current cadence |
| SQLite WAL | Retain current journal behavior |
| Ayatana backend | Retain validated helper + Qt fallback |
| canberra dependency | Do not add |
| Property-based dependency | Do not add |

All evidence-gated maintenance decisions required by TASK-779 are closed without
speculative production changes.
