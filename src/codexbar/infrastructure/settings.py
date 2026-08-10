from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from contextlib import suppress
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from codexbar.application.settings import SettingsLoadResult, SettingsOrigin
from codexbar.domain.errors import (
    SettingsDocumentError,
    SettingsReadError,
    SettingsSchemaError,
    SettingsWriteError,
)
from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.domain.settings import (
    AppSettings,
    RefreshIntervalSeconds,
    UsageReserve,
    UsageReservePolicy,
)

_SCHEMA_VERSION = 2
_SCHEMA_1_KEYS = frozenset(
    {
        "schema_version",
        "low_remaining_threshold",
        "refresh_interval_seconds",
        "notifications_enabled",
    }
)
_SCHEMA_2_KEYS = _SCHEMA_1_KEYS | {"usage_reserves"}


class JsonSettingsRepository:
    def __init__(self, *, env: Mapping[str, str] | None = None) -> None:
        self._env = dict(os.environ if env is None else env)
        self._path = _settings_path(self._env)

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> SettingsLoadResult:
        if not self._path.exists():
            return SettingsLoadResult(AppSettings.defaults(), SettingsOrigin.DEFAULTS)

        try:
            raw = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            return SettingsLoadResult(
                AppSettings.defaults(),
                SettingsOrigin.DEFAULTS,
                SettingsReadError(f"cannot read settings: {exc}"),
            )

        try:
            payload = json.loads(raw)
            settings, source_schema_version = _decode_settings(payload)
        except (json.JSONDecodeError, SettingsDocumentError, ValueError) as exc:
            document_error = (
                exc
                if isinstance(exc, SettingsDocumentError)
                else SettingsDocumentError(f"invalid settings document: {exc}")
            )
            return SettingsLoadResult(
                AppSettings.defaults(),
                SettingsOrigin.DEFAULTS,
                document_error,
            )

        return SettingsLoadResult(
            settings,
            SettingsOrigin.PERSISTED,
            source_schema_version=source_schema_version,
        )

    def save(self, settings: AppSettings) -> None:
        payload = _encode_settings(settings)
        parent = self._path.parent

        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise SettingsWriteError(f"cannot create settings directory: {exc}") from exc

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=parent,
                prefix=".settings.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(temp_path, self._path)
            temp_path = None
        except OSError as exc:
            raise SettingsWriteError(f"cannot write settings: {exc}") from exc
        finally:
            if temp_path is not None:
                with suppress(FileNotFoundError):
                    temp_path.unlink()

    def reset(self) -> None:
        try:
            self._path.unlink()
        except FileNotFoundError:
            return
        except OSError as exc:
            raise SettingsWriteError(f"cannot reset settings: {exc}") from exc


def _settings_path(env: Mapping[str, str]) -> Path:
    home = Path(env.get("HOME", str(Path.home()))).expanduser()
    raw = env.get("XDG_CONFIG_HOME")

    if raw:
        candidate = Path(raw).expanduser()
        config_home = (
            candidate if not _is_snap_scoped(candidate, home) else home / ".config"
        )
    else:
        config_home = home / ".config"

    return config_home / "codexbar" / "settings.json"


def _is_snap_scoped(path: Path, home: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to((home / "snap").resolve(strict=False))
    except ValueError:
        return False
    return True


def _encode_settings(settings: AppSettings) -> dict[str, object]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "low_remaining_threshold": str(settings.low_remaining_threshold.value),
        "refresh_interval_seconds": settings.refresh_interval_seconds.value,
        "notifications_enabled": settings.notifications_enabled,
        "usage_reserves": {
            entry.window_id.value: str(entry.reserve.value)
            for entry in sorted(
                settings.usage_reserves.entries,
                key=lambda item: item.window_id.value,
            )
        },
    }


def _decode_settings(payload: Any) -> tuple[AppSettings, int]:
    if not isinstance(payload, dict):
        raise SettingsDocumentError("settings document must be a JSON object")

    schema_version = payload.get("schema_version")
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise SettingsSchemaError(
            f"unsupported settings schema version: {schema_version!r}"
        )

    if schema_version == 1:
        _validate_keys(payload, _SCHEMA_1_KEYS)
        reserves = UsageReservePolicy()
    elif schema_version == 2:
        _validate_keys(payload, _SCHEMA_2_KEYS)
        reserves = _decode_usage_reserves(payload["usage_reserves"])
    else:
        raise SettingsSchemaError(
            f"unsupported settings schema version: {schema_version!r}"
        )

    threshold = _decode_fraction_string(
        payload["low_remaining_threshold"],
        "low_remaining_threshold",
    )

    refresh_raw = payload["refresh_interval_seconds"]
    if isinstance(refresh_raw, bool) or not isinstance(refresh_raw, int):
        raise SettingsDocumentError("refresh_interval_seconds must be an integer")

    notifications_raw = payload["notifications_enabled"]
    if not isinstance(notifications_raw, bool):
        raise SettingsDocumentError("notifications_enabled must be a boolean")

    try:
        settings = AppSettings(
            low_remaining_threshold=threshold,
            refresh_interval_seconds=RefreshIntervalSeconds(refresh_raw),
            notifications_enabled=notifications_raw,
            usage_reserves=reserves,
        )
    except ValueError as exc:
        raise SettingsDocumentError(f"invalid settings value: {exc}") from exc

    return settings, schema_version


def _validate_keys(payload: dict[str, Any], expected: frozenset[str]) -> None:
    if frozenset(payload) == expected:
        return
    unknown = sorted(set(payload) - expected)
    missing = sorted(expected - set(payload))
    detail = []
    if unknown:
        detail.append(f"unknown fields: {', '.join(unknown)}")
    if missing:
        detail.append(f"missing fields: {', '.join(missing)}")
    raise SettingsSchemaError(
        "; ".join(detail) or "settings fields do not match schema"
    )


def _decode_fraction_string(value: object, field: str) -> Fraction:
    if not isinstance(value, str):
        raise SettingsDocumentError(f"{field} must be a decimal string")
    try:
        return Fraction(Decimal(value))
    except (InvalidOperation, ValueError) as exc:
        raise SettingsDocumentError(f"invalid {field}") from exc


def _decode_usage_reserves(value: object) -> UsageReservePolicy:
    if not isinstance(value, dict):
        raise SettingsDocumentError("usage_reserves must be an object")

    entries: list[UsageReserve] = []
    for raw_window_id, raw_reserve in value.items():
        if not isinstance(raw_window_id, str) or not raw_window_id.strip():
            raise SettingsDocumentError(
                "usage_reserves keys must be non-empty window-id strings"
            )
        reserve = _decode_fraction_string(
            raw_reserve,
            f"usage_reserves[{raw_window_id!r}]",
        )
        try:
            entries.append(
                UsageReserve(UsageWindowId(raw_window_id), reserve)
            )
        except ValueError as exc:
            raise SettingsDocumentError(
                f"invalid usage reserve for {raw_window_id!r}: {exc}"
            ) from exc

    return UsageReservePolicy(
        tuple(sorted(entries, key=lambda item: item.window_id.value))
    )
