# CodexBar v1.7 Phase H — Physical Target Checklist

Status: **GREEN — see PHASE-H-PHYSICAL-EVIDENCE.md**
Target: Ubuntu / GNOME / Wayland
Tasks: TASK-784..786

Record PASS / FAIL / capability SKIP for every item. Do not convert an API
diagnostic into a claim of physical rendering.

## Preconditions

- local global automated gate is green;
- one normal installed/checkout CodexBar target is available;
- no destructive redeem is attempted unless a safe unresolved reset credit exists.

## PH-H-01 — initial owner

Start one normal GUI owner.

Expected:

- one tray/indicator owner appears;
- Current continues updating;
- no duplicate indicator is created.

## PH-H-02 — second-instance focus

With the first owner running, launch `codexbar --gui` again.

Expected:

- second process exits;
- existing Open Details is focused/shown;
- no second polling/notifier/indicator owner appears.

Then run the Phase H characterizer with `--with-ipc` to capture the 20-sample
SHOW_DETAILS p95 budget.

## PH-H-03 — Open Details lifecycle

Open, close, reopen Open Details repeatedly.

Expected:

- Current is readable;
- reset credits remain factual;
- Budget no-policy state remains "not applicable" when no reserve exists;
- no Context or System Health surface is embedded into Open Details.

## PH-H-04 — History + Context

Open Usage History and exercise Historical Context.

Expected:

- History remains usable;
- Context loads asynchronously without freezing the surface;
- stale/older completion does not visibly replace a newer request;
- coverage/evidence wording remains descriptive, not predictive.

## PH-H-05 — System Health

Open the separate System Health window.

Expected:

- default view is human-readable;
- technical details remain behind the details affordance;
- lineage honestly reports the local single-account History assumption;
- Context insufficient evidence alone does not degrade overall app health;
- close/reopen remains stable.

## PH-H-06 — native indicator

Run the native indicator diagnostic and observe the actual desktop owner.

Expected:

- API diagnostic completes;
- the normal native indicator physically renders and remains responsive;
- deprecation/canberra warnings remain non-blocking if observed.

## PH-H-07 — Qt fallback

Validate Qt fallback only through a supported/safe failure path already available
on the target. Do not uninstall distro packages merely to force the test.

Expected:

- native-helper unavailability does not crash the GUI;
- Qt fallback remains usable;
- overall health does not treat unavailable Ayatana as fatal when Qt fallback is
  healthy.

If no safe target failure path is available during this run, record a justified
capability SKIP and retain the prior physically validated fallback evidence.

## PH-H-08 — redeem responsiveness

If a safe unresolved reset-credit capability exists:

- initiate the normal confirmed manual redeem/retry path;
- verify explicit in-progress state;
- verify the UI remains responsive;
- verify duplicate activation is prevented;
- verify authoritative refetch/result handling.

If no safe unresolved credit exists, record:

`SKIP — no safe unresolved redeem capability on target`

Do not create or consume a credit merely to satisfy the release checklist.

## PH-H-09 — Settings and closure/reopen stability

Open Settings, close it, reopen it, then repeat History, Open Details and System
Health.

Expected:

- no duplicate owners;
- no window resurrection from late background work;
- no crash;
- no regression in settings display.

## Closure

Phase H physical gate is green when all executable checks pass and any SKIP is a
documented capability SKIP allowed by the frozen release contract.
