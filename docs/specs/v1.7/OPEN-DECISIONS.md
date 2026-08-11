# CodexBar v1.7 — Open Decisions

Status: no implementation-blocking decisions

All product/architecture decisions required to begin implementation are frozen.

The items below are evidence-gated outcomes with a defined default. They may end
with no implementation change.

## OD-1701 — Persistent app-server session

Default: retain one-shot lifecycle.

Review only after Phase A decomposes spawn/initialize/request/parse/shutdown cost.

A change requires a documented ADR/spec amendment and safe supervision/reconnect
design.

## OD-1702 — History prune cadence

Default: prune as in v1.6.

Review only if Phase G evidence shows material avoidable cost.

Any reduced cadence must explicitly preserve or redefine the 180-day edge.

## OD-1703 — SQLite WAL

Default: retain current journal behavior.

Review only if concurrent characterization demonstrates meaningful lock/contention
impact.

## OD-1704 — Ayatana backend migration

Default: retain validated backend and Qt fallback.

Migration needs a supported replacement, prototype, automated helper diagnostics
and physical target PASS.

## OD-1705 — canberra GTK warning

Default: treat as non-blocking unless evidence shows missing behavior.

Do not add a hard dependency merely to silence a cosmetic warning.

## OD-1706 — Property-based test dependency

Default: no new dependency.

May be added only if Phase G evaluation demonstrates meaningful unique coverage
for Context/runtime state machines.

## OD-1707 — Future account-aware History

Deferred beyond v1.7.

The current supported app-server account surface has no stable opaque account ID
for this purpose. Revisit only when a supported stable identity exists or a
separate profile model is explicitly designed.
