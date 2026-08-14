from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.context import (
    HistoricalContextReason,
    HistoricalContextResult,
    HistoricalContextService,
    HistoricalContextState,
)
from codexbar.application.revisions import CurrentRevision, HistoryRevision
from codexbar.domain.context import ContextCoverage, ContextRank
from codexbar.domain.models import UsageWindowId


class ContextViewKind(StrEnum):
    UNAVAILABLE = "unavailable"
    INSUFFICIENT = "insufficient"
    SPARSE = "sparse"
    LIMITED = "limited"
    ESTABLISHED = "established"


@dataclass(frozen=True, slots=True)
class ContextWindowViewState:
    window_id: UsageWindowId
    label: str
    kind: ContextViewKind
    comparable_cycle_count: int | None
    status_text: str
    median: Decimal | None = None
    range_low: Decimal | None = None
    range_high: Decimal | None = None
    band_low: Decimal | None = None
    band_high: Decimal | None = None
    rank_text: str | None = None


@dataclass(frozen=True, slots=True)
class ContextViewState:
    windows: tuple[ContextWindowViewState, ...]


@dataclass(frozen=True, slots=True)
class ContextPresentationRequest:
    observation: AccountRateLimitsObservation
    current_revision: CurrentRevision
    history_revision: HistoryRevision

    @property
    def identity(self) -> tuple[CurrentRevision, HistoryRevision]:
        return self.current_revision, self.history_revision


class ContextPresenter:
    """Present Context from a coherently captured Current/History revision pair."""

    def __init__(
        self,
        latest_reader: LatestAccountObservationReader,
        service: HistoricalContextService,
        *,
        history_revision_reader: Callable[[], HistoryRevision] | None = None,
    ) -> None:
        self._latest_reader = latest_reader
        self._service = service
        self._history_revision_reader = history_revision_reader

    def current(self) -> ContextViewState:
        """Compatibility path for v1.6/unit callers; production Qt uses ContextController."""
        request = self.capture_request()
        if request is None:
            return ContextViewState(())
        return self.evaluate_request(request)

    def capture_request(self) -> ContextPresentationRequest | None:
        observation, current_revision = self._latest_reader.capture()
        if observation is None:
            return None
        revision_reader = self._history_revision_reader
        history_revision = revision_reader() if revision_reader is not None else HistoryRevision()
        return ContextPresentationRequest(
            observation=observation,
            current_revision=current_revision,
            history_revision=history_revision,
        )

    def current_identity(self) -> tuple[CurrentRevision, HistoryRevision] | None:
        request = self.capture_request()
        return None if request is None else request.identity

    def evaluate_request(self, request: ContextPresentationRequest) -> ContextViewState:
        observation = request.observation
        revision_reader = self._history_revision_reader
        return ContextViewState(
            tuple(
                self._window_state(
                    label=window.label,
                    result=(
                        self._service.evaluate(
                            current=observation.usage,
                            window_id=window.id,
                        )
                        if revision_reader is None
                        else self._service.evaluate(
                            current=observation.usage,
                            window_id=window.id,
                            current_revision=request.current_revision,
                            history_revision=request.history_revision,
                        )
                    ),
                )
                for window in observation.usage.windows
            )
        )

    @staticmethod
    def _window_state(
        *,
        label: str,
        result: HistoricalContextResult,
    ) -> ContextWindowViewState:
        count = result.comparable_cycle_count
        if result.state is HistoricalContextState.UNAVAILABLE:
            return ContextWindowViewState(
                window_id=result.window_id,
                label=label,
                kind=ContextViewKind.UNAVAILABLE,
                comparable_cycle_count=count,
                status_text=_reason_text(result.reason),
            )

        if result.state is HistoricalContextState.INSUFFICIENT:
            return ContextWindowViewState(
                window_id=result.window_id,
                label=label,
                kind=ContextViewKind.INSUFFICIENT,
                comparable_cycle_count=count,
                status_text=(
                    "Insufficient independent historical cycles for a "
                    "distributional summary."
                ),
            )

        summary = result.summary
        if summary is None:
            raise AssertionError("sufficient Context result must include a summary")

        kind = {
            ContextCoverage.SPARSE: ContextViewKind.SPARSE,
            ContextCoverage.LIMITED: ContextViewKind.LIMITED,
            ContextCoverage.ESTABLISHED: ContextViewKind.ESTABLISHED,
        }.get(summary.coverage)
        if kind is None:
            raise AssertionError(
                "insufficient coverage must not reach sufficient presentation"
            )

        return ContextWindowViewState(
            window_id=result.window_id,
            label=label,
            kind=kind,
            comparable_cycle_count=count,
            status_text=_coverage_text(summary.coverage),
            median=summary.median,
            range_low=summary.observed_min,
            range_high=summary.observed_max,
            band_low=summary.q25,
            band_high=summary.q75,
            rank_text=_rank_text(summary.rank),
        )


def _reason_text(reason: HistoricalContextReason | None) -> str:
    return {
        HistoricalContextReason.CURRENT_WINDOW_MISSING:
            "Current window is unavailable.",
        HistoricalContextReason.CURRENT_NOT_CURRENT:
            "Current usage is stale; historical comparison is withheld.",
        HistoricalContextReason.CURRENT_RESET_MISSING:
            "Current reset timestamp is unavailable; historical comparison is not inferred.",
        HistoricalContextReason.CURRENT_RESET_INVALID:
            "Current reset timestamp is not valid for historical comparison.",
        HistoricalContextReason.NO_HISTORICAL_OBSERVATIONS:
            "No retained historical observations are available.",
        HistoricalContextReason.NO_IDENTIFIABLE_CYCLES:
            "History exists, but no authoritative historical cycles can be identified.",
        HistoricalContextReason.NO_COMPARABLE_CYCLES:
            "Historical cycles exist, but none are close enough to the current time-to-reset.",
        HistoricalContextReason.HISTORY_UNAVAILABLE:
            "Historical context is temporarily unavailable.",
        HistoricalContextReason.TOO_FEW_COMPARABLE_CYCLES:
            "Insufficient independent historical cycles.",
        None:
            "Historical context is unavailable.",
    }[reason]


def _coverage_text(coverage: ContextCoverage) -> str:
    return {
        ContextCoverage.SPARSE: "Sparse empirical coverage.",
        ContextCoverage.LIMITED: "Limited empirical coverage.",
        ContextCoverage.ESTABLISHED: "Established empirical coverage.",
        ContextCoverage.INSUFFICIENT: "Insufficient empirical coverage.",
    }[coverage]


def _rank_text(rank: ContextRank | None) -> str | None:
    if rank is None:
        return None
    return f"Historical comparison: {rank.describe()}."
