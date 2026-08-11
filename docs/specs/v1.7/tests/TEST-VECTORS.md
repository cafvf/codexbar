# CodexBar v1.7 — Canonical Test Vectors

Status: frozen for implementation

## TV-1701 — Overall healthy with Context insufficient

Current: CURRENT and source healthy.
History: healthy.
Context infrastructure: healthy, N=0.
Native: unavailable, Qt fallback healthy.

Expected overall: `healthy`.

## TV-1702 — Stale Current

Last known Current exists but latest source read failed.

Expected:

- Current freshness: stale;
- source operational health: degraded/failed as appropriate;
- overall: `degraded`;
- History remains independently reported.

## TV-1703 — No usable Current

No Current observation exists and source probe/read fails.

Expected overall: `needs_attention`.

## TV-1704 — Metric thresholds

Durations: 1..20 ms.

Expected:

- at N=1: last only;
- N=2: p50 hidden;
- N=3: p50 visible;
- N=19: p95 hidden;
- N=20: p95 visible.

Collector receives samples 1..65 with capacity 64.

Expected retained sequence: 2..65.

## TV-1705 — Context cache identity

Entries:

- (R10,H4,W1) -> A
- request (R10,H4,W1) -> hit A
- request (R11,H4,W1) -> miss
- request (R10,H5,W1) -> miss
- request (R10,H4,W2) -> miss

## TV-1706 — Obsolete Context completion

Start job J1 for (R1,H1,W).
Start J2 after Current advances to R2.
J1 completes before/after J2.

Expected:
J1 never becomes current visible result once R2 is active.

## TV-1707 — History revision zero-effect mutation

History revision H=7.

- duplicate append -> H remains 7;
- prune removes 0 -> H remains 7;
- append new snapshot -> H=8;
- prune removes 3 -> H=9.

## TV-1708 — Explicit zero reserve versus no reserve

Window remaining .50.

Case A: no reserve policy:
- reserve = None;
- headroom = None/not applicable;
- status = NO_POLICY.

Case B: explicit reserve .00:
- reserve = .00;
- headroom = .50;
- status = ABOVE_RESERVE.

The two states are not equivalent.

## TV-1709 — Multi-bucket source preference

Payload contains:

- legacy `rateLimits`: primary used=90%;
- `rateLimitsByLimitId.codex`: primary used=25%;
- `rateLimitsByLimitId.other`: primary used=1%.

Expected CodexBar remaining for selected primary: 75%.

No window from `other` appears.

## TV-1710 — Legacy source fallback

`rateLimitsByLimitId` absent/null.
Legacy primary used=25%.

Expected remaining: 75%.

## TV-1711 — Dynamic source window

Explicit Codex primary duration = 720 minutes, used=40%.

Expected:

- UsageWindowId = `window_720m`;
- dynamic label equivalent to 12 hours;
- remaining = .60.

No 5h/Weekly assumption.

## TV-1712 — Diagnostic secret minimization

Account probe result contains email `person@example.com`.

Expected default Doctor/JSON:
- auth/account capability may be reported;
- raw `person@example.com` does not appear;
- no token/JWT fields appear.

## TV-1713 — Native guide

Windows:
- 12h 100%;
- 30d 100%;
- stale suffix possible.

Expected guide accommodates actual rendered labels and contains no mandatory
literal `5h` or `W`.

## TV-1714 — Redeem async duplicate click

Controller running attempt A.
Second start invoked before A completes.

Expected:
- second start rejected/no external consume;
- exactly one process-manager invocation;
- UI remains running until A terminal result.

## TV-1715 — v1.6 semantic inheritance

All TV-1601..TV-1609 remain canonical and unchanged.
