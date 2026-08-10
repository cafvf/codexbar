from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from codexbar.application.reset_events import (
    DeadlinePassed,
    ResetEvent,
    ResetEventId,
    ResetEventProvenance,
    ResetEventType,
)
from codexbar.application.reset_ledger import ResetEventRepository
from codexbar.application.reset_projection import fold_reset_events
from codexbar.domain.reset import ExpiryKind


class ResetDeadlineService:
    def __init__(
        self,
        repository: ResetEventRepository,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(UTC))

    def record_passed_known_deadlines(self) -> int:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("deadline service clock must be timezone-aware")
        now = now.astimezone(UTC)

        projection = fold_reset_events(self._repository.query_all())
        signaled = {credit_id.value for credit_id in projection.signaled_deadlines}
        events = []

        for detail in projection.known_details:
            expiry = detail.expiry
            if (
                expiry.kind is ExpiryKind.EXPIRES_AT
                and expiry.instant is not None
                and expiry.instant <= now
                and detail.credit_id.value not in signaled
            ):
                events.append(
                    ResetEvent(
                        event_id=ResetEventId(str(uuid4())),
                        event_type=ResetEventType.DEADLINE_PASSED,
                        occurred_at=now,
                        provenance=ResetEventProvenance.SYSTEM,
                        payload=DeadlinePassed(detail.credit_id, expiry.instant),
                    )
                )

        return self._repository.append_many(tuple(events))
