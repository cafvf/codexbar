from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from codexbar.domain.errors import SettingsError
from codexbar.domain.settings import AppSettings


class SettingsOrigin(StrEnum):
    DEFAULTS = "defaults"
    PERSISTED = "persisted"


@dataclass(frozen=True, slots=True)
class SettingsLoadResult:
    settings: AppSettings
    origin: SettingsOrigin
    diagnostic: SettingsError | None = None
    source_schema_version: int | None = None

    @property
    def migrated_from_schema_v1(self) -> bool:
        return self.origin is SettingsOrigin.PERSISTED and self.source_schema_version == 1


class SettingsRepository(Protocol):
    def load(self) -> SettingsLoadResult: ...

    def save(self, settings: AppSettings) -> None: ...

    def reset(self) -> None: ...


@dataclass(frozen=True, slots=True)
class GetSettings:
    repository: SettingsRepository

    def execute(self) -> SettingsLoadResult:
        return self.repository.load()


@dataclass(frozen=True, slots=True)
class SaveSettings:
    repository: SettingsRepository

    def execute(self, settings: AppSettings) -> None:
        self.repository.save(settings)


@dataclass(frozen=True, slots=True)
class ResetSettings:
    repository: SettingsRepository

    def execute(self) -> None:
        self.repository.reset()
