from pathlib import Path

from voicescribe.cli import build_config, parse_args


def test_english_flags_are_parsed() -> None:
    args = parse_args(["rec.m4a", "--folder", "--language", "de", "--output", "out", "--edit", "--diarize"])
    config = build_config(args)

    assert config.input_path == Path("rec.m4a")
    assert config.folder_mode is True
    assert config.language == "de"
    assert config.output_dir == Path("out")
    assert config.edit is True
    assert config.diarize is True


def test_legacy_turkish_flags_still_work() -> None:
    args = parse_args(["rec.m4a", "--klasor", "--dil=tr", "--cikti", "out", "--duzenle", "--konusmaci-ayir"])
    config = build_config(args)

    assert config.folder_mode is True
    assert config.language == "tr"
    assert config.output_dir == Path("out")
    assert config.edit is True
    assert config.diarize is True


def test_defaults() -> None:
    config = build_config(parse_args(["rec.m4a"]))

    assert config.output_dir == Path("./transcripts")
    assert config.edit is False
    assert config.diarize is False
