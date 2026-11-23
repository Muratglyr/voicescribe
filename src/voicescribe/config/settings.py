"""Typed, immutable settings built from layered configuration.

Precedence (lowest to highest):
    packaged ``defaults.toml`` < user TOML file < ``<PREFIX><SEP>SECTION<SEP>KEY`` env vars
    < explicit overrides (CLI flags).
"""

from __future__ import annotations

import os
import tomllib
import types
import typing
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import Any, TypeVar

from voicescribe.core.consistency import ConsistencySettings
from voicescribe.core.errors import ConfigurationError
from voicescribe.core.formatting import FormatSettings
from voicescribe.resources import DEFAULTS_FILE, read_resource

T = TypeVar("T")
_TRUE_STRINGS = frozenset({"1", "true", "yes", "on"})
_LIST_SEPARATOR = ","
_KEY_SEPARATOR = "."


@dataclass(frozen=True)
class AppSettings:
    locale: str
    log_level: str
    log_format: str
    user_config_file: str
    dotenv_file: str
    env_prefix: str
    env_separator: str


@dataclass(frozen=True)
class AudioSettings:
    supported_extensions: tuple[str, ...]
    ffmpeg_executable: str


@dataclass(frozen=True)
class WhisperSettings:
    model: str
    available_models: tuple[str, ...]
    condition_on_previous_text: bool
    verbose: bool


@dataclass(frozen=True)
class DeepgramSettings:
    api_url: str
    api_key_env: str
    model: str
    content_type: str
    auth_scheme: str
    timeout_seconds: int
    query: dict[str, str]


@dataclass(frozen=True)
class TranscriptionSettings:
    engine: str
    diarization_engine: str
    fallback_engine: str
    language: str
    whisper: WhisperSettings
    deepgram: DeepgramSettings


@dataclass(frozen=True)
class LlmSettings:
    base_url: str
    api_key_env: str
    model: str
    system_prompt: str
    chunk_max_chars: int
    temperature: float


@dataclass(frozen=True)
class EditingSettings:
    enabled: bool
    llm: LlmSettings


@dataclass(frozen=True)
class OutputSettings:
    directory: Path
    formats: tuple[str, ...]
    edited_suffix: str
    encoding: str
    json_indent: int


@dataclass(frozen=True)
class ProgressSettings:
    enabled: bool
    unit: str


@dataclass(frozen=True)
class Settings:
    app: AppSettings
    audio: AudioSettings
    transcription: TranscriptionSettings
    editing: EditingSettings
    consistency: ConsistencySettings
    format: FormatSettings
    output: OutputSettings
    progress: ProgressSettings


class SettingsLoader:
    """Merges the configuration layers and converts the result into :class:`Settings`."""

    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = environ

    def load(
        self,
        config_file: Path | None = None,
        overrides: Mapping[str, object] | None = None,
    ) -> Settings:
        data = tomllib.loads(read_resource(DEFAULTS_FILE))
        app = data["app"]

        user_file = config_file or Path(app["user_config_file"])
        if config_file is not None and not config_file.is_file():
            raise ConfigurationError("error.config_not_found", path=config_file)
        if user_file.is_file():
            with user_file.open("rb") as handle:
                _deep_merge(data, tomllib.load(handle))

        environ = os.environ if self._environ is None else self._environ
        prefix = data["app"]["env_prefix"] + data["app"]["env_separator"]
        for name, value in environ.items():
            if name.startswith(prefix):
                path = name[len(prefix) :].lower().split(data["app"]["env_separator"])
                _set_path(data, path, value)

        for dotted_key, override in (overrides or {}).items():
            _set_path(data, dotted_key.split(_KEY_SEPARATOR), override)

        return _build(Settings, data)


def _deep_merge(base: dict[str, Any], update: Mapping[str, Any]) -> None:
    for key, value in update.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def _set_path(data: dict[str, Any], path: list[str], value: object) -> None:
    node = data
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value


def _build(cls: type[T], data: Mapping[str, Any]) -> T:
    """Recursively instantiate a settings dataclass from a mapping, coercing value types."""
    hints = typing.get_type_hints(cls)
    known = {field.name for field in fields(cls)}  # type: ignore[arg-type]
    unknown = set(data) - known
    if unknown:
        raise ConfigurationError("error.unknown_config_keys", section=cls.__name__, keys=sorted(unknown))
    kwargs = {name: _coerce(data[name], hints[name]) for name in known if name in data}
    return cls(**kwargs)


def _coerce(value: Any, target: Any) -> Any:
    if is_dataclass(target) and isinstance(target, type):
        return _build(target, value)
    origin = typing.get_origin(target)
    if origin is tuple:
        items = value.split(_LIST_SEPARATOR) if isinstance(value, str) else value
        return tuple(item.strip() if isinstance(item, str) else item for item in items)
    if origin is dict or isinstance(target, types.GenericAlias):
        return dict(value)
    if target is bool:
        return value.strip().lower() in _TRUE_STRINGS if isinstance(value, str) else bool(value)
    if target in (int, float, str, Path):
        return target(value)
    return value
