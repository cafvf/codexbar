# CodexBar v1.5 Architecture

Status: frozen target architecture for v1.5 implementation
Baseline: v1.4.0

## Design objective

Integrate Control without destabilizing the validated v1.4 boundaries.

The architecture deliberately avoids:
- adding reset credits to UsageSnapshot;
- a second reset polling scheduler;
- full Event Sourcing;
- a global event bus;
- a DI framework;
- concurrent account mutations.

## Layered boundaries

### Domain

Existing usage domain remains stable.

New pure reset/control value types may live in domain when they contain no orchestration/persistence concern:
- ResetCreditDetail;
- ResetCreditInventory;
- DetailCoverage;
- ExpiryKnowledge;
- BudgetStatus / reserve value types.

### Application

Application owns:
- ports;
- composed account observation DTO;
- reset ledger event types/projection contracts;
- ResetLedgerService;
- RedeemProcessManager;
- ResetSituation;
- ResetOpportunityPolicy;
- settings migration/application use cases.

### Infrastructure

Infrastructure owns:
- JSON-RPC gateway;
- app-server parsers;
- SQLite Event Store;
- JSON settings schema codec;
- notify-send transport.

### UI

UI owns:
- current/reset/control view states;
- ResetCreditsPanel / BudgetPanel;
- confirmation/recovery interactions;
- no direct infrastructure imports.

## Ports & Adapters

Application ports:

`UsageProvider`
- existing compatibility interface.

`AccountRateLimitsReader`
- returns AccountRateLimitsObservation.

`ResetCreditConsumer`
- performs explicit consume command.

`ResetEventRepository`
- append/query/inspect reset events.

`NotificationPort`
- transport-neutral notification message.

One `CodexAppServerGateway` infrastructure adapter may implement Reader and Consumer.

`UsageProviderAdapter` projects usage from Reader for existing consumers.

## Composed read

One app-server read produces:

`AccountRateLimitsObservation`
- UsageSnapshot
- ResetCreditReadResult

History capture and reset-ledger derivation run in the same background operation.

## Decorator/capture chain

Preferred GUI path:

CodexAppServerGateway
-> CapturingAccountRateLimitsReader
   -> HistoryService.process(usage)
   -> ResetLedgerService.process(reset result)
-> AccountRateLimitsObservation

Existing HistoryCapturingUsageProvider remains supported for compatibility until task decomposition proves
whether it can be reused internally without duplicate reads.

## CQRS boundary

Commands:
- refresh account state;
- redeem reset;
- save settings.

Queries/read models:
- current account view;
- ledger projection;
- history analytics;
- reset situation/control view.

No full CQRS framework is introduced.

## Event Store + Projection

Reset events are append-only.

Projection is rebuilt/folded from reset events in v1.5 unless performance evidence requires materialization.

Projection SHALL not masquerade as current reset inventory.

## Redeem Process Manager

Redeem is a distributed side effect spanning:
- local durable intent;
- external consume;
- local outcome;
- external refetch.

It is modeled as a Process Manager/Saga-like workflow using the upstream idempotency key.

No two account operations execute concurrently.

## Notification adapter

Current usage AlertEvent SHALL no longer be the transport contract.

Application services format transport-neutral NotificationMessage values.
Infrastructure NotifySendNotificationAdapter only delivers them.

This change must preserve existing LOW/EXHAUSTED notification behavior.

## UI composition

v1.5 SHALL preserve v1.4 explicit ownership and render-on-transition.

Conceptually:

Current Details
- UsageSection / RichUsagePanel
- ResetCreditsSection
- Control/BudgetSection

Reset/control sections SHALL be composed widgets, not appended ad hoc into RichUsagePanel.

History remains top-level/sibling and independent.

## Composition root

v1.5 SHOULD introduce `codexbar/composition.py` or equivalent runtime builder so `__main__.py` remains CLI
dispatch rather than accumulating infrastructure wiring.

No dependency-injection framework is required.

## Design patterns used deliberately

- Ports & Adapters / Hexagonal Architecture
- Anti-Corruption Layer (Codex app-server gateway)
- Adapter (UsageProvider compatibility)
- Decorator (capture/maintenance)
- Repository (SQLite/settings)
- Append-only Event Store
- Projection / Read Model
- CQRS-lite
- Process Manager / Saga
- Explicit State Machine
- Strategy / Policy
- Single Writer / Command Queue
- Composition Root

Patterns explicitly not adopted:
- full Event Sourcing;
- global Event Bus;
- actor framework;
- service locator;
- DI framework.
