# CodexBar v1.7 Phase G — CI + Metadata + Evidence

Status: **local evidence closed; global gate and hosted CI pending**
Tasks: TASK-770..779
Base: `471e43a859414e27d9f4ffdad91e6761a30345bc`

## Remote precondition

The Phase D–F commit is present on remote `main` at the exact SHA above.

Before Phase G, the repository had no `.github/workflows` directory and the remote
commit had no hosted status checks or workflow runs. Phase G intentionally closes
that gap.

## TASK-770 / TASK-771 — hosted headless gate

Phase G adds `.github/workflows/ci.yml` with:

- Ubuntu hosted runners;
- Python 3.12, 3.13 and 3.14 matrix;
- pytest;
- Ruff;
- strict mypy;
- compileall;
- explicit architecture-test execution;
- Qt offscreen mode for headless GUI imports/tests;
- read-only repository permissions.

Physical Ayatana/GNOME rendering and wall-clock performance thresholds remain
outside hosted CI.

Hosted evidence remains pending until the Phase G commit is pushed and all matrix
entries are observed green.

## TASK-772 / TASK-773 — version authority

`pyproject.toml` remains the sole release-version literal authority.

`codexbar.__version__` now derives from installed package metadata rather than an
independent source literal.

Target validation under Python 3.14:

| Mode | Project | Runtime | Metadata | Result |
|---|---|---|---|---|
| `uv run` | 1.6.0 | 1.6.0 | 1.6.0 | PASS |
| editable | 1.6.0 | 1.6.0 | 1.6.0 | PASS |
| isolated `uv tool` | 1.6.0 | 1.6.0 | 1.6.0 | PASS |

The project version intentionally remains `1.6.0` during Phase G. Phase H changes
the single `pyproject.toml` authority to `1.7.0` at release preparation.

## TASK-774 — History append/prune characterization

Target run:

- samples: `30`;
- recorded at: `2026-08-14T16:57:15.319974+00:00`.

Append:

- p50: `0.294 ms`;
- p95: `0.400 ms`;
- max: `0.474 ms`;
- errors: `0`.

Prune:

- p50: `0.171 ms`;
- p95: `0.274 ms`;
- max: `0.383 ms`;
- errors: `0`.

Prune effects:

- first call removed 12 intentionally expired rows;
- 29/30 successful prune calls removed zero rows;
- zero-effect frequency: `0.9667`.

Decision: **retain current prune cadence**.

The zero-effect frequency is high, but the measured absolute cost is
sub-millisecond. There is no material avoidable cost justifying a new cadence or a
changed 180-day retention contract.

## TASK-775 — concurrent Current/History/Context and WAL decision

Thirty concurrent rounds were run in each journal mode.

DELETE:

| Operation | p50 (ms) | p95 (ms) | max (ms) | Errors |
|---|---:|---:|---:|---:|
| writer | 1.922 | 2.276 | 3.194 | 0 |
| History read | 3.895 | 5.547 | 5.855 | 0 |
| Context read | 0.918 | 1.138 | 1.223 | 0 |

WAL:

| Operation | p50 (ms) | p95 (ms) | max (ms) | Errors |
|---|---:|---:|---:|---:|
| writer | 0.749 | 1.053 | 1.300 | 0 |
| History read | 2.197 | 2.748 | 4.005 | 0 |
| Context read | 0.958 | 1.203 | 1.558 | 0 |

WAL improved writer and History-read timings in the synthetic fixture, but DELETE
showed no lock/contention failure and all p95 values remained low.

Decision: **retain current journal behavior; do not enable WAL in v1.7**.

The frozen WAL evidence gate requires meaningful lock/contention impact, which was
not demonstrated.

## TASK-776 / TASK-777 — Ayatana and canberra

Target native diagnostic recorded:

- diagnostic exit code: `0`;
- Ayatana deprecation warning: observed;
- canberra warning: observed;
- all native API diagnostic steps: PASS;
- GLib loop: PASS.

The Ayatana warning recommends the newer GLib implementation for newly written
code. That is a migration candidate, but not evidence that the current validated
backend is failing.

Decision: **retain the current Ayatana helper + Qt fallback for v1.7**.

The canberra warning appeared while the native diagnostic still completed
successfully. No missing CodexBar behavior was demonstrated.

Decision: **do not add a hard canberra dependency**.

Physical shell rendering remains separate evidence and is not inferred from this
diagnostic.

## TASK-778 — property-based testing

Decision: **do not add a new property-based testing dependency in v1.7**.

The deterministic canonical and state-transition coverage remains sufficient for
the current release scope. No unique release-blocking coverage gap was identified.

## TASK-779 — explicit decision closure

`docs/specs/v1.7/adr/PHASE-G-EVIDENCE-DECISIONS.md` records the final decisions:

- app-server one-shot: retain;
- prune cadence: retain;
- WAL: retain current mode;
- Ayatana backend: retain;
- canberra hard dependency: reject;
- property-based dependency: reject for v1.7.

No evidence-gated item forces a speculative production change.

## Local gate state

Focused Phase G gate after correcting the generated workflow/test package:

- release metadata test: PASS;
- version-authority architecture tests: PASS;
- CI-contract architecture tests: PASS;
- strict mypy: PASS.

The remaining local requirement is the full global gate after applying this
evidence closure.

## Gate G remaining evidence

Phase G is not complete until:

1. the final local global gate is green;
2. Phase G changes are committed and pushed;
3. the hosted Python 3.12/3.13/3.14 workflow is observed green.

No further production change is justified by the captured Phase G maintenance
evidence.
