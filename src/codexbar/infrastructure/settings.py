from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from contextlib import suppress
from datetime import timedelta
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
from codexbar.domain.quantities import TimeToReset
from codexbar.domain.settings import (
    AppSettings,
    RefreshIntervalSeconds,
    UsagePlanCheckpoint,
    UsagePlanCheckpointPolicy,
    UsageReserve,
    UsageReservePolicy,
)

_SCHEMA_VERSION = 3
_SCHEMA_1_KEYS = frozenset(
    {
        "schema_version",
        "low_remaining_threshold",
        "refresh_interval_seconds",
        "notifications_enabled",
    }
)
_SCHEMA_2_KEYS = _SCHEMA_1_KEYS | {"usage_reserves"}
_SCHEMA_3_KEYS = _SCHEMA_2_KEYS | {
    "usage_plan_checkpoints",
    "plan_breach_notifications_enabled",
}
_CHECKPOINT_KEYS = frozenset(
    {
        "time_to_reset_seconds",
        "minimum_remaining",
    }
)


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
    checkpoints: dict[str, list[dict[str, object]]] = {}
    for entry in settings.usage_plan_checkpoints.entries:
        checkpoints.setdefault(entry.window_id.value, []).append(
            {
                "time_to_reset_seconds": _time_to_reset_seconds(entry.time_to_reset),
                "minimum_remaining": str(entry.minimum_remaining.value),
            }
        )

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
        "usage_plan_checkpoints": {
            window_id: checkpoints[window_id]
            for window_id in sorted(checkpoints)
        },
        "plan_breach_notifications_enabled": (
            settings.plan_breach_notifications_enabled
        ),
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
        checkpoints = UsagePlanCheckpointPolicy()
        plan_breach_notifications_enabled = False
    elif schema_version == 2:
        _validate_keys(payload, _SCHEMA_2_KEYS)
        reserves = _decode_usage_reserves(payload["usage_reserves"])
        checkpoints = UsagePlanCheckpointPolicy()
        plan_breach_notifications_enabled = False
    elif schema_version == 3:
        _validate_keys(payload, _SCHEMA_3_KEYS)
        reserves = _decode_usage_reserves(payload["usage_reserves"])
        checkpoints = _decode_usage_plan_checkpoints(
            payload["usage_plan_checkpoints"]
        )
        plan_breach_notifications_enabled = _decode_boolean(
            payload["plan_breach_notifications_enabled"],
            "plan_breach_notifications_enabled",
        )
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

    notifications_enabled = _decode_boolean(
        payload["notifications_enabled"],
        "notifications_enabled",
    )

    try:
        settings = AppSettings(
            low_remaining_threshold=threshold,
            refresh_interval_seconds=RefreshIntervalSeconds(refresh_raw),
            notifications_enabled=notifications_enabled,
            usage_reserves=reserves,
            usage_plan_checkpoints=checkpoints,
            plan_breach_notifications_enabled=plan_breach_notifications_enabled,
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


def _decode_boolean(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise SettingsDocumentError(f"{field} must be a boolean")
    return value


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


def _decode_usage_plan_checkpoints(value: object) -> UsagePlanCheckpointPolicy:
    if not isinstance(value, dict):
        raise SettingsDocumentError("usage_plan_checkpoints must be an object")

    entries: list[UsagePlanCheckpoint] = []
    for raw_window_id, raw_checkpoints in value.items():
        if not isinstance(raw_window_id, str) or not raw_window_id.strip():
            raise SettingsDocumentError(
                "usage_plan_checkpoints keys must be non-empty window-id strings"
            )
        if not isinstance(raw_checkpoints, list):
            raise SettingsDocumentError(
                f"usage_plan_checkpoints[{raw_window_id!r}] must be an array"
            )

        try:
            window_id = UsageWindowId(raw_window_id)
        except ValueError as exc:
            raise SettingsDocumentError(
                f"invalid usage plan window id {raw_window_id!r}: {exc}"
            ) from exc

        for index, raw_checkpoint in enumerate(raw_checkpoints):
            field = f"usage_plan_checkpoints[{raw_window_id!r}][{index}]"
            if not isinstance(raw_checkpoint, dict):
                raise SettingsDocumentError(f"{field} must be an object")
            _validate_keys(raw_checkpoint, _CHECKPOINT_KEYS)

            raw_seconds = raw_checkpoint["time_to_reset_seconds"]
            if (
                isinstance(raw_seconds, bool)
                or not isinstance(raw_seconds, int)
                or raw_seconds < 0
            ):
                raise SettingsDocumentError(
                    f"{field}.time_to_reset_seconds must be a non-negative integer"
                )

            minimum = _decode_fraction_string(
                raw_checkpoint["minimum_remaining"],
                f"{field}.minimum_remaining",
            )
            try:
                time_to_reset = TimeToReset(timedelta(seconds=raw_seconds))
            except (OverflowError, ValueError) as exc:
                raise SettingsDocumentError(
                    f"{field}.time_to_reset_seconds is outside the supported range"
                ) from exc
            entries.append(
                UsagePlanCheckpoint(
                    window_id=window_id,
                    time_to_reset=time_to_reset,
                    minimum_remaining=minimum,
                )
            )

    try:
        return UsagePlanCheckpointPolicy(tuple(entries))
    except ValueError as exc:
        raise SettingsDocumentError(f"invalid usage plan checkpoints: {exc}") from exc


def _time_to_reset_seconds(value: TimeToReset) -> int:
    duration = value.duration
    if duration.microseconds != 0:
        raise ValueError("persisted plan checkpoint must use whole seconds")
    return duration.days * 86_400 + duration.seconds
