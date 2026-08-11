from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.context import (
    HistoricalContextReason,
    HistoricalContextResult,
    HistoricalContextService,
    HistoricalContextState,
)
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


class ContextPresenter:
    """Present Context from the already-captured latest account observation."""

    def __init__(
        self,
        latest_reader: LatestAccountObservationReader,
        service: HistoricalContextService,
    ) -> None:
        self._latest_reader = latest_reader
        self._service = service

    def current(self) -> ContextViewState:
        observation = self._latest_reader.latest
        if observation is None:
            return ContextViewState(())

        return ContextViewState(
            tuple(
                self._window_state(
                    label=window.label,
                    result=self._service.evaluate(
                        current=observation.usage,
                        window_id=window.id,
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
