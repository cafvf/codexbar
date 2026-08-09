from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowSample,
    HistoryInspection,
    HistoryInterval,
    HistoryRepository,
    HistoryState,
    HistoryWriteError,
)
from codexbar.application.history_runtime import (
    HistoryCapturingUsageProvider,
    HistoryService,
)
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)

T0 = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


class Repo(HistoryRepository):
    def __init__(self) -> None:
        self.append_count = 0
        self.prune_count = 0

    def append(self, snapshot: HistoricalSnapshot) -> None:
        self.append_count += 1

    def query(self, interval: HistoryInterval) -> tuple[HistoricalSnapshot, ...]:
        return ()

    def query_window(self, window_id, interval) -> tuple[HistoricalWindowSample, ...]:
        return ()

    def prune(self, cutoff: datetime) -> int:
        self.prune_count += 1
        return 3

    def inspect(self) -> HistoryInspection:
        return HistoryInspection(path="/tmp/history.sqlite3", state=HistoryState.READY_EMPTY)

    def clear(self) -> None:
        pass


class Provider:
    def __init__(self, value: UsageSnapshot) -> None:
        self._value = value

    def get_usage(self) -> UsageSnapshot:
        return self._value


def snapshot(freshness: Freshness = Freshness.CURRENT) -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal("0.50")),
            ),
        ),
        observed_at=T0,
        source=UsageSource.MOCK,
        freshness=freshness,
    )


def test_history_service_reports_capture_and_prune_count() -> None:
    repo = Repo()
    result = HistoryService(repo, clock=lambda: T0).process(snapshot())

    assert result.captured
    assert result.pruned_count == 3
    assert result.diagnostic is None
    assert repo.append_count == 1
    assert repo.prune_count == 1


def test_history_service_reports_capture_when_only_prune_fails() -> None:
    class FailingRepo(Repo):
        def prune(self, cutoff: datetime) -> int:
            raise HistoryWriteError("prune failed")

    result = HistoryService(FailingRepo(), clock=lambda: T0).process(snapshot())

    assert result.captured
    assert isinstance(result.diagnostic, HistoryWriteError)


def test_history_service_ignores_stale_without_maintenance() -> None:
    repo = Repo()
    result = HistoryService(repo, clock=lambda: T0).process(
        snapshot(Freshness.STALE)
    )

    assert not result.captured
    assert repo.append_count == 0
    assert repo.prune_count == 0


def test_history_service_contains_history_error() -> None:
    class FailingRepo(Repo):
        def append(self, snapshot: HistoricalSnapshot) -> None:
            raise HistoryWriteError("boom")

    result = HistoryService(FailingRepo(), clock=lambda: T0).process(snapshot())

    assert not result.captured
    assert isinstance(result.diagnostic, HistoryWriteError)


def test_history_service_rejects_naive_maintenance_clock() -> None:
    repo = Repo()
    service = HistoryService(repo, clock=lambda: T0.replace(tzinfo=None))

    with pytest.raises(ValueError, match="timezone-aware"):
        service.process(snapshot())


def test_history_capturing_provider_runs_service_with_provider_result() -> None:
    repo = Repo()
    wrapped = HistoryCapturingUsageProvider(
        Provider(snapshot()),
        HistoryService(repo, clock=lambda: T0),
    )

    result = wrapped.get_usage()

    assert result == snapshot()
    assert repo.append_count == 1
    assert repo.prune_count == 1
