from codexbar.application.notifications import NotificationUrgency
from codexbar.application.reset_monitor import (
    OpportunityPriority,
    ResetAdvice,
    ResetFact,
    ResetFactKind,
)
from codexbar.application.reset_notifications import (
    reset_advice_message,
    reset_fact_message,
)


def test_fact_and_advice_wording_are_distinct() -> None:
    fact = reset_fact_message(
        ResetFact(ResetFactKind.EXPIRY_1H, "A:1h", "Credit expires within 1h.")
    )
    advice = reset_advice_message(
        ResetAdvice(OpportunityPriority.HIGH, "Consider redeeming.")
    )

    assert "fact" in fact.summary.lower()
    assert "advice" in advice.summary.lower()
    assert fact.urgency is NotificationUrgency.CRITICAL
