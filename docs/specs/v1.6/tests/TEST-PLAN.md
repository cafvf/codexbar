# CodexBar v1.6 — Test Plan

Status: frozen for implementation

## Test layers

1. Unit — pure time/cycle/tolerance/statistical logic.
2. Repository integration — schema-v1 history reads, 180-day retention, query shape.
3. Application integration — Current + History -> Context state.
4. Architecture — dependency direction and no UI/SQLite leakage.
5. Acceptance — product behavior and v1.5 regression contracts.
6. Performance characterization — synthetic 180-day dataset.
7. Physical GUI validation — final target environment.

## Mandatory unit families

### Time-to-reset
- timezone-aware equivalent instants;
- positive h;
- observation at reset h=0;
- observation after reset metadata -> explicitly ineligible/invalid;
- no naive datetime acceptance.

### Hybrid tolerance
Exact boundary tests for:

- h*=100h -> 2h;
- h*=40h -> 2h;
- h*=10h -> 30min;
- h*=2h -> 6min;
- mismatch exactly equal to tolerance -> included;
- mismatch epsilon above -> excluded.

### Cycle grouping
- same window + same reset -> one cycle;
- same window + different reset -> distinct cycles;
- different window + same reset -> distinct cycles;
- missing reset -> ineligible;
- current cycle -> excluded.

### Nearest selection
- nearest before h*;
- nearest after h*;
- equal-distance tie -> later observed_at;
- many polls -> one selected value;
- nearest outside tolerance -> no contribution.

### Coverage
Boundary counts:

- N=0,1,2 -> Insufficient;
- N=3,4 -> Sparse;
- N=5,9 -> Limited;
- N=10,11 -> Established.

### Statistics
- median odd/even N;
- observed min/max;
- rank strict greater/equal/lower;
- Q25/Q75 fixed convention;
- Decimal preservation;
- no float drift at displayed whole-percent boundary.

## Mandatory integration families

- schema-v1 history remains readable;
- 180-day prune behavior;
- Current cycle not counted;
- one comparator per cycle despite high-frequency polling;
- context unavailable does not fail Current;
- corruption/read failure is isolated;
- dynamic UsageWindowId, no fixed 5h/weekly assumption.

## Mandatory acceptance regressions

Protect all v1.5 release invariants, especially:

- no automatic redeem;
- Current/History lifecycle;
- Control/Budget independent of Context;
- settings schema compatibility;
- alerts do not depend on Context;
- tray/native label unchanged;
- History remains observational;
- `UsageSnapshot` does not gain Context fields.

## Performance fixture

Create deterministic synthetic fixtures approximating 180 days at realistic poll
cadence, with multiple windows and reset cycles.

Record:

- row counts;
- DB file size;
- context query p50/p95;
- History query p50/p95;
- full context summary p50/p95.

Do not use performance timing as a flaky normal unit-test assertion on shared CI.
Use a dedicated characterization script/test marker and record the target result.
