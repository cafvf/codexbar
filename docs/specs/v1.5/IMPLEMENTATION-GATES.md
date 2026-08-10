# CodexBar v1.5 — Implementation Gates

Status: normative

## Gate A — Account read

Required:
- protocol/parser tests for count-only, partial, complete, non-expiring and malformed reset detail;
- one-read-per-refresh acceptance test;
- UsageProvider compatibility test;
- usage-history capture regression;
- no reset field on UsageSnapshot architecture test;
- global pytest/Ruff/mypy/compileall green.

No SQLite reset ledger or redeem code is required yet.

## Gate B — Reset Event Store

Required:
- fresh/absent/corrupt/unsupported schema tests;
- baseline/change/coverage/discovery/removal/deadline derivation tests;
- PARTIAL omission negative test;
- COMPLETE omission positive removal test;
- restart projection/dedup test;
- unresolved-attempt projection fixture support;
- `reset-ledger inspect` tests;
- history/settings database isolation;
- global gate green.

## Gate C — Settings/Budget

Required:
- schema-1 load with no disk rewrite;
- schema-2 save/read;
- atomic persistence regression;
- unsupported/corrupt behavior regression;
- immutable per-window reserve model;
- headroom/budget status boundary tests;
- existing settings runtime behavior green;
- global gate green.

## Gate D — Redeem

Required:
- REQUESTED committed before consumer call;
- ledger failure blocks consumer call;
- all four upstream outcomes;
- timeout/possible-send -> OUTCOME_UNKNOWN;
- same attempt ID reused on retry;
- restart recovery;
- serialized refresh/redeem/refetch;
- post-success refetch;
- success + refetch failure isolation;
- no automatic redeem architecture test;
- global gate green.

No production UI redeem button before this gate passes.

## Gate E — Monitor

Required:
- factual situation tests;
- fixed policy threshold boundary tests at exactly 24h/6h/2h/5pp;
- DOES_NOT_EXPIRE negative expiry test;
- COUNT_ONLY/PARTIAL negative expiry test;
- dedup tests;
- notification transport regression for LOW/EXHAUSTED;
- no slope/forecast dependency architecture test;
- global gate green.

## Gate F — UI

Required:
- count/coverage/expiry rendering;
- unknown vs non-expiring distinction;
- reserve/headroom rendering and runtime edit;
- explicit redeem confirmation;
- double activation prevention;
- unresolved attempt recovery UI;
- Current unchanged polls preserve widget identity;
- History open/hide/refresh regressions;
- Ayatana/Qt fallback regression;
- global gate green.

## Gate G — Release

Required:
- full automated suite;
- updated `scripts/validate_v1_5.py`;
- mock/fault-injection physical validation;
- real account read-only reset inventory validation when capability is available;
- real redeem validation only by explicit user choice;
- v1.4 regression target;
- traceability contains no P0 pending criterion;
- release documentation/version metadata consistent.
