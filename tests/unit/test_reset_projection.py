from datetime import UTC, datetime

from codexbar.application.reset_events import (
    InventoryBaseline,
    RedeemAttemptId,
    RedeemRequested,
    ResetEvent,
    ResetEventId,
    ResetEventProvenance,
    ResetEventType,
    SequencedResetEvent,
)
from codexbar.application.reset_projection import fold_reset_events
from codexbar.domain.reset import DetailCoverage


def test_projection_supports_restart_and_unresolved_attempt_fixture() -> None:
    events = (
        SequencedResetEvent(
            1,
            ResetEvent(
                ResetEventId("baseline"),
                ResetEventType.INVENTORY_BASELINE,
                datetime(2026, 8, 10, 12, tzinfo=UTC),
                ResetEventProvenance.OBSERVATION,
                InventoryBaseline(2, DetailCoverage.COUNT_ONLY),
            ),
        ),
        SequencedResetEvent(
            2,
            ResetEvent(
                ResetEventId("request"),
                ResetEventType.REDEEM_REQUESTED,
                datetime(2026, 8, 10, 12, 1, tzinfo=UTC),
                ResetEventProvenance.USER_ACTION,
                RedeemRequested(RedeemAttemptId("attempt-1")),
            ),
        ),
    )

    projection = fold_reset_events(events)

    assert projection.last_count == 2
    assert projection.last_coverage is DetailCoverage.COUNT_ONLY
    assert projection.unresolved_attempt_ids == ("attempt-1",)
