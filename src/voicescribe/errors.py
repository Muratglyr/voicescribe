"""Exception hierarchy.

Exceptions carry a message *key* and parameters instead of a rendered text, so the
wording stays in the message catalogues (``resources/messages``) and can be localised.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .messages import Messages


class VoicescribeError(Exception):
    """Base class for every error raised by voicescribe."""

    def __init__(self, message_key: str, **params: object) -> None:
        super().__init__(message_key, params)
        self.message_key = message_key
        self.params = params

    def render(self, messages: Messages) -> str:
        return messages(self.message_key, **self.params)


class ConfigurationError(VoicescribeError):
    """Invalid or missing configuration."""


class InputError(VoicescribeError):
    """The input path or audio file cannot be processed."""


class DependencyError(VoicescribeError):
    """An optional dependency required by the selected feature is not installed."""
