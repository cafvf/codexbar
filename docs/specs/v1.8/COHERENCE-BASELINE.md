# CodexBar v1.8 — Coherence baseline

Status: frozen for implementation
Purpose: distinguish justified existing-code repairs from unrelated cleanup before Plan implementation.

## 1. Rule

A pre-existing inconsistency is changed in v1.8 only when at least one is true:

1. it violates an already-released REQ/AC;
2. Plan would depend on the ambiguous behavior;
3. it can cause loss of user configuration;
4. it can misreport the outcome of a destructive operation;
5. it breaks the stable identity/error boundary Plan relies on.

Cosmetic naming alone is insufficient.

## 2. Mandatory/recommended coherence work

### CB-1801 — Preserve terminal redeem success across every expected Current refetch failure

Current implementation catches only `UsageSourceError` after successful consume.

Released `AC-REDEEM-019` is broader: consume success plus refetch failure must preserve terminal action evidence while Current degrades independently.

Change:

```text
RedeemResult.refetch_error:
    UsageError | None

_refetch_after_success():
    catch UsageError
```

Add a regression using `UsageSchemaError` or `UsageParseError`.

Classification: FIX of existing v1.5 contract.

Plan reason: post-redeem adoption is a v1.8 integration path; a successful destructive action must not be reclassified as failed before Plan sees/refuses the resulting Current.

### CB-1802 — Normalize adapter duplicate-window identity failure to UsageSchemaError

The adapter derives `UsageWindowId` from `windowDurationMins`.

If source primary/secondary normalize to duplicate IDs, `UsageSnapshot` currently rejects the duplicate through a domain `ValueError`.

At the external adapter boundary this is malformed/unsupported source data and should fail as normalized `UsageSchemaError`, preserving the v1.0 fail-closed contract.

Add one fixture/vector with duplicate normalized IDs.

Classification: FIX of existing source-boundary contract.

Plan reason: persisted Plan policy is keyed by stable unique `UsageWindowId`.

### CB-1803 — Keep one effective LOW policy inside the account presenter when it already gains AppSettings ownership

`CurrentAccountPresenter.current()` currently calls `UsageViewModel.from_snapshot()` without the configured policy, while the tray uses configured `UsagePolicy`.

The main tray state remains authoritative, so this is not a standalone release blocker.

However, v1.8 naturally requires the presenter to retain current `AppSettings` for Plan evaluation. At that point, passing `self._settings.usage_policy()` removes the mismatch with no new abstraction.

Add one focused test with a non-default LOW threshold.

Classification: small FIX/REFACTOR satisfying existing `AC-SETTINGS-012`.

Rule: do not introduce a new settings runtime solely for this fix.

### CB-1804 — Partial AppSettings updates preserve all unedited fields

Adding schema-v3 fields makes manual reconstruction of `AppSettings` hazardous.

Functional updates such as `with_usage_reserve()` and GUI candidate construction MUST preserve:

- checkpoint policies for unrelated windows;
- Plan notification opt-in;
- all existing fields not edited by the operation.

Implementation may use `dataclasses.replace()` or equivalent immutable reconstruction.

Classification: integration invariant required by schema v3.

### CB-1805 — Shared TimeToReset/FractionDelta ownership without harness break

Move semantic ownership to a neutral domain module, but preserve historical import paths through direct imports/re-exports.

Existing tests importing:

```text
codexbar.domain.context.TimeToReset
```

must remain green.

Existing consumers importing:

```text
codexbar.application.analytics.FractionDelta
```

must remain green.

Classification: REFACTOR, behavior-preserving.

### CB-1806 — Root product-state documentation must reflect released v1.7

Root `PRODUCT_SPEC.md` currently describes v1.7 as a release candidate even though v1.7.0 is released.

Before freezing v1.8 implementation, root product state should say:

```text
Current validated release: v1.7.0 — Diagnose
Active planning/specification release: v1.8 — Plan
```

Classification: DOC coherence.

## 3. Explicitly deferred findings

### Deferred: broadening tray stale fallback to every UsageError

Do not do this.

v1.0 explicitly says malformed/unsupported source schema fails closed, while last-valid STALE fallback is for transient source failure.

Current `RefreshCoordinator` catching `UsageSourceError` preserves that distinction.

`LatestAccountObservationReader` may still mark its captured prior observation stale so Control/Context do not mistake it for authoritative Current.

### Deferred: eliminate startup Settings double-read

Composition and launcher currently both load Settings.

There is a theoretical external-edit race, but the launcher read is explicitly harnessed and no normal in-process Save occurs between the two startup reads.

Changing startup APIs solely for this race is not justified in v1.8.

Revisit only if Plan integration can remove the duplication without widening public/test surfaces.

### Deferred: merge `RedeemAttemptState` and `RedeemProcessStatus`

The enums duplicate values, but the refactor is unrelated to Plan behavior.

Do it only in a separate low-risk maintenance change if later touch makes the conversion cost worthwhile.

### Deferred: rename `reset_at` to `resets_at` across UI

Terminology would improve, but the mechanical churn does not pay for v1.8.

New Plan code should use canonical `resets_at`.

### Deferred: rename `migrated_from_schema_v1`

The name is historically misleading because load does not rewrite the file.

Keep it for compatibility during v1.8 unless a separate refactor proves no external/test cost.

New code should use generic `source_schema_version`.

### Deferred: remove `CurrentAccountController`

It has dedicated tests and represents an existing application contract.

Do not classify it as dead code without a separate reference/use audit.

### Separate repository maintenance, not Plan scope

The audit found:

- tracked `.omx` runtime artifacts, including machine-specific absolute paths;
- empty files whose names end with `:1:1`.

These should be cleaned in a separate CHORE commit so Plan behavior/review stays isolated.

## 4. Protected local work

The user's current checkout has an unstaged locally modified root `README.md`.

v1.8 specification/applicators MUST NOT overwrite, restore, stash or stage that file without an explicit reconciliation step.

README product documentation required by the documentation gate must be merged later against the user's current local README content.
