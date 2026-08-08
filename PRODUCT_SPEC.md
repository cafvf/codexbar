# CodexBar Product Specification

Status: draft normative

## Purpose
Provide a small Linux desktop monitor that makes the Codex usage information available at a glance,
without requiring the user to enter the interactive CLI solely to inspect usage.

## Product truth
CodexBar reports **what a verified Codex source exposes**. It does not promise an absolute token
balance unless the source explicitly provides that quantity. Usage windows are dynamic data.

## Core user outcome
The user can see current remaining usage, reset times when supplied, freshness, and whether the
reported windows indicate an exhausted limiting quota.

## Stable domain vocabulary
- Usage window: one independently reported quota/rate-limit window.
- Remaining fraction: normalized value in `[0,1]`.
- Snapshot: immutable observation of all windows at a point in time.
- Freshness: whether displayed data is current or cached/stale.
- Limiting window: a window whose valid state prevents continued included usage, when such semantics
  are known from the source contract.

## v1.0 scope
1. Query a verified local Codex source through an adapter.
2. Normalize one or more usage windows.
3. Display remaining fraction and reset time.
4. Preserve last valid snapshot during transient refresh failure and mark it stale.
5. Run as a Linux tray application with a compact panel.

## Non-goals for v1.0
Historical charts, generic developer dashboard, LM Studio/system metrics, plugin architecture, remote
account management, credit purchasing, and prediction of future consumption.

## Non-functional requirements
- Core must be usable without GUI dependencies.
- Domain and application layers are deterministic and independently testable.
- Unknown source schema fails closed.
- UI refresh must not block the GUI thread.
- User-facing timestamps are localized; internal timestamps remain timezone-aware.

## Risks
The Codex usage surface may change independently of CodexBar. A CLI text parser is especially fragile;
therefore source selection and fixture provenance are release gates rather than hidden assumptions.
