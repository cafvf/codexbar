from codexbar.application.settings import SettingsLoadResult, SettingsOrigin
from codexbar.domain.settings import AppSettings
from codexbar.ui import launcher


class FakeRepository:
    def load(self) -> SettingsLoadResult:
        return SettingsLoadResult(AppSettings.defaults(), SettingsOrigin.DEFAULTS)

    def save(self, settings: AppSettings) -> None:
        raise AssertionError("save must not be called during startup")

    def reset(self) -> None:
        raise AssertionError("reset must not be called during startup")


def test_gui_startup_loads_effective_app_settings_before_entering_qt(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_qt_tray(provider, settings, repository):
        captured["provider"] = provider
        captured["settings"] = settings
        captured["repository"] = repository
        return 0

    monkeypatch.setattr(launcher, "_load_qt_tray", lambda: fake_qt_tray)

    provider = object()
    repository = FakeRepository()
    result = launcher.run_tray(provider, repository=repository)

    assert result == 0
    assert captured["provider"] is provider
    assert captured["settings"] == AppSettings.defaults()
    assert captured["repository"] is repository
