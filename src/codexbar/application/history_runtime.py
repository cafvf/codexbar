from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from codexbar.application.history import (
    HistoricalSnapshot,
    HistoryError,
    HistoryRepository,
)
from codexbar.application.history_policy import HISTORY_RETENTION
from codexbar.application.ports import UsageProvider
from codexbar.application.revisions import HistoryRevision
from codexbar.domain.models import Freshness, UsageSnapshot


@dataclass(frozen=True, slots=True)
class HistoryMaintenanceResult:
    captured: bool
    pruned_count: int = 0
    diagnostic: HistoryError | None = None


class HistoryService:
    """Failure-isolated runtime capture and maintenance for usage history."""

    def __init__(
        self,
        repository: HistoryRepository,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))
        self._last_result = HistoryMaintenanceResult(captured=False)
        self._revision = HistoryRevision()

    @property
    def last_result(self) -> HistoryMaintenanceResult:
        return self._last_result

    @property
    def revision(self) -> HistoryRevision:
        return self._revision

    def process(self, snapshot: UsageSnapshot) -> HistoryMaintenanceResult:
        if snapshot.freshness is not Freshness.CURRENT:
            self._last_result = HistoryMaintenanceResult(captured=False)
            return self._last_result

        historical = HistoricalSnapshot.from_usage_snapshot(snapshot)
        try:
            appended = self._repository.append(historical)
        except HistoryError as exc:
            self._last_result = HistoryMaintenanceResult(
                captured=False,
                diagnostic=exc,
            )
            return self._last_result

        if appended:
            self._advance_revision()

        try:
            pruned = self._repository.prune(self._cutoff())
        except HistoryError as exc:
            self._last_result = HistoryMaintenanceResult(
                captured=True,
                diagnostic=exc,
            )
            return self._last_result

        if pruned > 0:
            self._advance_revision()

        self._last_result = HistoryMaintenanceResult(
            captured=True,
            pruned_count=pruned,
        )
        return self._last_result

    def clear(self) -> int:
        """Clear History and advance the runtime revision only when rows existed."""
        removed = self._repository.clear()
        if removed > 0:
            self._advance_revision()
        return removed

    def _advance_revision(self) -> None:
        self._revision = self._revision.next()

    def _cutoff(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("history maintenance clock must be timezone-aware")
        return now.astimezone(UTC) - HISTORY_RETENTION


class HistoryCapturingUsageProvider:
    """Run history persistence in the same worker call as the real provider."""

    def __init__(
        self,
        provider: UsageProvider,
        history_service: HistoryService,
    ) -> None:
        self._provider = provider
        self._history_service = history_service

    def get_usage(self) -> UsageSnapshot:
        snapshot = self._provider.get_usage()
        self._history_service.process(snapshot)
        return snapshot
