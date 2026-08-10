from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from datetime import UTC, datetime

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.budget import BudgetRuntime
from codexbar.application.notifications import NotificationMessage
from codexbar.application.ports import NotificationPort
from codexbar.application.reset_deadlines import ResetDeadlineService
from codexbar.application.reset_ledger import ResetLedgerError
from codexbar.application.reset_monitor import (
    ResetExpiryMonitor,
    ResetOpportunityPolicy,
    build_reset_situation,
)
from codexbar.application.reset_notifications import (
    reset_advice_message,
    reset_fact_message,
)
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.domain.errors import NotificationDeliveryError


class ResetMonitorRuntime:
    def __init__(
        self,
        budget_runtime: BudgetRuntime,
        notifier: NotificationPort,
        deadline_service: ResetDeadlineService,
        *,
        policy: ResetOpportunityPolicy | None = None,
        monitor: ResetExpiryMonitor | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._budget_runtime = budget_runtime
        self._notifier = notifier
        self._deadline_service = deadline_service
        self._policy = policy or ResetOpportunityPolicy()
        self._monitor = monitor or ResetExpiryMonitor()
        self._clock = clock or (lambda: datetime.now(UTC))

    def process(
        self,
        observation: AccountRateLimitsObservation,
        projection: ResetLedgerProjection,
    ) -> tuple[NotificationMessage, ...]:
        now = self._clock()
        situation = build_reset_situation(
            observation,
            self._budget_runtime,
            projection,
        )
        messages = [
            reset_fact_message(fact)
            for fact in self._monitor.evaluate(situation, now=now)
        ]
        advice = self._policy.assess(situation, now=now)
        if advice.priority.value != "none":
            messages.append(reset_advice_message(advice))

        with suppress(ResetLedgerError):
            self._deadline_service.record_passed_known_deadlines()

        for message in messages:
            try:
                self._notifier.notify(message)
            except NotificationDeliveryError:
                continue
        return tuple(messages)
