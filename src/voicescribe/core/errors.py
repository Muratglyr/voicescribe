"""Exception hierarchy.

Exceptions carry a message *key* and parameters instead of a rendered text, so the
wording stays in the message catalogues (``resources/messages``) and can be localised.
"""

from __future__ import annotations

from collections.abc import Callable

Translate = Callable[..., str]


class VoicescribeError(Exception):
    """Base class for every error raised by voicescribe."""

    def __init__(self, message_key: str, **params: object) -> None:
        super().__init__(message_key, params)
        self.message_key = message_key
        self.params = params

    def render(self, translate: Translate) -> str:
        """Render with any ``translate(key, **params)`` callable, e.g. :class:`Messages`."""
        return translate(self.message_key, **self.params)


class ConfigurationError(VoicescribeError):
    """Invalid or missing configuration."""


class InputError(VoicescribeError):
    """The input path or audio file cannot be processed."""


class DependencyError(VoicescribeError):
    """An optional dependency required by the selected feature is not installed."""
