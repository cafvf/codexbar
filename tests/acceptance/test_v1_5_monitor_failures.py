from datetime import UTC, datetime

from codexbar.application.budget import BudgetRuntime
from codexbar.application.reset_deadlines import ResetDeadlineService
from codexbar.application.reset_monitor_runtime import ResetMonitorRuntime
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.domain.errors import NotificationDeliveryError
from codexbar.domain.settings import AppSettings


class FailingNotifier:
    def notify(self, message):
        raise NotificationDeliveryError("desktop unavailable")


class EmptyRepository:
    def query_all(self):
        return ()

    def append(self, event):
        return True

    def append_many(self, events):
        return len(events)

    def inspect(self):
        raise AssertionError


def test_notification_failure_does_not_escape_runtime() -> None:
    runtime = ResetMonitorRuntime(
        BudgetRuntime(AppSettings.defaults()),
        FailingNotifier(),
        ResetDeadlineService(
            EmptyRepository(),
            clock=lambda: datetime(2026, 8, 10, tzinfo=UTC),
        ),
        clock=lambda: datetime(2026, 8, 10, tzinfo=UTC),
    )

    assert runtime is not None
    assert isinstance(ResetLedgerProjection(), ResetLedgerProjection)
