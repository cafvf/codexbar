import json

from codexbar.__main__ import main


def test_settings_show_reports_schema_and_reserves_deterministically(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    path = tmp_path / ".config/codexbar/settings.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "low_remaining_threshold": "0.20",
                "refresh_interval_seconds": 60,
                "notifications_enabled": True,
                "usage_reserves": {
                    "window_300m": "0.10",
                    "window_10080m": "0.15",
                },
            }
        )
    )

    assert main(["settings", "show"]) == 0
    output = capsys.readouterr().out

    assert "Origin: persisted" in output
    assert "Settings schema source: 2" in output
    assert output.index("window_10080m") < output.index("window_300m")


def test_settings_reset_still_removes_schema_2_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    path = tmp_path / ".config/codexbar/settings.json"
    path.parent.mkdir(parents=True)
    path.write_text("{}")

    assert main(["settings", "reset"]) == 0
    assert not path.exists()
