from __future__ import annotations

from dataclasses import dataclass

from codexbar.application.reset_derivation import derive_inventory_events
from codexbar.application.reset_ledger import ResetEventRepository, ResetLedgerError
from codexbar.application.reset_projection import ResetLedgerProjection, fold_reset_events
from codexbar.domain.reset import ResetCreditReadResult, ResetCreditReadStatus


@dataclass(frozen=True, slots=True)
class ResetLedgerProcessResult:
    appended_count: int
    projection: ResetLedgerProjection
    diagnostic: ResetLedgerError | None = None


class ResetLedgerService:
    """Failure-isolated derivation and persistence for reset-current observations."""

    def __init__(self, repository: ResetEventRepository) -> None:
        self._repository = repository
        self._last_result = ResetLedgerProcessResult(0, ResetLedgerProjection())

    @property
    def last_result(self) -> ResetLedgerProcessResult:
        return self._last_result

    def projection(self) -> ResetLedgerProjection:
        return fold_reset_events(self._repository.query_all())

    def process(self, result: ResetCreditReadResult) -> ResetLedgerProcessResult:
        if result.status is not ResetCreditReadStatus.CURRENT or result.inventory is None:
            try:
                projection = self.projection()
            except ResetLedgerError as exc:
                self._last_result = ResetLedgerProcessResult(
                    0,
                    ResetLedgerProjection(),
                    diagnostic=exc,
                )
                return self._last_result
            self._last_result = ResetLedgerProcessResult(0, projection)
            return self._last_result

        try:
            projection = self.projection()
            events = derive_inventory_events(projection, result.inventory)
            appended = self._repository.append_many(events)
            updated = fold_reset_events(self._repository.query_all())
        except ResetLedgerError as exc:
            self._last_result = ResetLedgerProcessResult(
                0,
                projection if "projection" in locals() else ResetLedgerProjection(),
                diagnostic=exc,
            )
            return self._last_result

        self._last_result = ResetLedgerProcessResult(appended, updated)
        return self._last_result
