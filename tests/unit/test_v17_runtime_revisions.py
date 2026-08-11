from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.history import (
    HistoricalSnapshot,
    HistoryInspection,
    HistoryInterval,
    HistoryState,
)
from codexbar.application.history_runtime import HistoryService
from codexbar.application.revisions import CurrentRevision, HistoryRevision
from codexbar.domain.errors import UsageSourceUnavailableError
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.domain.reset import ResetCreditReadResult

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
WINDOW = UsageWindowId("window-720m")


def usage(*, remaining: str = "0.50", freshness: Freshness = Freshness.CURRENT) -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                id=WINDOW,
                label="Dynamic",
                remaining=Fraction(Decimal(remaining)),
                resets_at=NOW + timedelta(hours=8),
            ),
        ),
        observed_at=NOW,
        source=UsageSource.MOCK,
        freshness=freshness,
    )


def observation(*, remaining: str = "0.50") -> AccountRateLimitsObservation:
    return AccountRateLimitsObservation(
        usage=usage(remaining=remaining),
        reset_credits=ResetCreditReadResult.unavailable("not relevant"),
    )


class SequenceReader:
    def __init__(self) -> None:
        self._calls = 0

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        self._calls += 1
        if self._calls == 1:
            return observation()
        if self._calls == 2:
            raise UsageSourceUnavailableError("offline")
        return observation(remaining="0.40")


class RevisionRepo:
    def __init__(self) -> None:
        self.pruned_count = 0
        self.snapshot_count = 0
        self.append_error: Exception | None = None
        self._snapshots: set[HistoricalSnapshot] = set()

    def append(self, snapshot: HistoricalSnapshot) -> bool:
        if self.append_error is not None:
            raise self.append_error
        previous_count = len(self._snapshots)
        self._snapshots.add(snapshot)
        self.snapshot_count = len(self._snapshots)
        return self.snapshot_count > previous_count

    def query(self, interval: HistoryInterval) -> tuple[HistoricalSnapshot, ...]:
        return ()

    def query_window(self, window_id, interval):
        return ()

    def prune(self, cutoff: datetime) -> int:
        result = self.pruned_count
        self.pruned_count = 0
        return result

    def inspect(self) -> HistoryInspection:
        return HistoryInspection(
            path="/tmp/history.sqlite3",
            state=(
                HistoryState.READY_EMPTY
                if self.snapshot_count == 0
                else HistoryState.READY_NON_EMPTY
            ),
            schema_version=1,
            snapshot_count=self.snapshot_count,
        )

    def clear(self) -> int:
        removed = len(self._snapshots)
        self._snapshots.clear()
        self.snapshot_count = 0
        return removed


def test_task_730_current_revision_advances_only_for_authoritative_adoption() -> None:
    reader = LatestAccountObservationReader(SequenceReader())

    assert reader.current_revision == CurrentRevision(0)
    reader.read_account_rate_limits()
    assert reader.current_revision == CurrentRevision(1)

    with pytest.raises(UsageSourceUnavailableError):
        reader.read_account_rate_limits()

    assert reader.current_revision == CurrentRevision(1)
    assert reader.latest is not None
    assert reader.latest.usage.freshness is Freshness.STALE

    reader.read_account_rate_limits()
    assert reader.current_revision == CurrentRevision(2)


def test_task_731_732_history_revision_tracks_effective_runtime_mutations() -> None:
    repo = RevisionRepo()
    service = HistoryService(repo, clock=lambda: NOW)

    assert service.revision == HistoryRevision(0)
    service.process(usage(freshness=Freshness.STALE))
    assert service.revision == HistoryRevision(0)

    service.process(usage())
    assert service.revision == HistoryRevision(1)

    # The same immutable snapshot is a zero-effect append and must not invalidate
    # revision-aware Context cache entries.
    service.process(usage())
    assert service.revision == HistoryRevision(1)

    repo.pruned_count = 2
    service.process(usage(remaining="0.40"))
    assert service.revision == HistoryRevision(3)


def test_task_732_history_clear_advances_only_when_rows_exist() -> None:
    repo = RevisionRepo()
    service = HistoryService(repo, clock=lambda: NOW)

    assert service.clear() == 0
    assert service.revision == HistoryRevision(0)

    service.process(usage())
    assert service.revision == HistoryRevision(1)
    assert service.clear() == 1
    assert service.revision == HistoryRevision(2)


def test_revision_types_reject_negative_values() -> None:
    with pytest.raises(ValueError):
        CurrentRevision(-1)
    with pytest.raises(ValueError):
        HistoryRevision(-1)
