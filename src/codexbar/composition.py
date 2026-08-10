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
from codexbar.application.reset_ledger_service import ResetLedgerService
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
from codexbar.infrastructure.reset_event_paths import reset_ledger_database_path
from codexbar.infrastructure.reset_event_sqlite import SqliteResetEventRepository
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
    reset_ledger_service: ResetLedgerService | None = None

    def close(self) -> None:
        self.history_controller.close()
        if self.operation_coordinator is not None:
            self.operation_coordinator.close()


def build_usage_provider(*, mock: bool = False) -> UsageProvider:
    if mock:
        return MockUsageProvider()
    return AccountUsageProvider(CodexAccountRateLimitsReader())


def build_gui_runtime(*, mock: bool = False) -> GuiRuntime:
    history_path = history_database_path()
    history_repository = SqliteHistoryRepository(history_path)
    history_service = HistoryService(history_repository)
    history_controller = HistoryController(
        HistoricalAnalysisService(open_history_analytics_repository(history_path))
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

    reset_repository = SqliteResetEventRepository(reset_ledger_database_path())
    reset_ledger_service = ResetLedgerService(reset_repository)
    coordinator = AccountOperationCoordinator()
    reader: AccountRateLimitsReader = CodexAccountRateLimitsReader()
    reader = CapturingAccountRateLimitsReader(
        reader,
        history_service,
        reset_ledger_service,
    )
    reader = CoordinatedAccountRateLimitsReader(reader, coordinator)

    return GuiRuntime(
        provider=AccountUsageProvider(reader),
        settings_repository=settings_repository,
        notifier=notifier,
        history_controller=history_controller,
        account_controller=CurrentAccountController(reader),
        operation_coordinator=coordinator,
        reset_ledger_service=reset_ledger_service,
    )
