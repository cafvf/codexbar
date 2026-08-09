from concurrent.futures import Future
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from codexbar.application.refresh import RefreshCoordinator
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.ui.controller import TrayController


class ImmediateExecutor:
    def submit(self, fn: Any, *args: Any, **kwargs: Any) -> Future[object]:
        future: Future[object] = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as exc:
            future.set_exception(exc)
        return future


class StaticProvider:
    def get_usage(self) -> UsageSnapshot:
        return UsageSnapshot(
            windows=(
                UsageWindow(
                    UsageWindowId("weekly"),
                    "Weekly",
                    Fraction(Decimal("0.18")),
                ),
            ),
            observed_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
            source=UsageSource.MOCK,
        )


def test_runtime_usage_policy_can_change_without_restarting_controller() -> None:
    controller = TrayController(
        RefreshCoordinator(GetCurrentUsage(StaticProvider())),
        executor=ImmediateExecutor(),
    )

    controller.start_refresh()
    first = controller.poll()
    assert first.usage is not None
    assert first.usage.windows[0].state.value == "low"

    from codexbar.domain.models import UsagePolicy

    controller.apply_usage_policy(
        UsagePolicy(low_remaining_threshold=Fraction(Decimal("0.15")))
    )
    controller.start_refresh()
    second = controller.poll()

    assert second.usage is not None
    assert second.usage.windows[0].state.value == "available"
