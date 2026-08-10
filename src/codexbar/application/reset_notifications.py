from __future__ import annotations

from codexbar.application.notifications import NotificationMessage, NotificationUrgency
from codexbar.application.reset_monitor import (
    OpportunityPriority,
    ResetAdvice,
    ResetFact,
    ResetFactKind,
)


def reset_fact_message(fact: ResetFact) -> NotificationMessage:
    urgency = (
        NotificationUrgency.CRITICAL
        if fact.kind is ResetFactKind.EXPIRY_1H
        else NotificationUrgency.NORMAL
    )
    return NotificationMessage(
        "CodexBar reset fact",
        fact.body,
        urgency,
    )


def reset_advice_message(advice: ResetAdvice) -> NotificationMessage:
    urgency = (
        NotificationUrgency.CRITICAL
        if advice.priority in {OpportunityPriority.URGENT, OpportunityPriority.HIGH}
        else NotificationUrgency.NORMAL
    )
    return NotificationMessage(
        "CodexBar reset advice",
        advice.reason,
        urgency,
    )
