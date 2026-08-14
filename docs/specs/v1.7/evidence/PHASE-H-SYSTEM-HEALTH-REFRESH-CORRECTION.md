# CodexBar v1.7 Phase H — System Health Refresh Semantics

Status: **correction prepared; physical revalidation pending**
Recorded: 2026-08-14
Related tasks: TASK-782 / TASK-784 / TASK-785 / TASK-789

## Physical finding

The Phase H target session found a semantic inconsistency between two controls
named `Refresh`.

`Open Details` uses the application refresh coordinator. It starts a background
authoritative Current read. The captured observation can update History, and an
open History dialog is refreshed after the tray controller transitions from
loading to fresh.

`System Health` is intentionally a read-only live diagnostic surface. Its
presenter only snapshots already-shared runtime state. The window also refreshes
that snapshot automatically every 750 ms while visible.

A manual `Refresh` button in System Health therefore could not honestly have the
same meaning as `Refresh` in Open Details. Adding an acknowledgement to the
System Health button made the action visible but did not resolve the semantic
ambiguity.

## Final correction

The System Health manual `Refresh` button is removed.

The controls now state:

`Updates automatically while this window is open.`

The existing 750 ms automatic snapshot timer remains unchanged.

The `Close` action remains unchanged.

## Contract

The final v1.7 UI semantics are:

- **Open Details / Refresh** — request new authoritative usage data through the
  normal async refresh pipeline;
- **System Health** — observe live shared runtime health automatically without
  initiating a new source read or persistence mutation;
- **Usage History** — refresh from its controller when a successful authoritative
  usage refresh completes while the dialog is open.

This preserves the protected read-only System Health boundary and removes two
different meanings for the same button label.

## Regression coverage

`tests/gui/test_system_health_auto_refresh.py` verifies that:

- System Health has no manual `Refresh` button;
- the automatic-update explanation is visible;
- explicit dialog snapshot refresh still renders presenter state;
- only `Close` remains as an action button.

The superseded `tests/gui/test_system_health_refresh.py` is removed.

## Gate status

Phase H remains open until focused/global automated gates pass and the corrected
System Health window is physically revalidated on target.
