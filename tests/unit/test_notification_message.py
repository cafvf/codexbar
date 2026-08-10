import pytest

from codexbar.application.notifications import NotificationMessage, NotificationUrgency


def test_notification_message_is_transport_neutral() -> None:
    message = NotificationMessage("Summary", "Body", NotificationUrgency.CRITICAL)

    assert message.summary == "Summary"
    assert message.body == "Body"
    assert message.urgency.value == "critical"


@pytest.mark.parametrize("summary, body", [("", "body"), ("summary", "")])
def test_notification_message_rejects_blank_text(summary, body) -> None:
    with pytest.raises(ValueError):
        NotificationMessage(summary, body)
