from codexbar.__main__ import main


def test_cli_mock_smoke(capsys) -> None:
    assert main(["--mock"]) == 0
    output = capsys.readouterr().out
    assert "CodexBar" in output
    assert "Weekly: 81% left" in output


def test_cli_desktop_status_uses_desktop_command(monkeypatch, capsys) -> None:
    from codexbar.desktop import DesktopStatus

    monkeypatch.setattr(
        "codexbar.desktop.desktop_status",
        lambda: DesktopStatus(True, True, True, False),
    )
    assert main(["desktop", "status"]) == 0
    output = capsys.readouterr().out
    assert "Installed: yes" in output
    assert "Autostart: disabled" in output
