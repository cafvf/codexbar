# REQ-USAGE-001 — Query and present Codex usage

Status: validated on target Linux workstation  
Priority: P0  
Release: v1.0

## Requirement
CodexBar SHALL obtain the usage/quota state exposed by the verified local Codex app-server and present
every valid usage window without fabricating absent information.

## External contract
Normative adapter source: ADR-002, `codex app-server` -> `account/rateLimits/read`.

The source reports **used percent**; the domain reports **remaining fraction**:

`remaining = (100 - usedPercent) / 100`.

### UC-USAGE-001 — Get current usage
Input: `GetUsageQuery(force_refresh: bool)`.
Output: `UsageSnapshot` or a normalized `UsageError`.

- AC-USAGE-001: `usedPercent=25` maps to remaining `Decimal("0.75")`.
- AC-USAGE-002: every reported valid primary/secondary window is preserved.
- AC-USAGE-003: a null/absent window is not synthesized as zero.
- AC-USAGE-004: domain fractions outside `[0,1]`, including non-finite values, are rejected.
- AC-USAGE-005: non-null source reset timestamps become timezone-aware datetimes.
- AC-USAGE-006: known source/process/protocol failures use typed `UsageSourceError` subclasses.
- AC-USAGE-007: malformed or unsupported source schema fails closed; no partial invented snapshot.

### UC-USAGE-002 — Present usage
The presentation layer maps a valid snapshot to immutable view state without consulting infrastructure.

- AC-USAGE-008: zero remaining is a valid exhausted state, not an exception.
- AC-USAGE-009: UI modules do not import infrastructure modules.

### UC-USAGE-003 — Preserve last valid observation
On transient source failure, the last valid snapshot MAY be shown if one exists, but MUST be marked
stale and retain its original observation timestamp.

- AC-USAGE-010: prior valid data returned after a transient failure has `freshness=STALE`.

## Policy decision
The LOW visual state is not inferred from Codex. Its threshold is an explicit `UsagePolicy`, currently
20% remaining by default, and therefore can later become user-configurable without changing source
semantics.
