# CodexBar v1.7 Phase H — Physical Target Evidence

Status: **GREEN**
Recorded: 2026-08-14
Target: Ubuntu / GNOME / Wayland
Related tasks: TASK-782 / TASK-784 / TASK-785 / TASK-786

## Summary

The final v1.7 target validation session completed successfully after one
user-visible System Health semantics defect was corrected and physically
revalidated.

The target operator reported that the Phase H checklist behaved as expected
except for the original System Health `Refresh` control. That control was then
investigated, corrected, and retested on the physical target.

## PH-H-01 — initial owner

PASS.

One normal GUI owner was observed. No duplicate tray/indicator owner was reported.

## PH-H-02 — second-instance focus and IPC

PASS.

The second-instance `SHOW_DETAILS` IPC characterization completed with:

- sample count: 20;
- p50: 0.161 ms;
- p95: 7.853 ms;
- maximum: 12.040 ms;
- frozen budget: p95 <= 250 ms;
- result: PASS.

The second-instance behavior remained consistent with the single-owner contract.

## PH-H-03 — Open Details lifecycle

PASS.

Open Details remained usable across close/reopen cycles and its `Refresh` action
retained the authoritative application-refresh semantics.

## PH-H-04 — Usage History + Historical Context

PASS.

Usage History and Historical Context were reported as operating according to the
Phase H checklist, including responsive asynchronous Context behavior and
descriptive/non-predictive presentation.

## PH-H-05 — System Health

PASS after correction.

Initial physical finding:

- the System Health window exposed a control named `Refresh`;
- unlike Open Details `Refresh`, this action only regenerated the already-shared
  in-memory diagnostic snapshot;
- the window already refreshed that snapshot automatically every 750 ms;
- the duplicate label therefore implied a stronger operation than the control
  actually performed.

Final v1.7 correction:

- the manual System Health `Refresh` button was removed;
- the window now states
  `Updates automatically while this window is open.`;
- the existing automatic 750 ms snapshot refresh remains;
- System Health remains a read-only observer and does not initiate an
  authoritative Current source read or persistence mutation;
- Open Details remains the surface whose `Refresh` initiates authoritative usage
  refresh.

The corrected target was physically retested and the button removal was confirmed.

## PH-H-06 — native indicator

PASS.

The target session was reported as operating according to the native-indicator
diagnostic/checklist and the normal indicator remained functional.

## PH-H-07 — Qt fallback

No destructive target manipulation was required for Phase H.

The release retains the previously validated native-helper plus Qt-fallback
architecture. Phase G evidence remains authoritative for the decision not to
replace Ayatana in v1.7.

## PH-H-08 — redeem responsiveness

Capability SKIP unless a safe unresolved reset-credit capability is naturally
present.

The real target read-only validation recorded zero unresolved redeem attempts.
No reset credit was created or consumed solely to satisfy release validation.

The existing Phase E async/fake/physical evidence remains the release evidence
for responsiveness, duplicate prevention, late-result suppression, and retry
semantics.

## PH-H-09 — Settings and close/reopen stability

PASS.

The target operator reported the requested windows and flows operating according
to the checklist after the System Health correction.

## TASK-782 closure

GREEN.

Real target state was validated for:

- persisted History;
- reset ledger;
- desktop integration;
- live GUI Context;
- live System Health.

## TASK-784 closure

GREEN.

The single-instance, Open Details, History/Context, Settings and window-lifecycle
physical checks are accepted on target.

## TASK-785 closure

GREEN.

Native indicator behavior remains physically accepted. Qt fallback retains the
previous validated evidence and is not forced through destructive package
manipulation.

## TASK-786 closure

GREEN with allowed capability SKIP for a real redeem mutation when no safe
unresolved credit exists.

## Remaining Phase H work

TASK-780 through TASK-786 are now closed.

Release closure still requires:

- final global automated gate after the System Health correction;
- TASK-787 documentation closure;
- TASK-788 version authority bump to `1.7.0` and lock regeneration;
- TASK-789 final local/hosted release gate and tag preparation.
