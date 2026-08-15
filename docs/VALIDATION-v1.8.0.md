# CodexBar v1.8.0 — Validation

Status: released
Release theme: Plan
Target desktop: Ubuntu/GNOME/Wayland
Release date: 2026-08-14
Release tag: `v1.8.0`

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

The v1.8 target GUI behaved normally during physical Settings/Plan validation. Qt/Wayland emitted non-fatal text-input diagnostic lines during close/focus transitions; there was no traceback or application crash.

v1.8 does not replace the released Ayatana-helper/Qt-fallback architecture. Native/Qt fallback and single-instance behavior remain covered by the released regression suites. A destructive removal of distro packages solely to force fallback was not required.

No real reset credit was required or consumed for v1.8 Plan validation.

## Final local release-prep evidence

The release-prep tree was validated after the version bump and lock regeneration:

- `uv.lock` changed only the local editable CodexBar package from `1.7.0` to `1.8.0`; no dependency churn was introduced;
- pytest: **819 passed**;
- Ruff pre/post checks: PASS;
- strict mypy: PASS over 89 source files;
- compileall: PASS;
- `git diff --check`: PASS;
- v1.8 release-contract architecture test: PASS as part of the full suite.

Release-version authority validation reports `1.8.0` consistently in all three modes:

- `uv-run`: metadata/runtime 1.8.0 — PASS;
- editable: metadata/runtime 1.8.0 — PASS;
- isolated `uv-tool`: metadata/runtime 1.8.0 — PASS.

The hosted workflow uses the release-neutral `scripts/validate_release_version_modes.py` entry point.

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

The pre-existing local README expansion was reconstructed from its original Ubuntu/Ayatana/uv-tool transformation and then reconciled with v1.8 Plan documentation. The released README preserves the expanded installation/runtime guidance and adds v1.8-facing changes:

- release identity;
- Plan capability and Current Details section;
- Plan Settings controls and schema-v3 compatibility;
- release-neutral version validation / Plan notification harness examples;
- v1.8 release-document links.

This closed the README ownership constraint without blind replacement.

## Hosted release-prep CI evidence

Release-prep commit:

`dd87b4716fe29c5d433704079b729338c42e33c4`

Remote `main` was verified at the same commit.

GitHub Actions run:

`31858424480` — **SUCCESS**

Hosted jobs:

- Python 3.12 — SUCCESS (job `94947313261`);
- Python 3.13 — SUCCESS (job `94947313317`);
- Python 3.14 — SUCCESS (job `94947313325`);
- isolated uv-tool version mode — SUCCESS (job `94947313274`).

Each Python matrix job completed hosted pytest, Ruff, strict mypy, compileall, architecture-gate and project/editable version-authority steps successfully. The separate uv-tool job completed the release-neutral isolated installation/version check successfully.

## Final tag-target CI evidence

Evidence-closure/tag-target commit:

`8edf0154f80862c283ea20f5f2e9e5fcbca8e734`

Remote `main` was verified at that commit before tagging.

GitHub Actions run:

`31858617233` — **SUCCESS**

Hosted jobs:

- Python 3.12 — SUCCESS (job `94947807995`);
- Python 3.13 — SUCCESS (job `94947807960`);
- Python 3.14 — SUCCESS (job `94947807946`);
- isolated uv-tool version mode — SUCCESS (job `94947807935`).

This exact commit therefore passed the same hosted release contract used for the release-prep commit and became the authorized tag target.

## Annotated tag verification

Remote ref:

`refs/tags/v1.8.0`

Annotated-tag object SHA:

`47411ee438fdb10745a5bd1fdce1d76067ab4cee`

The annotated tag object points to:

`8edf0154f80862c283ea20f5f2e9e5fcbca8e734`

Tag message:

`CodexBar v1.8.0 — Plan`

GitHub tagger timestamp:

`2026-08-15T02:15:46Z`

This corresponds to the 2026-08-14 project-local release date in America/Maceio.

GitHub verification metadata reports `verified: false` with reason `unsigned`. The release process did not require a signed tag, so this is recorded as factual metadata rather than a release blocker.

## Release decision

**RELEASED.**

All required implementation, regression, version-authority, physical desktop, release-prep hosted, final tag-target hosted and remote annotated-tag verification gates are closed.

The immutable `v1.8.0` tag points to the exact green commit `8edf0154f80862c283ea20f5f2e9e5fcbca8e734`.

Any documentation synchronization after tag creation occurs on `main` and does not move or rewrite the released tag.
