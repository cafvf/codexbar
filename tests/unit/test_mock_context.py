from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.history import HistoryInterval
from codexbar.domain.models import UsageWindowId
from codexbar.infrastructure.mock_context import MockContextHistoryRepository

NOW = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)


def test_mock_context_exposes_sparse_fixture_for_five_hour_window() -> None:
    repository = MockContextHistoryRepository()
    values = repository.query_candidates(
        UsageWindowId("window_300m"),
        HistoryInterval(NOW - timedelta(days=180), NOW),
    )

    assert len(values) == 3
    assert [value.remaining.value for value in values] == [
        Decimal("0.55"),
        Decimal("0.72"),
        Decimal("0.80"),
    ]


def test_mock_context_weekly_fixture_makes_ties_visually_unmistakable() -> None:
    repository = MockContextHistoryRepository()
    values = repository.query_candidates(
        UsageWindowId("window_10080m"),
        HistoryInterval(NOW - timedelta(days=180), NOW),
    )

    current_weekly = Decimal("0.44")
    assert len(values) == 10
    assert sum(value.remaining.value == current_weekly for value in values) == 4
    assert sum(value.remaining.value < current_weekly for value in values) == 3
    assert sum(value.remaining.value > current_weekly for value in values) == 3
