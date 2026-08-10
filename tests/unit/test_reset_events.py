from datetime import UTC, datetime

import pytest

from codexbar.application.reset_events import (
    InventoryBaseline,
    ResetEvent,
    ResetEventId,
    ResetEventProvenance,
    ResetEventType,
    SequencedResetEvent,
)
from codexbar.domain.reset import DetailCoverage


def test_reset_event_is_typed_versioned_and_sequence_record_is_positive() -> None:
    event = ResetEvent(
        ResetEventId("evt-1"),
        ResetEventType.INVENTORY_BASELINE,
        datetime(2026, 8, 10, 12, tzinfo=UTC),
        ResetEventProvenance.OBSERVATION,
        InventoryBaseline(2, DetailCoverage.COUNT_ONLY),
    )
    record = SequencedResetEvent(1, event)

    assert record.event.payload_version == 1
    assert record.event.event_id.value == "evt-1"


def test_event_identity_and_sequence_reject_invalid_values() -> None:
    with pytest.raises(ValueError):
        ResetEventId(" ")
    with pytest.raises(ValueError):
        SequencedResetEvent(
            0,
            ResetEvent(
                ResetEventId("evt"),
                ResetEventType.INVENTORY_BASELINE,
                datetime(2026, 8, 10, 12, tzinfo=UTC),
                ResetEventProvenance.OBSERVATION,
                InventoryBaseline(0, DetailCoverage.DETAILS_COMPLETE),
            ),
        )
