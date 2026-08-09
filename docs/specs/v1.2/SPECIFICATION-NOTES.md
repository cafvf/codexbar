# v1.2 specification review notes

The v1.2 specification is deliberately narrow.

Key choices:
- transition semantics, not periodic reminder semantics;
- silent first baseline, including startup already LOW/EXHAUSTED;
- state tracking continues while notifications are disabled;
- stale/error outcomes do not participate in alert state;
- temporary window absence does not imply recovery;
- deduplication state is not persisted;
- no settings schema migration in v1.2;
- Linux transport remains an implementation decision pending inspection/ADR.

These choices avoid hidden time/cooldown policy, avoid replay surprises after re-enable/restart, and preserve
the existing `UsageWindow.state(UsagePolicy)` classifier as the single source of truth.

No production code is included in this package.
