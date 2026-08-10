from __future__ import annotations

from codexbar.application.context import ContextHistoryRepository
from codexbar.application.history import HistoryInterval
from codexbar.domain.context import ContextObservation
from codexbar.domain.models import UsageWindowId
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository


class SqliteContextHistoryRepository(ContextHistoryRepository):
    """Schema-v1 adapter exposing historical samples as Context candidates."""

    def __init__(self, history_repository: SqliteHistoryRepository) -> None:
        self._history_repository = history_repository

    def query_candidates(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[ContextObservation, ...]:
        samples = self._history_repository.query_window(window_id, interval)
        return tuple(
            ContextObservation(
                window_id=sample.observation.window_id,
                observed_at=sample.observed_at,
                remaining=sample.observation.remaining,
                resets_at=sample.observation.resets_at,
            )
            for sample in samples
        )
