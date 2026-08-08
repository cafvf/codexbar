import pytest

from codexbar.ui.controller import TraySettings


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"refresh_interval_seconds": 0}, "refresh_interval_seconds"),
        ({"poll_interval_milliseconds": 0}, "poll_interval_milliseconds"),
    ],
)
def test_tray_settings_require_positive_intervals(kwargs: dict[str, int], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        TraySettings(**kwargs)
