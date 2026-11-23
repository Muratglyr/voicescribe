"""Command-line interface: maps flags onto configuration overrides and runs the pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from dotenv import load_dotenv

from . import __version__
from .errors import VoicescribeError
from .factory import PipelineFactory
from .messages import FALLBACK_LOCALE, Messages
from .settings import Settings, SettingsLoader

PROG = "voicescribe"
_DEBUG_LEVEL = "DEBUG"
_LIST_JOINER = ", "

# CLI flag (argparse dest) -> dotted configuration key it overrides.
_OVERRIDES = {
    "whisper_model": "transcription.whisper.model",
    "language": "transcription.language",
    "output_dir": "output.directory",
    "formats": "output.formats",
    "llm_model": "editing.llm.model",
}


def build_parser(messages: Messages, settings: Settings) -> argparse.ArgumentParser:
    whisper = settings.transcription.whisper
    parser = argparse.ArgumentParser(prog=PROG, description=messages("cli.description"))
    parser.add_argument("input", type=Path, help=messages("cli.input"))
    parser.add_argument("--config", type=Path, help=messages("cli.config"))
    parser.add_argument("--folder", dest="folder_mode", action="store_true", help=messages("cli.folder"))
    parser.add_argument(
        "--model",
        dest="whisper_model",
        choices=whisper.available_models,
        help=messages("cli.model", default=whisper.model),
    )
    parser.add_argument(
        "--language",
        help=messages("cli.language", default=settings.transcription.language),
    )
    parser.add_argument(
        "--output",
        dest="output_dir",
        type=Path,
        help=messages("cli.output", default=settings.output.directory),
    )
    parser.add_argument(
        "--format",
        dest="formats",
        action="append",
        help=messages("cli.format", default=_LIST_JOINER.join(settings.output.formats)),
    )
    parser.add_argument(
        "--edit",
        action="store_true",
        help=messages("cli.edit", env=settings.editing.llm.api_key_env),
    )
    parser.add_argument("--llm-model", dest="llm_model", help=messages("cli.llm_model"))
    parser.add_argument(
        "--diarize",
        action="store_true",
        help=messages("cli.diarize", env=settings.transcription.deepgram.api_key_env),
    )
    parser.add_argument("--verbose", action="store_true", help=messages("cli.verbose"))
    parser.add_argument("--version", action="version", version=f"{PROG} {__version__}", help=messages("cli.version"))
    return parser


def overrides_from(args: argparse.Namespace, settings: Settings) -> dict[str, object]:
    """Translate parsed flags into dotted configuration overrides (unset flags are ignored)."""
    overrides: dict[str, object] = {
        key: getattr(args, dest) for dest, key in _OVERRIDES.items() if getattr(args, dest) is not None
    }
    if args.edit:
        overrides["editing.enabled"] = True
    if args.diarize:
        overrides["transcription.engine"] = settings.transcription.diarization_engine
    if args.verbose:
        overrides["app.log_level"] = _DEBUG_LEVEL
    return overrides


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    config_file = _peek_config(arguments)
    loader = SettingsLoader()

    try:
        _load_dotenv(loader.load(config_file).app.dotenv_file)
        base = loader.load(config_file)
        messages = Messages.load(base.app.locale)
        args = build_parser(messages, base).parse_args(arguments)
        settings = loader.load(config_file, overrides_from(args, base))
    except VoicescribeError as error:
        print(error.render(Messages.load(FALLBACK_LOCALE)), file=sys.stderr)
        return 1

    logging.basicConfig(level=settings.app.log_level, format=settings.app.log_format)
    messages = Messages.load(settings.app.locale)
    try:
        PipelineFactory(settings, messages).build().run(args.input, args.folder_mode)
    except VoicescribeError as error:
        logging.getLogger(PROG).error(messages("error.prefix", message=error.render(messages)))
        return 1
    except Exception as error:  # last-resort guard: show a message instead of a traceback
        logging.getLogger(PROG).debug("", exc_info=True)
        logging.getLogger(PROG).error(messages("error.unexpected", error=error))
        return 1
    return 0


def _peek_config(arguments: Sequence[str]) -> Path | None:
    """Read --config before the full parser exists (its help text depends on the config)."""
    peek = argparse.ArgumentParser(add_help=False)
    peek.add_argument("--config", type=Path)
    config: Path | None = peek.parse_known_args(arguments)[0].config
    return config


def _load_dotenv(dotenv_file: str) -> None:
    load_dotenv(dotenv_file)
