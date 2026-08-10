# REQ-UI-003 — Richer current usage visualization

Status: validated — v1.4.0 release candidate
Priority: P1  
Release: v1.4  
Change taxonomy: EVOLUTION

## Requirement

After Phase C is functionally complete, CodexBar SHALL provide a richer representation of current normalized
usage while preserving the existing canonical tray glance and CURRENT/STALE/error semantics.

No new provider semantics are introduced.

The current presentation contract SHALL preserve each reported window's stable `UsageWindowId` so current
presentation can navigate to historical analysis without label matching or reconstruction from history.

## Current percentage compatibility

Existing current presentation renders remaining quota as whole percentages.

v1.4 SHALL preserve that presentation contract for current textual and visual quota indicators unless a
future requirement explicitly changes percentage precision.

A richer visual indicator SHALL represent the same presentation percentage exposed to the user; it SHALL
NOT independently reinterpret or recompute raw/provider data.

## UC-UI-008 — Present current windows clearly

For every currently reported window, details SHALL expose:

- stable window identity through the presentation contract;
- label;
- remaining whole percentage;
- visual remaining indicator;
- AVAILABLE / LOW / EXHAUSTED classification;
- reset timestamp when available;
- relative reset time when meaningful.

Acceptance criteria:

- `AC-UI-034`: every reported window creates one current presentation item.
- `AC-UI-035`: missing windows are omitted rather than fabricated.
- `AC-UI-036`: textual percentage preserves existing whole-percent current presentation semantics.
- `AC-UI-037`: visual remaining indicator represents the same presentation percentage exposed by the
  current view state and does not independently reinterpret provider data.
- `AC-UI-038`: classification uses the existing runtime `UsagePolicy`.
- `AC-UI-039`: unavailable reset metadata does not fabricate a timestamp; the UI MAY explicitly render
  `Reset: not reported`.
- `AC-UI-040`: historical values never substitute for absent current data.
- `AC-UI-040A`: each current presentation item preserves the corresponding stable `UsageWindowId`.

## UC-UI-009 — Communicate freshness

- `AC-UI-041`: CURRENT and STALE are visually distinguishable.
- `AC-UI-042`: STALE preserves the last valid values per existing contracts.
- `AC-UI-043`: observation age derives from `UsageSnapshot.observed_at`.
- `AC-UI-044`: stale presentation creates no new history observation.
- `AC-UI-045`: initial hard error with no cached snapshot creates no fabricated usage card.

## UC-UI-010 — Show reset information

- `AC-UI-046`: available `resets_at` can be shown as localized absolute time.
- `AC-UI-047`: a future `resets_at` can additionally be shown as relative duration.
- `AC-UI-048`: relative duration uses one captured presentation instant.
- `AC-UI-049`: past reset metadata is not silently rewritten as a newly inferred reset.
- `AC-UI-050`: absent `resets_at` remains semantically absent; explanatory text such as
  `Reset: not reported` is permitted.

## UC-UI-011 — Navigate from current window to history

- `AC-UI-051`: a current window can open history focused on the same stable `UsageWindowId`.
- `AC-UI-052`: navigation uses stable identity preserved by the current presentation contract, not label
  matching.
- `AC-UI-053`: no matching historical observations yields the standard empty-history state.
- `AC-UI-054`: navigation causes no extra historical write.
- `AC-UI-054A`: navigation from a current window does not require reconstructing current identity from
  historical storage.

## UC-UI-012 — Preserve tray glance compatibility

- `AC-UI-055`: existing canonical glance semantics remain valid.
- `AC-UI-056`: native Ayatana label remains compatible with existing presentation data.
- `AC-UI-057`: Qt tray fallback remains usable.
- `AC-UI-058`: richer details do not require raw provider data across the native-helper boundary.
- `AC-UI-059`: current refresh remains asynchronous and non-overlapping.


## UC-UI-013 — Preserve GUI lifecycle stability

- `AC-UI-060`: polling an unchanged current state does not rebuild the current details widget tree.
- `AC-UI-061`: current details are composed once and are not replaced after `TrayShell` construction.
- `AC-UI-062`: closing/hiding History and then refreshing CURRENT does not terminate the application.
- `AC-UI-063`: History and Current Details have independent top-level lifecycles.
- `AC-UI-064`: a completed CURRENT refresh re-queries visible History only after a successful FRESH
  transition; hidden History is not re-rendered solely because CURRENT refreshed.

## Architectural invariants

- `INV-UI-003-001`: richer visualization consumes normalized current-state/application contracts.
- `INV-UI-003-002`: UI performs no provider parsing.
- `INV-UI-003-003`: current state is never reconstructed from history.
- `INV-UI-003-004`: existing Ayatana/system-Python isolation remains intact.
- `INV-UI-003-005`: no raw provider payload or credential crosses presentation boundaries.
- `INV-UI-003-006`: validated earlier UI/settings/alert behavior remains backward compatible unless
  explicitly superseded.
- `INV-UI-003-007`: stable `UsageWindowId` crosses the current presentation boundary as identity-bearing
  presentation data.
- `INV-UI-003-008`: current whole-percent formatting remains the canonical current display precision for
  v1.4.
- `INV-UI-003-009`: periodic controller polling does not imply periodic widget reconstruction.
- `INV-UI-003-010`: History ownership is independent from the Current Details dialog.
- `INV-UI-003-011`: current `TrayController` remains free of history-read/storage dependencies.

## Primary test specification

Acceptance: `tests/acceptance/test_req_ui_003_current_details.py`

Required scenarios:

1. multiple current windows;
2. missing window omission;
3. stable `UsageWindowId` preserved in current presentation state;
4. AVAILABLE/LOW/EXHAUSTED boundaries;
5. whole-percent text/visual consistency for a non-integer domain percentage such as 63.9%;
6. stale current snapshot;
7. future reset absolute/relative presentation;
8. absent reset;
9. current-to-history navigation by stable id;
10. current-to-history with no retained samples;
11. canonical glance regression;
12. native-helper boundary regression.

Architecture/regression guards should be added to:
`tests/acceptance/test_v1_4_architecture_invariants.py`

Existing v1.3 architecture evidence that keeps history storage out of the current `TrayController` SHALL be
preserved or strengthened rather than removed merely to implement navigation.
