# CodexBar v1.7 Phase H — Final Performance Evidence

Status: **TASK-783 green on target workstation**
Recorded: 2026-08-14
Target: Python 3.14.4 / Linux 7.0.0-29-generic
Samples: N=20
Release metadata during validation: 1.6.0

## Gate result

Final aggregate result:

- `overall_hard_pass = true`;
- Phase A characterization completed on attempt 1;
- Phase C characterization completed;
- Phase D characterization completed;
- local Doctor characterization completed independently;
- IPC remains intentionally pending physical GUI validation.

All currently executable hard performance gates are green.

## Frozen budgets

| Metric | Final p95 | Budget / target | Result |
|---|---:|---:|---|
| Doctor local-only | 1.516 ms | <= 500 ms | PASS |
| Context cache hit | 0.0047 ms | <= 5 ms | PASS |
| Context Qt synchronous | 0.0408 ms | <= 50 ms | PASS |
| Context cold | 17.383 ms | <= 150 ms engineering target | PASS |
| SHOW_DETAILS IPC | pending | <= 250 ms | physical run pending |

Context semantic equivalence also passed.

## Phase A to Phase H comparison

| Metric | Phase A p95 | Final p95 | Change |
|---|---:|---:|---:|
| app-server spawn | 1.613 ms | 1.410 ms | -12.6% |
| app-server initialize | 329.143 ms | 313.832 ms | -4.7% |
| app-server request | 912.809 ms | 951.454 ms | +4.2% |
| app-server parse | 0.235 ms | 0.236 ms | +0.5% |
| app-server shutdown | 31.784 ms | 31.892 ms | +0.3% |
| app-server total | 1235.441 ms | 1259.532 ms | +1.9% |
| Current full read | 1222.721 ms | 1206.786 ms | -1.3% |
| Doctor local-only | 1.634 ms | 1.516 ms | -7.2% |
| History 30d read | 38.492 ms | 42.988 ms | +11.7% |
| History 180d read | 38.202 ms | 37.348 ms | -2.2% |
| Context candidate read | 14.502 ms | 9.082 ms | -37.4% |
| Context cold | 21.328 ms | 17.383 ms | -18.5% |
| repeated v1.6 Context behavior | 27.211 ms | 17.221 ms | -36.7% |

## Interpretation

The release-critical Context goals are comfortably met:

- cache-hit latency is effectively negligible relative to the 5 ms budget;
- synchronous Qt-side Context work remains far below the 50 ms budget;
- cold Context remains far below the 150 ms engineering target;
- candidate-read and repeated Context paths improved materially versus Phase A.

The app-server request and total one-shot measurements are slightly slower than the
Phase A sample, while spawn/initialize improved. The changes are small relative to
the external request variance and do not alter the Phase G evidence decision to
retain the validated one-shot app-server lifecycle for v1.7.

History 30d p95 is higher than the Phase A sample while 180d is slightly lower.
Neither observation violates a frozen release budget or demonstrates a release
regression requiring a persistence change. The Phase G decision to retain current
prune cadence and SQLite journal behavior therefore remains unchanged.

## TASK-783 closure

TASK-783 is **GREEN**.

Remaining performance evidence:

- `SHOW_DETAILS` IPC p95 must be captured while one real GUI owner is running;
- that measurement belongs to the physical Phase H session and must satisfy
  p95 <= 250 ms.

No release metadata bump is authorized by this document alone.
