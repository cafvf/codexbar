# CodexBar v1.8.0 — Validation

Status: release candidate — local release-prep gates green; hosted closure pending
Release theme: Plan
Target desktop: Ubuntu/GNOME/Wayland
Validation date: 2026-08-14

## Implementation-completion automated evidence

Before the release metadata bump, the v1.8 implementation baseline passed:

- pytest: 815 passed in 3.24 s;
- Ruff: PASS;
- strict mypy: PASS over 89 source files;
- compileall: PASS;
- `git diff --check`: PASS.

The implementation baseline commit is:

`b8b83abe4fae33ed873e33cb1a3c5462366266dd`

## Plan semantic evidence

The frozen evaluator vectors P01..P14 are covered by the pure Plan suite. They include no-policy, reserve-only, exact-threshold activation, stepwise checkpoint selection, reserve/checkpoint dominance, ties, missing/invalid reset, non-monotonic checkpoints and zero-duration activation.

Plan alert vectors A01..A10 cover:

- silent initial baseline;
- factual transition into BELOW;
- repeated-BELOW dedupe;
- recovery/rearm;
- delivery disabled with tracker advancement/no replay;
- same-cycle checkpoint activation;
- policy rebaseline;
- reset-cycle rebaseline;
- missing/invalid reset ineligibility;
- STALE non-advancement;
- multi-window isolation.

Settings vectors S01..S08 cover defaults, legacy loads without rewrite, explicit save to schema 3, canonical round-trip and invalid duplicate/type/fraction cases.

## Physical Settings and PlanPanel validation

The target operator validated on Ubuntu/GNOME/Wayland:

- Plan checkpoint add/edit/remove in Settings;
- Plan breach-notification opt-in;
- Save/reopen persistence;
- Cancel without persistence;
- Reset to empty checkpoints/disabled Plan notifications;
- Current Details PlanPanel placement between Control/Budget and Reset action;
- configured/no-active/active Plan behavior;
- immediate Plan rerender after live Settings Save without process restart;
- `72h` checkpoint presentation for the normative 72-hour coordinate;
- `30d` presentation for a 30-day checkpoint;
- Budget remained reserve-only when reserve was 15% and the active Plan checkpoint floor was 90%.

This last check is direct physical evidence for the v1.8 reserve-owner/Budget-independence boundary.

## Physical notification validation

Using the existing notification harness/transport:

### Plan breach

- ABOVE baseline: 0 events;
- transition BELOW: 1 event;
- remain BELOW: 0 repeated events.

### Plan recovery/rearm

Sequence event counts: `0, 1, 0, 1`.

### Plan delivery disabled

- breach while Plan notifications disabled: tracker event recorded, desktop delivery suppressed;
- re-enable while still BELOW: 0 replay;
- recovery then new breach: 1 new notification.

### Plan checkpoint activation

- checkpoint inactive: 0 events;
- same-cycle checkpoint becomes active while remaining is BELOW its floor: 1 event.

### Released usage alerts

The LOW, dedupe, disabled/no-replay and multi-window LOW/EXHAUSTED physical scenarios remained green.

## Desktop/native evidence

The v1.8 target GUI behaved normally during physical Settings/Plan validation. Qt/Wayland emitted non-fatal text-input diagnostic lines during one close/focus transition; there was no traceback or application crash.

v1.8 does not replace the released Ayatana-helper/Qt-fallback architecture. Native/Qt fallback and single-instance behavior remain covered by the released regression suites and must remain green in the final full/hosted gates. A destructive removal of distro packages solely to force fallback is not required for release theater.

No real reset credit is required or consumed for v1.8 Plan validation.

## Final local release-prep evidence

The release-prep tree was validated after the version bump and lock regeneration:

- `uv.lock` changed only the local editable CodexBar package from `1.7.0` to `1.8.0`; no dependency churn was introduced;
- pytest: **819 passed in 3.35 s**;
- Ruff pre/post checks: PASS;
- strict mypy: PASS over 89 source files;
- compileall: PASS;
- `git diff --check`: PASS;
- v1.8 release-contract architecture test: PASS as part of the full suite.

Release-version authority validation reports `1.8.0` consistently in all three modes:

- `uv-run`: metadata/runtime 1.8.0 — PASS;
- editable: metadata/runtime 1.8.0 — PASS;
- isolated `uv-tool`: metadata/runtime 1.8.0 — PASS.

The hosted workflow now uses the release-neutral `scripts/validate_release_version_modes.py` entry point.

## Final release-candidate physical smoke

A final concise smoke on Ubuntu/GNOME/Wayland passed on the release-prep tree:

- normal GUI owner startup;
- native indicator/glance remained usage-focused;
- Open Details opened and closed/reopened normally;
- Plan remained in the intended Current Details position and retained validated semantics;
- Settings opened and closed/reopened normally;
- no duplicate/resurrected window behavior was observed;
- Quit terminated the owner normally.

Qt/Wayland emitted `qt.qpa.wayland.textinput` leave/focus diagnostic lines during window interaction. They were non-fatal: there was no traceback, crash or functional deviation.

The Qt fallback contract remains covered by the complete regression suite. No distro package was destructively removed solely to force a fallback path for release theater.

## README reconciliation

The pre-existing local README expansion was reconstructed exactly from its original Ubuntu/Ayatana/uv-tool transformation and then reconciled with v1.8 Plan documentation. The reconciled release-candidate README preserves the expanded installation/runtime guidance and adds only v1.8-facing changes:

- release-candidate identity;
- Plan capability and Current Details section;
- Plan Settings controls and schema-v3 compatibility;
- release-neutral version validation / Plan notification harness examples;
- v1.8 release-document links.

This closes the README ownership constraint without blind replacement.

## Hosted CI

The existing hosted gate covers Python 3.12, 3.13 and 3.14 with pytest, Ruff, strict mypy, compileall, architecture gates and project/editable version authority. A separate Python 3.14 job validates the isolated uv-tool mode.

Final hosted evidence: **PENDING** until the exact final release-prep commit is pushed.

## Release decision

Implementation behavior and the completed v1.8 physical Plan checks are green.

The local automated, version-authority and target physical gates are green.

The release remains **NOT TAG-READY** until:

1. the exact release-prep commit is pushed;
2. remote `main` is verified at that commit;
3. hosted Python 3.12/3.13/3.14 and isolated uv-tool jobs succeed on that exact commit.

After hosted closure, release-status documentation may be finalized and must itself pass CI on the exact commit chosen for the annotated `v1.8.0` tag. The tag is never created on an unverified commit.
