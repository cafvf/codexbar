from __future__ import annotations

from typing import Protocol

from codexbar.application.notifications import NotificationMessage
from codexbar.domain.models import UsageSnapshot


class UsageProvider(Protocol):
    def get_usage(self) -> UsageSnapshot: ...


class NotificationPort(Protocol):
    def notify(self, message: NotificationMessage) -> None: ...
