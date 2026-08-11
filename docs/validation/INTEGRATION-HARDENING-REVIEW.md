# CodexBar v1.6 — Integration Hardening Review

Baseline reviewed: `28f9460` (`feat: add v1.6 historical context UI`).

This patch is intentionally cross-version: it hardens integration boundaries shared by
v1.4 Current/History, v1.5 Control/Reset/Redeem, and v1.6 Historical Context before
Phase F performance/fault characterization.

## Resolved integration findings

- **IH-01 — one coherent Current/STALE observation:** `LatestAccountObservationReader`
  now marks the whole composed observation stale on upstream failure. Reset Current is
  explicitly unavailable in that state; Budget/Control sees stale usage; Context refuses
  to query history from stale Current.
- **IH-02 — History startup isolation:** failure to open/validate History no longer blocks
  GUI Current. Capture is disabled, History read state remains failure-isolated, and Context
  receives an unavailable history port.
- **IH-03 — Reset Ledger startup/read isolation:** ledger failure no longer blocks Current
  or authoritative reset-current display. Control advice is withheld and manual redeem is
  disabled/fail-closed when the ledger cannot be trusted.
- **IH-04 — expired-credit bug:** already-expired credits are excluded from upcoming expiry
  opportunity calculation.
- **IH-05 — explicit Context wiring:** removed the lateral `presenter.context_presenter`
  injection and `getattr` fallback. The dependency now flows composition -> runtime ->
  `__main__` -> launcher -> control tray -> panel.
- **IH-06 — render retry safety:** Control tray restores the previous rendered-state marker
  if rendering raises, so an optional-panel failure cannot permanently mark an unrendered
  state as rendered.
- **IH-07 — post-redeem coherence:** successful process-manager refetch is adopted directly
  by `TrayController` instead of immediately causing a duplicate upstream read. Generation
  invalidation prevents an older in-flight refresh from overwriting the post-redeem state.
- **IH-08 — Context performance measurement alignment:** characterization now records the
  actual production `HistoricalContextService` path in addition to SQL characterization.
- **IH-09 — cycle-count semantics:** `None` now means the comparison coordinate/count could
  not be defined; `0` is reserved for a defined comparison with zero contributing cycles.
- **IH-10 — Context domain invariants:** coverage-specific payload shape, rank total,
  statistic bounds, range ordering, and quartile ordering are validated by the domain type.
- **IH-11 — SQLite operational contract checks:** startup validates uniqueness, primary-key,
  and index contracts relied upon for history idempotency/query behavior and reset-ledger
  replay/idempotency.
- **IH-12 — benchmark drift guard:** the synthetic fast-load schema is validated against the
  operational storage contract and the full production Context service is benchmarked.
- **IH-13 — retention constant:** 180-day retention has one production source of truth in
  `application/history_policy.py`.
- **IH-14 — local validation hygiene:** `docs/validation/*.local.md` is ignored by Git.

## Additional code-smell corrections

- removed string comparison against `ContextCoverage.value` in application logic;
- removed dynamic `getattr`-based dependency lookup;
- replaced untyped redeem callback/result introspection with `RedeemResult`;
- narrowed redeem UI exception handling to expected application/process failures;
- corrected the default Current-account policy clock to timezone-aware UTC;
- centralized user-facing rank wording through `ContextRank.describe()`;
- added generation-based stale-result rejection to the asynchronous tray refresh path.

## Validation performed while assembling this patch

- Python byte-compilation of all supplied `src`, `scripts`, and `tests` files: PASS.
- integration-wiring architecture tests included in this patch: PASS in the assembly
  environment.
- line-length audit at 100 characters over supplied Python files: PASS.

The complete repository gate must still be run after extracting this root-ready patch,
because the assembly environment did not contain a network-accessible full checkout of the
repository and therefore cannot substitute for the project's full pytest/ruff/mypy gate.

## Hygiene pass 2

A second integration pass simplified the composition root after the first full local gate:

- History construction is now isolated in `_build_history_runtime`; concrete repositories never
  escape their successful branch as `Optional`, eliminating nullable repository plumbing.
- Reset-ledger construction is now isolated in `_build_reset_runtime` with the same fail-closed
  contract.
- Account adapters and projection-provider selection are centralized helpers rather than repeated
  conditional wiring.
- Ruff SIM102/import-order findings from the first local gate were resolved structurally.
- Formatting around newly added dataclasses was normalized to the project style.

This pass intentionally reduces branching and type ambiguity in `build_gui_runtime` rather than
adding casts or `type: ignore` directives.
