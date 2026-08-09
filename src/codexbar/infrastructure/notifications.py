from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, cast

from PySide6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

from codexbar.application.alerts import AlertEvent
from codexbar.domain.errors import NotificationDeliveryError
from codexbar.domain.models import UsageWindowState

_SERVICE = "org.freedesktop.Notifications"
_PATH = "/org/freedesktop/Notifications"
_INTERFACE = "org.freedesktop.Notifications"


class _DbusInterface(Protocol):
    def isValid(self) -> bool: ...


InterfaceFactory = Callable[[], _DbusInterface]


def _default_interface() -> _DbusInterface:
    return cast(
        _DbusInterface,
        QDBusInterface(
            _SERVICE,
            _PATH,
            _INTERFACE,
            QDBusConnection.sessionBus(),
        ),
    )


def _call_notify(interface: _DbusInterface, *args: object) -> QDBusMessage:
    qt_interface = cast(Any, interface)
    return cast(QDBusMessage, qt_interface.call("Notify", *args))


class QtDbusNotificationAdapter:
    """Deliver normalized alerts through org.freedesktop.Notifications."""

    def __init__(self, interface_factory: InterfaceFactory = _default_interface) -> None:
        self._interface_factory = interface_factory

    def notify(self, event: AlertEvent) -> None:
        interface = self._interface_factory()
        if not interface.isValid():
            raise NotificationDeliveryError("desktop notification service is unavailable")

        summary = _summary(event.state)
        body = _body(event)
        reply = _call_notify(
            interface,
            "CodexBar",
            0,
            "",
            summary,
            body,
            [],
            {},
            -1,
        )
        if reply.type() is QDBusMessage.MessageType.ErrorMessage:
            detail = reply.errorMessage() or "unknown D-Bus notification error"
            raise NotificationDeliveryError(detail)


def _summary(state: UsageWindowState) -> str:
    if state is UsageWindowState.EXHAUSTED:
        return "CodexBar usage exhausted"
    return "CodexBar usage low"


def _body(event: AlertEvent) -> str:
    percent = format(event.remaining.percent.normalize(), "f")
    text = f"{event.label}: {percent}% remaining"
    if event.resets_at is not None:
        reset = event.resets_at.astimezone().strftime("%Y-%m-%d %H:%M %Z")
        return f"{text}. Resets {reset}."
    return text
