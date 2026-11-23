"""Girdi olarak verilen dosya ya da klasorden islenecek ses dosyalarini bulur."""

from __future__ import annotations

from pathlib import Path

from .config import SUPPORTED_EXTENSIONS
from .exceptions import InputNotFoundError, UnsupportedFileError


class AudioFileFinder:
    """Desteklenen ses dosyalarini tek dosya ya da klasor girdisinden tespit eder."""

    def __init__(self, supported_extensions: frozenset[str] = SUPPORTED_EXTENSIONS) -> None:
        self._supported_extensions = supported_extensions

    def is_supported_file(self, file: Path) -> bool:
        """Verilen dosyanin uzantisi desteklenen ses formatlarindan biri mi?"""
        return file.suffix.lower() in self._supported_extensions

    def find_files(self, input_path: Path, folder_mode: bool) -> list[Path]:
        """Girdi yoluna gore islenecek ses dosyalarinin siralanmis listesini dondurur."""
        if not input_path.exists():
            raise InputNotFoundError(f"Path not found: {input_path}")

        if folder_mode:
            return self._find_files_in_folder(input_path)
        return self._validate_single_file(input_path)

    def _find_files_in_folder(self, folder_path: Path) -> list[Path]:
        if not folder_path.is_dir():
            raise InputNotFoundError(f"--folder was given but '{folder_path}' is not a folder.")

        files = sorted(
            p for p in folder_path.iterdir() if p.is_file() and self.is_supported_file(p)
        )
        if not files:
            raise InputNotFoundError(
                f"No supported audio files found in '{folder_path}'. "
                f"Supported formats: {', '.join(sorted(self._supported_extensions))}"
            )
        return files

    def _validate_single_file(self, file_path: Path) -> list[Path]:
        if not file_path.is_file():
            raise InputNotFoundError(
                f"'{file_path}' is not a file. Use --folder to process a folder."
            )
        if not self.is_supported_file(file_path):
            raise UnsupportedFileError(
                f"Unsupported file format: {file_path.suffix}. "
                f"Supported formats: {', '.join(sorted(self._supported_extensions))}"
            )
        return [file_path]
