# CodexBar v1.7 — Acceptance Criteria

Status: frozen for implementation

## AC-1701 — One health model

CLI text, JSON and System Health UI are demonstrably derived from the same typed
health model rather than three independent diagnostic implementations.

## AC-1702 — Orthogonal states

A Context result with no comparable cycles can report healthy infrastructure while
showing insufficient/unavailable evidence.

## AC-1703 — Overall health

- healthy Current + healthy Qt fallback + unavailable Ayatana -> overall healthy;
- stale Current after source failure -> overall degraded;
- no usable Current and failed source -> needs attention.

## AC-1704 — Doctor safety

Running Doctor changes no settings/history/ledger/account/reset-credit state.

## AC-1705 — Diagnostic schema

`doctor --json` parses as JSON, reports schema version 1, and does not expose raw
email/token/auth material.

## AC-1706 — Bounded metrics

One operation family never retains more than 64 samples; p50 and p95 suppression
thresholds are exact.

## AC-1707 — Single instance

Two normal GUI launch attempts result in one runtime owner. The second launch
focuses Open Details and exits.

## AC-1708 — Stale IPC recovery

A stale instance endpoint can be reclaimed without manual user file editing.

## AC-1709 — Ambiguous ownership fails closed

When ownership cannot be safely established, CodexBar does not knowingly start a
second active GUI owner.

## AC-1710 — Context cache

Repeated Context request with identical CurrentRevision/HistoryRevision/window
returns an equal cached result and meets the cache-hit characterization budget.

## AC-1711 — Cache invalidation

New Current revision or effective History revision invalidates the relevant cache
entry.

## AC-1712 — Context stale result

An older asynchronous Context result cannot overwrite state produced for a newer
revision pair.

## AC-1713 — Lean projection

Context candidate read does not construct unrelated rich History presentation
models and does not move frozen Context selection/statistics into SQL.

## AC-1714 — Context UI responsiveness

Qt render/action code does not execute Context repository/full-summary work
synchronously.

## AC-1715 — Context semantic regression

All v1.6 Context canonical vectors and protected behavior pass unchanged.

## AC-1716 — Redeem UI responsiveness

A deliberately delayed fake consume/refetch operation leaves the UI event path
responsive and exposes an in-progress state.

## AC-1717 — Redeem safety regression

Durable begin, serialization, idempotent retry, unknown outcome, manual
confirmation and refetch semantics remain green.

## AC-1718 — Account lineage honesty

Doctor/System Health state explicitly says History is not account-namespaced;
production code does not parse private auth/JWT storage for lineage.

## AC-1719 — Multi-bucket source

A fixture containing both legacy `rateLimits` and an explicit
`rateLimitsByLimitId.codex` uses the explicit Codex snapshot.

## AC-1720 — Legacy source

A legacy-only rate-limit fixture remains readable.

## AC-1721 — Unrelated source bucket

Additional non-Codex bucket fixtures do not create extra CodexBar Current windows.

## AC-1722 — Budget no policy

No reserve -> no numeric policy headroom and UI states "not applicable" or
equivalent.

## AC-1723 — Native stderr

A helper emitting sustained stderr cannot block the helper protocol; retained
diagnostic output remains bounded.

## AC-1724 — Dynamic native guide

Native guide generation works for non-5h/non-weekly dynamic windows.

## AC-1725 — CI range

GitHub CI has green headless coverage for Python 3.12, 3.13 and 3.14.

## AC-1726 — Version authority

Project metadata and runtime package version cannot drift through separate source
literals.

## AC-1727 — Performance evidence

Phase A and final characterization record all REQ-PERF metrics and stop/go
decisions.

## AC-1728 — Evidence gates do not force change

Persistent app-server, prune cadence, WAL and Ayatana migration may validly end
with "retain v1.6 implementation" when evidence does not justify change.

## AC-1729 — Physical desktop lifecycle

Open Details, History, Context, Settings, native/Qt tray behavior and closing/
reopening remain stable on target Ubuntu/GNOME/Wayland.

## AC-1730 — No scope leakage

No v1.7 production behavior adds forecasting, automatic redeem, Context-driven
alerts, Cycle Explorer or new reset-fact notifications.
