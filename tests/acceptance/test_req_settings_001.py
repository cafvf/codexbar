from concurrent.futures import Future
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

from codexbar.application.refresh import RefreshCoordinator
from codexbar.application.use_cases import GetCurrentUsage
from codexbar.domain.models import (
    Fraction,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.ui.controller import TrayController
from codexbar.ui.viewmodel import UsageViewModel

OBSERVED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)


class ImmediateExecutor:
    def submit(self, fn: Any, *args: Any, **kwargs: Any) -> Future[object]:
        future: Future[object] = Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except BaseException as exc:  # test executor mirrors Future semantics
            future.set_exception(exc)
        return future


class StaticProvider:
    def __init__(self, value: UsageSnapshot) -> None:
        self._value = value

    def get_usage(self) -> UsageSnapshot:
        return self._value


class RecordingRefreshTimer:
    def __init__(self) -> None:
        self.intervals: list[int] = []

    def setInterval(self, milliseconds: int) -> None:
        self.intervals.append(milliseconds)


def _settings_modules():
    domain = import_module("codexbar.domain.settings")
    application = import_module("codexbar.application.settings")
    infrastructure = import_module("codexbar.infrastructure.settings")
    return domain, application, infrastructure


def test_ac_settings_001_fresh_install_uses_documented_defaults(tmp_path: Path) -> None:
    domain, application, infrastructure = _settings_modules()
    repository = infrastructure.JsonSettingsRepository(
        env={"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    )

    result = application.GetSettings(repository).execute()

    assert result.settings == domain.AppSettings.defaults()
    assert result.settings.low_remaining_threshold == Fraction(Decimal("0.20"))
    assert result.settings.refresh_interval_seconds.value == 60
    assert result.settings.notifications_enabled is True


def test_ac_settings_002_003_saved_values_survive_new_repository_instance(tmp_path: Path) -> None:
    domain, application, infrastructure = _settings_modules()
    env = {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    first = infrastructure.JsonSettingsRepository(env=env)
    settings = domain.AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.12")),
        refresh_interval_seconds=domain.RefreshIntervalSeconds(180),
        notifications_enabled=False,
    )

    application.SaveSettings(first).execute(settings)
    second = infrastructure.JsonSettingsRepository(env=env)

    assert application.GetSettings(second).execute().settings == settings


def test_ac_settings_004_snap_scoped_config_is_not_used(tmp_path: Path) -> None:
    domain, application, infrastructure = _settings_modules()
    home = tmp_path / "home"
    env = {"HOME": str(home), "XDG_CONFIG_HOME": str(home / "snap/code/255/.config")}
    repository = infrastructure.JsonSettingsRepository(env=env)

    application.SaveSettings(repository).execute(domain.AppSettings.defaults())

    assert (home / ".config/codexbar/settings.json").exists()


def test_ac_settings_005_006_corruption_falls_back_without_destroying_evidence(
    tmp_path: Path,
) -> None:
    domain, application, infrastructure = _settings_modules()
    config = tmp_path / "config/codexbar"
    config.mkdir(parents=True)
    path = config / "settings.json"
    corrupt = "{broken"
    path.write_text(corrupt)
    repository = infrastructure.JsonSettingsRepository(
        env={"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    )

    result = application.GetSettings(repository).execute()

    assert result.settings == domain.AppSettings.defaults()
    assert result.diagnostic is not None
    assert path.read_text() == corrupt


def test_ac_settings_012_configured_threshold_changes_classification_not_snapshot() -> None:
    domain, _, _ = _settings_modules()
    snapshot = UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal("0.18")),
            ),
        ),
        observed_at=OBSERVED_AT,
        source=UsageSource.MOCK,
    )
    configured = domain.AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.15")),
        refresh_interval_seconds=domain.RefreshIntervalSeconds(60),
        notifications_enabled=True,
    )

    default_state = UsageViewModel.from_snapshot(snapshot)
    configured_state = UsageViewModel.from_snapshot(snapshot, configured.usage_policy())

    assert default_state.windows[0].state.value == "low"
    assert configured_state.windows[0].state.value == "available"
    assert snapshot.windows[0].remaining == Fraction(Decimal("0.18"))


def test_ac_settings_012_runtime_controller_uses_configured_threshold() -> None:
    domain, _, _ = _settings_modules()
    snapshot = UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal("0.18")),
            ),
        ),
        observed_at=OBSERVED_AT,
        source=UsageSource.MOCK,
    )
    configured = domain.AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.15")),
        refresh_interval_seconds=domain.RefreshIntervalSeconds(60),
        notifications_enabled=True,
    )
    controller = TrayController(
        RefreshCoordinator(GetCurrentUsage(StaticProvider(snapshot))),
        executor=ImmediateExecutor(),
        usage_policy=configured.usage_policy(),
    )

    controller.start_refresh()
    state = controller.poll()

    assert state.usage is not None
    assert state.usage.windows[0].state.value == "available"
    assert snapshot.windows[0].remaining == Fraction(Decimal("0.18"))


def test_ac_settings_013_existing_refresh_timer_accepts_live_interval_change() -> None:
    domain, _, _ = _settings_modules()
    controller_module = import_module("codexbar.ui.controller")
    timer = RecordingRefreshTimer()
    configured = domain.AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.20")),
        refresh_interval_seconds=domain.RefreshIntervalSeconds(180),
        notifications_enabled=True,
    )

    controller_module.apply_refresh_interval(timer, configured)

    assert timer.intervals == [180_000]


def test_ac_settings_015_016_017_reset_restores_defaults_and_preserves_neighbors(
    tmp_path: Path,
) -> None:
    domain, application, infrastructure = _settings_modules()
    env = {"HOME": str(tmp_path), "XDG_CONFIG_HOME": str(tmp_path / "config")}
    repository = infrastructure.JsonSettingsRepository(env=env)
    custom = domain.AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.10")),
        refresh_interval_seconds=domain.RefreshIntervalSeconds(300),
        notifications_enabled=False,
    )
    application.SaveSettings(repository).execute(custom)
    neighbor = tmp_path / "config/codexbar/keep.txt"
    neighbor.write_text("keep")

    application.ResetSettings(repository).execute()
    application.ResetSettings(repository).execute()

    assert application.GetSettings(repository).execute().settings == domain.AppSettings.defaults()
    assert neighbor.read_text() == "keep"
