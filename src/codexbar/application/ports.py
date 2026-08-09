from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from codexbar.domain.models import UsageSnapshot

if TYPE_CHECKING:
    from codexbar.application.alerts import AlertEvent


class UsageProvider(Protocol):
    def get_usage(self) -> UsageSnapshot: ...


class NotificationPort(Protocol):
    def notify(self, event: AlertEvent) -> None: ...
