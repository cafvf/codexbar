from __future__ import annotations

from dataclasses import dataclass

from codexbar.application.account import AccountRateLimitsReader
from codexbar.application.account_operations import (
    AccountOperationCoordinator,
    CoordinatedAccountRateLimitsReader,
)
from codexbar.application.account_runtime import CapturingAccountRateLimitsReader
from codexbar.application.analytics import HistoricalAnalysisService
from codexbar.application.current_account import CurrentAccountController
from codexbar.application.history_runtime import HistoryCapturingUsageProvider, HistoryService
from codexbar.application.ports import NotificationPort, UsageProvider
from codexbar.application.settings import SettingsRepository
from codexbar.application.usage_adapter import AccountUsageProvider
from codexbar.infrastructure.account_reader import CodexAccountRateLimitsReader
from codexbar.infrastructure.history_paths import history_database_path
from codexbar.infrastructure.history_sqlite import (
    SqliteHistoryRepository,
    open_history_analytics_repository,
)
from codexbar.infrastructure.mock_provider import MockUsageProvider
from codexbar.infrastructure.notifications import NotifySendNotificationAdapter
from codexbar.infrastructure.settings import JsonSettingsRepository
from codexbar.ui.history_controller import HistoryController


@dataclass(slots=True)
class GuiRuntime:
    provider: UsageProvider
    settings_repository: SettingsRepository
    notifier: NotificationPort
    history_controller: HistoryController
    account_controller: CurrentAccountController | None = None
    operation_coordinator: AccountOperationCoordinator | None = None

    def close(self) -> None:
        self.history_controller.close()
        if self.operation_coordinator is not None:
            self.operation_coordinator.close()


def build_usage_provider(*, mock: bool = False) -> UsageProvider:
    """Build the one-shot compatibility provider without importing GUI frameworks."""
    if mock:
        return MockUsageProvider()
    return AccountUsageProvider(CodexAccountRateLimitsReader())


def build_gui_runtime(*, mock: bool = False) -> GuiRuntime:
    """Build v1.5 GUI runtime dependencies while preserving the v1.4 UI contract."""
    path = history_database_path()
    history_repository = SqliteHistoryRepository(path)
    history_service = HistoryService(history_repository)
    history_controller = HistoryController(
        HistoricalAnalysisService(open_history_analytics_repository(path))
    )
    settings_repository = JsonSettingsRepository()
    notifier = NotifySendNotificationAdapter()

    if mock:
        provider: UsageProvider = HistoryCapturingUsageProvider(
            MockUsageProvider(),
            history_service,
        )
        return GuiRuntime(
            provider=provider,
            settings_repository=settings_repository,
            notifier=notifier,
            history_controller=history_controller,
        )

    coordinator = AccountOperationCoordinator()
    reader: AccountRateLimitsReader = CodexAccountRateLimitsReader()
    reader = CapturingAccountRateLimitsReader(reader, history_service)
    reader = CoordinatedAccountRateLimitsReader(reader, coordinator)

    return GuiRuntime(
        provider=AccountUsageProvider(reader),
        settings_repository=settings_repository,
        notifier=notifier,
        history_controller=history_controller,
        account_controller=CurrentAccountController(reader),
        operation_coordinator=coordinator,
    )
