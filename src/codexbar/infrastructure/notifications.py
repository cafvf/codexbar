from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from codexbar.application.notifications import NotificationMessage
from codexbar.domain.errors import NotificationDeliveryError

_NOTIFY_SEND = "notify-send"
_COMMAND_TIMEOUT_SECONDS = 5.0


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


CommandRunner = Callable[[Sequence[str]], CommandResult]


def _default_runner(command: Sequence[str]) -> CommandResult:
    try:
        completed = subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            text=True,
            timeout=_COMMAND_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise NotificationDeliveryError(
            "notify-send is unavailable; install the libnotify-bin package"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise NotificationDeliveryError("notify-send timed out") from exc
    except OSError as exc:
        raise NotificationDeliveryError(f"cannot execute notify-send: {exc}") from exc

    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


class NotifySendNotificationAdapter:
    def __init__(
        self,
        runner: CommandRunner = _default_runner,
        *,
        executable: str = _NOTIFY_SEND,
    ) -> None:
        self._runner = runner
        self._executable = executable

    def notify(self, message: NotificationMessage) -> None:
        result = self._runner(self.command(message))
        if result.returncode != 0:
            detail = (
                result.stderr.strip()
                or result.stdout.strip()
                or "unknown notify-send failure"
            )
            raise NotificationDeliveryError(
                f"desktop notification delivery failed: {detail}"
            )

    def command(self, message: NotificationMessage) -> tuple[str, ...]:
        return (
            self._executable,
            "--app-name=CodexBar",
            f"--urgency={message.urgency.value}",
            message.summary,
            message.body,
        )


def notify_send_available() -> bool:
    return shutil.which(_NOTIFY_SEND) is not None
