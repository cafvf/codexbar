# Implementation Review Against the New Constitution

Date: 2026-08-08

## What actually existed before this repository
The prior conversation had produced architecture and code sketches, but no durable repository files or
verified executable production adapter. Therefore this review distinguishes **previous design proposals**
from **implemented code**. The current repository is the first concrete baseline in this workstream.

## Decisions retained

| Earlier proposal | Review | Current decision |
|---|---|---|
| Linux tray utility focused on Codex usage | Keep | Product purpose |
| Ports and adapters / hexagonal architecture | Keep, simplify | ADR-001 |
| MVVM-like presentation boundary | Keep without framework ceremony | `UsageViewModel` maps immutable state |
| Typed input/output | Keep | dataclasses/value objects |
| Normalized error taxonomy | Keep | `domain/errors.py` |
| Mock first | Keep | `MockUsageProvider` |
| TDD/specification-driven workflow | Strengthen | Constitution + traceability |

## Decisions changed

### 1. Fixed 5-hour + weekly fields -> dynamic usage windows
Reason: the external product can expose different windows. Hard-coding two fields would leak a volatile
source assumption into the domain.

### 2. Generic plugin architecture -> one provider port
The previous plugin idea was premature. One `UsageProvider` protocol is enough for v1. Additional source
selection can be introduced only after a second real implementation exists.

### 3. Event bus -> explicit refresh coordinator
An event bus adds indirection without solving a v1 requirement. Refresh is a direct use-case invocation;
Qt can schedule it without a domain-wide bus.

### 4. Universal `Result[T,E]` -> typed exceptions at infrastructure boundaries
Python exceptions are appropriate for exceptional provider failures. Valid states such as 0% remaining
stay ordinary domain values. This reduces wrapper boilerplate while preserving a closed error taxonomy.

### 5. `float` percentages -> `Decimal` fraction value object
The domain has one canonical unit (`0..1`). UI converts it to percent. This prevents unit ambiguity.

### 6. Absolute token counter promise -> reported quota/usage state
The product must not call a percentage quota "tokens remaining" unless the source explicitly supplies an
absolute token balance. Current public Codex guidance describes usage limits/credits and the amount
consumed as workload/model dependent; therefore the UI language remains source-faithful.

### 7. Real CLI parser -> structured app-server adapter
Contract verification resolved ADR-002: the implementation uses the documented stable `codex app-server`
JSON-RPC interface and `account/rateLimits/read`. Interactive `/status` prose is not parsed.

### 8. PyQt6 -> PySide6 proposed for GUI shell
Both are viable. PySide6 is kept as an optional dependency because the core must run headless and because
its licensing/distribution model is convenient for a small open-source utility. This remains reversible
until TASK-014 lands.

## Current architecture

```text
UI shell (future PySide6) / CLI smoke surface
        |
UsageViewModel
        |
RefreshCoordinator -> GetCurrentUsage -> UsageProvider (port)
                                           ^
                                           |
                           Mock / CodexAppServerProvider

Domain: Fraction, UsageWindow, UsageSnapshot, errors
```

## Quality assessment

### Strong now
- Domain does not know Codex CLI text or Qt.
- Missing data cannot silently become zero.
- Fractions and timestamps validate their invariants.
- Stale fallback preserves the observation time.
- Architecture rule is executable as a test.
- Scope is explicit; speculative dashboard work is deferred.

### Intentionally incomplete
- The production source is implemented and contract-tested, but could not be exercised against a real
  account in this validation container because `codex` is not installed.
- No Qt tray shell.
- No persistent cache across process restarts.
- `force_refresh` is present in the stable query contract but not yet semantically meaningful; it should
  either be wired to a cache policy when persistence is introduced or removed before v1 if unnecessary.
- Low-usage threshold is now an explicit `UsagePolicy`; 20% remains the default presentation policy and
  is not treated as Codex source semantics.

## Remaining design risks
1. Availability cannot safely be inferred as `min(remaining)` for arbitrary future windows. The adapter
   preserves the backend `rateLimitReachedType` rather than inventing enforcement semantics.
2. The source contract can evolve; captured fixtures and fail-closed parsing are therefore mandatory.
3. `force_refresh` is reserved in the application input contract but has no caching semantics yet.

## Recommended next red-green-refactor slice
1. Specify REQ-UI-001: tray lifecycle, refresh cadence, stale/error presentation, and shutdown behavior.
2. Write acceptance tests before the PySide6 implementation.
3. Implement nonblocking refresh against the already stable use-case/ViewModel boundary.
4. Validate on a target Linux desktop with an installed/authenticated Codex CLI.
