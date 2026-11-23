"""Localised user-facing text loaded from ``resources/messages/<locale>.toml``."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping

from .resources import MESSAGES_DIR, RESOURCE_ENCODING, resource

FALLBACK_LOCALE = "en"
CATALOGUE_SUFFIX = ".toml"
KEY_SEPARATOR = "."


class Messages:
    """Looks up ``section.name`` keys and formats them with keyword parameters.

    Keys missing from the selected locale fall back to the English catalogue.
    """

    def __init__(self, catalogue: Mapping[str, Mapping[str, str]]) -> None:
        self._catalogue = catalogue

    @classmethod
    def load(cls, locale: str) -> Messages:
        catalogue = cls._read(FALLBACK_LOCALE)
        if locale != FALLBACK_LOCALE:
            for section, entries in cls._read(locale).items():
                catalogue[section] = {**catalogue.get(section, {}), **entries}
        return cls(catalogue)

    def __call__(self, key: str, **params: object) -> str:
        section, _, name = key.partition(KEY_SEPARATOR)
        return self._catalogue[section][name].format(**params)

    @staticmethod
    def _read(locale: str) -> dict[str, dict[str, str]]:
        handle = resource(MESSAGES_DIR, locale + CATALOGUE_SUFFIX)
        if not handle.is_file():
            return {}
        return tomllib.loads(handle.read_text(encoding=RESOURCE_ENCODING))
