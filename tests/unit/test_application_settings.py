from dataclasses import dataclass

from codexbar.application.settings import (
    GetSettings,
    ResetSettings,
    SaveSettings,
    SettingsLoadResult,
    SettingsOrigin,
)
from codexbar.domain.settings import AppSettings


@dataclass
class FakeRepository:
    result: SettingsLoadResult
    saved: AppSettings | None = None
    resets: int = 0

    def load(self) -> SettingsLoadResult:
        return self.result

    def save(self, settings: AppSettings) -> None:
        self.saved = settings

    def reset(self) -> None:
        self.resets += 1


def test_get_settings_returns_repository_result_without_boundary_knowledge() -> None:
    result = SettingsLoadResult(AppSettings.defaults(), SettingsOrigin.DEFAULTS)
    repository = FakeRepository(result)

    assert GetSettings(repository).execute() is result


def test_save_settings_delegates_complete_domain_object() -> None:
    settings = AppSettings.defaults()
    repository = FakeRepository(SettingsLoadResult(settings, SettingsOrigin.DEFAULTS))

    SaveSettings(repository).execute(settings)

    assert repository.saved is settings


def test_reset_settings_delegates_to_repository() -> None:
    settings = AppSettings.defaults()
    repository = FakeRepository(SettingsLoadResult(settings, SettingsOrigin.DEFAULTS))

    ResetSettings(repository).execute()
    ResetSettings(repository).execute()

    assert repository.resets == 2
