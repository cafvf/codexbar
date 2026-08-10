# CodexBar v1.6 — Canonical Statistical Test Vectors

These vectors freeze expected semantics independently of implementation libraries.

## TV-1601 — Tolerance cap

Current h* = 100h.

- alpha*h = 5h
- cap = 2h
- tolerance = 2h

Historical mismatch 2h -> eligible.
Historical mismatch 2h + 1 microsecond -> ineligible.

## TV-1602 — Relative tolerance near reset

Current h* = 2h.

- alpha*h = 0.1h = 6min
- cap = 2h
- tolerance = 6min

Mismatch 6min -> eligible.
Mismatch 6min + 1 microsecond -> ineligible.

## TV-1603 — One value per cycle

One historical cycle has remaining observations:

- h=51h, remaining=.60
- h=50h, remaining=.57
- h=49h, remaining=.55

Current h*=50.2h.

Expected cycle contribution: remaining=.57 only.

## TV-1604 — Equal-distance tie

Historical observations:

- observed_at 10:00, h=50.5h, remaining=.60
- observed_at 11:00, h=49.5h, remaining=.54

Current h*=50h.

Expected selected value: .54 because later observed_at wins.

## TV-1605 — Median and rank

Reference values:

    [.20, .30, .40, .50, .60]

Current remaining = .35.

Expected:

- median = .40
- observed min = .20
- observed max = .60
- historical values greater than current = 3
- equal = 0
- lower = 2
- coverage = Limited

## TV-1606 — Rank ties

Reference values:

    [.20, .30, .30, .50]

Current remaining = .30.

Expected:

- strictly greater = 1
- equal = 2
- strictly lower = 1
- UI must not say simply `lower than 1 of 4` without representing ties.

## TV-1607 — Established quantiles

Reference values:

    [.10, .20, .30, .40, .50, .60, .70, .80, .90, 1.00]

N=10.

Using index `(N-1)*p` and linear interpolation:

- Q25 index = 2.25 -> .325
- Q75 index = 6.75 -> .775
- median = .55

These Decimal expectations are canonical.

## TV-1608 — Current-cycle exclusion

Current:
- window_id W
- resets_at R2

History contains cycles:
- W/R1
- W/R2
- W/R0

Expected comparable cycle identities:
- W/R0
- W/R1

W/R2 is excluded regardless of how many earlier observations exist.

## TV-1609 — Coverage boundaries

N=2 -> Insufficient
N=3 -> Sparse
N=4 -> Sparse
N=5 -> Limited
N=9 -> Limited
N=10 -> Established
