from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from codexbar.application.history import HistoryError, HistoryInterval
from codexbar.application.history_policy import HISTORY_RETENTION
from codexbar.application.revisions import CurrentRevision, HistoryRevision
from codexbar.domain.context import (
    ContextCoverage,
    ContextEmpiricalSummary,
    ContextObservation,
    ContextSelectionState,
    select_context_references,
    summarize_context_reference_set,
)
from codexbar.domain.models import Freshness, UsageSnapshot, UsageWindowId


class ContextHistoryRepository(Protocol):
    """Read-only application port for historical Context candidates."""

    def query_candidates(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[ContextObservation, ...]: ...


class FailedContextHistoryRepository:
    """Read port preserving an already-normalized history failure."""

    def __init__(self, error: HistoryError) -> None:
        self._error = error

    def query_candidates(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[ContextObservation, ...]:
        raise self._error


class HistoricalContextState(StrEnum):
    UNAVAILABLE = "unavailable"
    INSUFFICIENT = "insufficient"
    SUFFICIENT = "sufficient"


class HistoricalContextReason(StrEnum):
    CURRENT_WINDOW_MISSING = "current_window_missing"
    CURRENT_NOT_CURRENT = "current_not_current"
    CURRENT_RESET_MISSING = "current_reset_missing"
    CURRENT_RESET_INVALID = "current_reset_invalid"
    NO_HISTORICAL_OBSERVATIONS = "no_historical_observations"
    NO_IDENTIFIABLE_CYCLES = "no_identifiable_cycles"
    NO_COMPARABLE_CYCLES = "no_comparable_cycles"
    TOO_FEW_COMPARABLE_CYCLES = "too_few_comparable_cycles"
    HISTORY_UNAVAILABLE = "history_unavailable"


@dataclass(frozen=True, slots=True)
class HistoricalContextResult:
    """Failure-isolated application result for one current usage window."""

    window_id: UsageWindowId
    state: HistoricalContextState
    reason: HistoricalContextReason | None = None
    summary: ContextEmpiricalSummary | None = None
    comparable_cycle_count: int | None = None
    diagnostic: str | None = None

    def __post_init__(self) -> None:
        if self.comparable_cycle_count is not None and self.comparable_cycle_count < 0:
            raise ValueError("comparable cycle count must not be negative")

        if self.state is HistoricalContextState.SUFFICIENT:
            if self.summary is None or self.reason is not None:
                raise ValueError("sufficient context requires summary and no absence reason")
        elif self.summary is not None or self.reason is None:
            raise ValueError("non-sufficient context requires an absence reason and no summary")
        if (
            self.summary is not None
            and self.comparable_cycle_count is not None
            and self.summary.cycle_count != self.comparable_cycle_count
        ):
            raise ValueError("summary cycle count must match comparable cycle count")


@dataclass(frozen=True, slots=True)
class ContextCacheKey:
    current_revision: CurrentRevision
    history_revision: HistoryRevision
    window_id: UsageWindowId


@dataclass(frozen=True, slots=True)
class ContextCacheStats:
    hits: int
    misses: int
    entries: int


class HistoricalContextService:
    """Compose an already-observed Current snapshot with bounded local history."""

    def __init__(self, repository: ContextHistoryRepository) -> None:
        self._repository = repository
        self._cache: dict[ContextCacheKey, HistoricalContextResult] = {}
        self._active_revision_pair: tuple[CurrentRevision, HistoryRevision] | None = None
        self._cache_hits = 0
        self._cache_misses = 0

    @property
    def cache_stats(self) -> ContextCacheStats:
        return ContextCacheStats(
            hits=self._cache_hits,
            misses=self._cache_misses,
            entries=len(self._cache),
        )

    def clear_cache(self, *, reset_metrics: bool = False) -> None:
        self._cache.clear()
        self._active_revision_pair = None
        if reset_metrics:
            self._cache_hits = 0
            self._cache_misses = 0

    def evaluate(
        self,
        *,
        current: UsageSnapshot,
        window_id: UsageWindowId,
        current_revision: CurrentRevision | None = None,
        history_revision: HistoryRevision | None = None,
    ) -> HistoricalContextResult:
        if (current_revision is None) != (history_revision is None):
            raise ValueError("Current and History revisions must be supplied together")

        # STALE is derived from an older authoritative observation and therefore does
        # not receive a new Current revision. It must bypass a cache entry produced
        # while that same revision was CURRENT.
        if current.freshness is not Freshness.CURRENT:
            return self._evaluate_uncached(current=current, window_id=window_id)

        if current_revision is None or history_revision is None:
            return self._evaluate_uncached(current=current, window_id=window_id)

        pair = (current_revision, history_revision)
        if pair != self._active_revision_pair:
            self._cache.clear()
            self._active_revision_pair = pair

        key = ContextCacheKey(
            current_revision=current_revision,
            history_revision=history_revision,
            window_id=window_id,
        )
        cached = self._cache.get(key)
        if cached is not None:
            self._cache_hits += 1
            return cached

        self._cache_misses += 1
        result = self._evaluate_uncached(current=current, window_id=window_id)
        if result.reason is not HistoricalContextReason.HISTORY_UNAVAILABLE:
            self._cache[key] = result
        return result

    def _evaluate_uncached(
        self,
        *,
        current: UsageSnapshot,
        window_id: UsageWindowId,
    ) -> HistoricalContextResult:
        if current.freshness is not Freshness.CURRENT:
            return self._unavailable(
                window_id,
                HistoricalContextReason.CURRENT_NOT_CURRENT,
                comparable_cycle_count=None,
            )

        window = next((item for item in current.windows if item.id == window_id), None)
        if window is None:
            return self._unavailable(
                window_id,
                HistoricalContextReason.CURRENT_WINDOW_MISSING,
                comparable_cycle_count=None,
            )

        current_observation = ContextObservation(
            window_id=window.id,
            observed_at=current.observed_at,
            remaining=window.remaining,
            resets_at=window.resets_at,
        )

        if window.resets_at is None:
            return self._unavailable(
                window_id,
                HistoricalContextReason.CURRENT_RESET_MISSING,
                comparable_cycle_count=None,
            )
        if window.resets_at < current.observed_at:
            return self._unavailable(
                window_id,
                HistoricalContextReason.CURRENT_RESET_INVALID,
                comparable_cycle_count=None,
            )

        interval = HistoryInterval(
            current.observed_at - HISTORY_RETENTION,
            current.observed_at,
        )
        try:
            historical = self._repository.query_candidates(window_id, interval)
        except HistoryError as exc:
            return HistoricalContextResult(
                window_id=window_id,
                state=HistoricalContextState.UNAVAILABLE,
                reason=HistoricalContextReason.HISTORY_UNAVAILABLE,
                comparable_cycle_count=None,
                diagnostic=str(exc),
            )

        selection = select_context_references(
            current=current_observation,
            historical=historical,
        )
        if selection.state is not ContextSelectionState.READY:
            return self._from_selection_absence(window_id, selection.state)

        reference_set = selection.reference_set
        if reference_set is None:
            raise AssertionError("READY context selection must contain a reference set")

        summary = summarize_context_reference_set(
            current_remaining=window.remaining,
            reference_set=reference_set,
        )
        if summary.coverage is ContextCoverage.INSUFFICIENT:
            return HistoricalContextResult(
                window_id=window_id,
                state=HistoricalContextState.INSUFFICIENT,
                reason=HistoricalContextReason.TOO_FEW_COMPARABLE_CYCLES,
                comparable_cycle_count=summary.cycle_count,
            )

        return HistoricalContextResult(
            window_id=window_id,
            state=HistoricalContextState.SUFFICIENT,
            summary=summary,
            comparable_cycle_count=summary.cycle_count,
        )

    @staticmethod
    def _unavailable(
        window_id: UsageWindowId,
        reason: HistoricalContextReason,
        *,
        comparable_cycle_count: int | None,
    ) -> HistoricalContextResult:
        return HistoricalContextResult(
            window_id=window_id,
            state=HistoricalContextState.UNAVAILABLE,
            reason=reason,
            comparable_cycle_count=comparable_cycle_count,
        )

    @classmethod
    def _from_selection_absence(
        cls,
        window_id: UsageWindowId,
        state: ContextSelectionState,
    ) -> HistoricalContextResult:
        reasons = {
            ContextSelectionState.CURRENT_RESET_MISSING:
                HistoricalContextReason.CURRENT_RESET_MISSING,
            ContextSelectionState.CURRENT_RESET_INVALID:
                HistoricalContextReason.CURRENT_RESET_INVALID,
            ContextSelectionState.NO_HISTORICAL_OBSERVATIONS:
                HistoricalContextReason.NO_HISTORICAL_OBSERVATIONS,
            ContextSelectionState.NO_IDENTIFIABLE_CYCLES:
                HistoricalContextReason.NO_IDENTIFIABLE_CYCLES,
            ContextSelectionState.NO_COMPARABLE_CYCLES:
                HistoricalContextReason.NO_COMPARABLE_CYCLES,
        }
        reason = reasons.get(state)
        if reason is None:
            raise ValueError(f"unsupported context selection state: {state}")
        count = (
            None
            if state in {
                ContextSelectionState.CURRENT_RESET_MISSING,
                ContextSelectionState.CURRENT_RESET_INVALID,
            }
            else 0
        )
        return cls._unavailable(
            window_id,
            reason,
            comparable_cycle_count=count,
        )
