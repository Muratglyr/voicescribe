"""Input discovery and system prerequisites for audio processing."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from .errors import InputError
from .settings import AudioSettings

_LIST_JOINER = ", "


class AudioSource:
    """Finds the audio files to process and verifies that ffmpeg is available."""

    def __init__(
        self,
        settings: AudioSettings,
        which: Callable[[str], str | None] = shutil.which,
    ) -> None:
        self._settings = settings
        self._extensions = frozenset(ext.lower() for ext in settings.supported_extensions)
        self._which = which

    def verify_ffmpeg(self) -> None:
        if self._which(self._settings.ffmpeg_executable) is None:
            raise InputError("error.ffmpeg_missing", executable=self._settings.ffmpeg_executable)

    def is_supported(self, file: Path) -> bool:
        return file.suffix.lower() in self._extensions

    def discover(self, input_path: Path, folder_mode: bool) -> list[Path]:
        if not input_path.exists():
            raise InputError("error.path_not_found", path=input_path)
        return self._from_folder(input_path) if folder_mode else self._single_file(input_path)

    def _from_folder(self, folder: Path) -> list[Path]:
        if not folder.is_dir():
            raise InputError("error.not_a_folder", path=folder)
        files = sorted(p for p in folder.iterdir() if p.is_file() and self.is_supported(p))
        if not files:
            raise InputError("error.no_audio_in_folder", path=folder, extensions=self._listing())
        return files

    def _single_file(self, file: Path) -> list[Path]:
        if not file.is_file():
            raise InputError("error.not_a_file", path=file)
        if not self.is_supported(file):
            raise InputError("error.unsupported_format", suffix=file.suffix, extensions=self._listing())
        return [file]

    def _listing(self) -> str:
        return _LIST_JOINER.join(sorted(self._extensions))
