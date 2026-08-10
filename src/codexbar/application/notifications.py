from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class NotificationUrgency(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class NotificationMessage:
    summary: str
    body: str
    urgency: NotificationUrgency = NotificationUrgency.NORMAL

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError("notification summary must not be blank")
        if not self.body.strip():
            raise ValueError("notification body must not be blank")
