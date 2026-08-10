from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from codexbar.application.reset_events import (
    CountChanged,
    CoverageChanged,
    CreditDetailChanged,
    CreditDiscovered,
    CreditRemoved,
    InventoryBaseline,
    ResetEvent,
    ResetEventId,
    ResetEventPayload,
    ResetEventProvenance,
    ResetEventType,
)
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.domain.reset import DetailCoverage, ResetCreditInventory

EventIdFactory = Callable[[], ResetEventId]


def default_event_id_factory() -> ResetEventId:
    return ResetEventId(str(uuid4()))


def derive_inventory_events(
    projection: ResetLedgerProjection,
    inventory: ResetCreditInventory,
    *,
    event_id_factory: EventIdFactory = default_event_id_factory,
) -> tuple[ResetEvent, ...]:
    occurred_at = inventory.observed_at
    events: list[ResetEvent] = []

    def emit(event_type: ResetEventType, payload: ResetEventPayload) -> None:
        events.append(
            ResetEvent(
                event_id=event_id_factory(),
                event_type=event_type,
                occurred_at=occurred_at,
                provenance=ResetEventProvenance.OBSERVATION,
                payload=payload,
            )
        )

    if projection.last_count is None or projection.last_coverage is None:
        emit(
            ResetEventType.INVENTORY_BASELINE,
            InventoryBaseline(inventory.available_count, inventory.detail_coverage),
        )
    else:
        if projection.last_count != inventory.available_count:
            emit(
                ResetEventType.COUNT_CHANGED,
                CountChanged(projection.last_count, inventory.available_count),
            )
        if projection.last_coverage is not inventory.detail_coverage:
            emit(
                ResetEventType.COVERAGE_CHANGED,
                CoverageChanged(projection.last_coverage, inventory.detail_coverage),
            )

    known = projection.detail_map()
    current = {detail.credit_id.value: detail for detail in inventory.credits}

    for credit_id in sorted(current):
        detail = current[credit_id]
        previous = known.get(credit_id)
        if previous is None:
            emit(ResetEventType.CREDIT_DISCOVERED, CreditDiscovered(detail))
        elif previous != detail:
            emit(
                ResetEventType.CREDIT_DETAIL_CHANGED,
                CreditDetailChanged(previous, detail),
            )

    if inventory.detail_coverage is DetailCoverage.DETAILS_COMPLETE:
        for credit_id in sorted(set(known) - set(current)):
            emit(
                ResetEventType.CREDIT_REMOVED,
                CreditRemoved(known[credit_id].credit_id),
            )

    return tuple(events)
