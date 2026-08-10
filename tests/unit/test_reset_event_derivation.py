from datetime import UTC, datetime

from codexbar.application.reset_derivation import derive_inventory_events
from codexbar.application.reset_events import (
    ResetEventId,
    ResetEventType,
    SequencedResetEvent,
)
from codexbar.application.reset_projection import fold_reset_events
from codexbar.domain.reset import (
    DetailCoverage,
    ExpiryKnowledge,
    ResetCreditDetail,
    ResetCreditId,
    ResetCreditInventory,
)

OBS = datetime(2026, 8, 10, 12, tzinfo=UTC)


def detail(value: str) -> ResetCreditDetail:
    return ResetCreditDetail(
        ResetCreditId(value),
        "codexRateLimits",
        "available",
        OBS,
        ExpiryKnowledge.does_not_expire(),
    )


class Ids:
    def __init__(self):
        self.value = 0

    def __call__(self):
        self.value += 1
        return ResetEventId(f"evt-{self.value}")


def project(events):
    return fold_reset_events(
        tuple(SequencedResetEvent(index + 1, event) for index, event in enumerate(events))
    )


def test_baseline_discovery_and_unchanged_poll_are_deterministic() -> None:
    inventory = ResetCreditInventory(
        OBS,
        1,
        DetailCoverage.DETAILS_COMPLETE,
        (detail("A"),),
    )
    ids = Ids()
    first = derive_inventory_events(project(()), inventory, event_id_factory=ids)
    second = derive_inventory_events(project(first), inventory, event_id_factory=ids)

    assert [event.event_type for event in first] == [
        ResetEventType.INVENTORY_BASELINE,
        ResetEventType.CREDIT_DISCOVERED,
    ]
    assert second == ()


def test_partial_omission_does_not_remove_but_complete_omission_does() -> None:
    ids = Ids()
    complete = ResetCreditInventory(
        OBS,
        1,
        DetailCoverage.DETAILS_COMPLETE,
        (detail("A"),),
    )
    initial = derive_inventory_events(project(()), complete, event_id_factory=ids)
    projection = project(initial)

    partial = ResetCreditInventory(
        OBS,
        1,
        DetailCoverage.DETAILS_PARTIAL,
        (),
    )
    partial_events = derive_inventory_events(projection, partial, event_id_factory=ids)
    assert ResetEventType.CREDIT_REMOVED not in {
        event.event_type for event in partial_events
    }

    # Fold the partial coverage change, then a COMPLETE zero inventory may prove removal.
    projection = project(initial + partial_events)
    empty_complete = ResetCreditInventory(
        OBS,
        0,
        DetailCoverage.DETAILS_COMPLETE,
        (),
    )
    complete_events = derive_inventory_events(
        projection,
        empty_complete,
        event_id_factory=ids,
    )
    assert ResetEventType.CREDIT_REMOVED in {
        event.event_type for event in complete_events
    }
