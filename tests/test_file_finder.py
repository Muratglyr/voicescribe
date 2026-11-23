from pathlib import Path

import pytest

from voicescribe.exceptions import InputNotFoundError, UnsupportedFileError
from voicescribe.file_finder import AudioFileFinder


@pytest.fixture
def finder() -> AudioFileFinder:
    return AudioFileFinder()


@pytest.mark.parametrize(
    "file_name, expected",
    [
        ("kayit.m4a", True),
        ("kayit.MP3", True),
        ("kayit.wav", True),
        ("kayit.mp4", True),
        ("kayit.aac", True),
        ("kayit.ogg", True),
        ("kayit.txt", False),
        ("kayit.mov", False),
    ],
)
def test_is_supported_file(finder: AudioFileFinder, file_name: str, expected: bool) -> None:
    assert finder.is_supported_file(Path(file_name)) is expected


def test_find_files_single_file(tmp_path: Path, finder: AudioFileFinder) -> None:
    file = tmp_path / "kayit.m4a"
    file.write_bytes(b"fake-audio-data")

    result = finder.find_files(file, folder_mode=False)

    assert result == [file]


def test_find_files_unsupported_format(tmp_path: Path, finder: AudioFileFinder) -> None:
    file = tmp_path / "kayit.txt"
    file.write_text("metin")

    with pytest.raises(UnsupportedFileError):
        finder.find_files(file, folder_mode=False)


def test_find_files_folder(tmp_path: Path, finder: AudioFileFinder) -> None:
    (tmp_path / "a.m4a").write_bytes(b"1")
    (tmp_path / "b.mp3").write_bytes(b"2")
    (tmp_path / "notlar.txt").write_text("ilgisiz")

    result = finder.find_files(tmp_path, folder_mode=True)

    assert sorted(p.name for p in result) == ["a.m4a", "b.mp3"]


def test_find_files_empty_folder(tmp_path: Path, finder: AudioFileFinder) -> None:
    with pytest.raises(InputNotFoundError):
        finder.find_files(tmp_path, folder_mode=True)


def test_find_files_missing_path(tmp_path: Path, finder: AudioFileFinder) -> None:
    with pytest.raises(InputNotFoundError):
        finder.find_files(tmp_path / "yok.m4a", folder_mode=False)


def test_find_files_folder_mode_with_single_file_raises(tmp_path: Path, finder: AudioFileFinder) -> None:
    file = tmp_path / "kayit.m4a"
    file.write_bytes(b"1")

    with pytest.raises(InputNotFoundError):
        finder.find_files(file, folder_mode=True)
