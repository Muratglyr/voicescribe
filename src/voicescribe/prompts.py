"""Prompt templates stored as files under ``resources/prompts`` (or anywhere on disk)."""

from __future__ import annotations

from pathlib import Path
from string import Template

from .errors import ConfigurationError
from .resources import PROMPTS_DIR, RESOURCE_ENCODING, resource


class PromptLibrary:
    """Loads prompt templates and fills ``$placeholders`` with :class:`string.Template`.

    A prompt reference is either a file name inside the packaged prompt folder or a
    path to a user-supplied file, so prompts can be changed without touching code.
    """

    def load(self, reference: str, **variables: object) -> str:
        return Template(self._read(reference)).safe_substitute(variables)

    @staticmethod
    def _read(reference: str) -> str:
        user_file = Path(reference)
        if user_file.is_file():
            return user_file.read_text(encoding=RESOURCE_ENCODING)
        packaged = resource(PROMPTS_DIR, reference)
        if packaged.is_file():
            return packaged.read_text(encoding=RESOURCE_ENCODING)
        raise ConfigurationError("error.prompt_not_found", name=reference)
