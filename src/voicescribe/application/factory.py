"""Composition root: turns :class:`Settings` into a wired :class:`TranscriptionPipeline`.

New engines and output formats are added by registering a builder below; nothing
else in the code base has to change.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import cast

from tqdm import tqdm

from voicescribe.adapters.audio import AudioSource
from voicescribe.adapters.editors import LlmTranscriptEditor
from voicescribe.adapters.transcribers import DeepgramTranscriber, WhisperTranscriber, deepgram, whisper
from voicescribe.adapters.writers import JsonWriter, SrtWriter, TextWriter, json, srt, text
from voicescribe.application.pipeline import Progress, TranscriptionPipeline
from voicescribe.config.messages import Messages
from voicescribe.config.prompts import PromptLibrary
from voicescribe.config.settings import Settings
from voicescribe.core.consistency import SpeakerConsistencyInspector
from voicescribe.core.errors import ConfigurationError
from voicescribe.core.formatting import TextChunker, TranscriptFormatter
from voicescribe.core.ports import Transcriber, TranscriptEditor, TranscriptWriter

logger = logging.getLogger(__name__)
_LIST_JOINER = ", "
_SPEAKER_EXAMPLES = (0, 1)

_BuiltTranscriber = tuple[Transcriber, Sequence[Callable[[], None]]]


class PipelineFactory:
    def __init__(
        self,
        settings: Settings,
        messages: Messages,
        environ: Mapping[str, str] | None = None,
        prompts: PromptLibrary | None = None,
    ) -> None:
        self._settings = settings
        self._messages = messages
        self._environ = os.environ if environ is None else environ
        self._prompts = prompts or PromptLibrary()
        self._formatter = TranscriptFormatter(settings.format)
        self._source = AudioSource(settings.audio)

    def build(self) -> TranscriptionPipeline:
        transcriber, preflight = self._transcriber()
        return TranscriptionPipeline(
            source=self._source,
            transcriber=transcriber,
            writers=self._writers(),
            output=self._settings.output,
            messages=self._messages,
            editor=self._editor(),
            inspector=SpeakerConsistencyInspector(self._settings.consistency)
            if self._settings.consistency.enabled
            else None,
            preflight=preflight,
            progress=self._progress(),
        )

    # -- transcription -------------------------------------------------------------

    def _transcriber(self) -> _BuiltTranscriber:
        transcription = self._settings.transcription
        built = self._build_engine(transcription.engine)
        if built is None:
            built = self._build_engine(transcription.fallback_engine)
        if built is None:
            raise ConfigurationError("error.unknown_engine", engine=transcription.engine, available=self._engines())
        return built

    def _build_engine(self, engine: str) -> _BuiltTranscriber | None:
        builder = _TRANSCRIBERS.get(engine)
        if builder is None:
            raise ConfigurationError("error.unknown_engine", engine=engine, available=self._engines())
        return builder(self)

    @staticmethod
    def _engines() -> str:
        return _LIST_JOINER.join(_TRANSCRIBERS)

    def _whisper(self) -> _BuiltTranscriber:
        transcriber = WhisperTranscriber(self._settings.transcription.whisper, self._settings.transcription.language)
        return transcriber, [self._source.verify_ffmpeg]

    def _deepgram(self) -> _BuiltTranscriber | None:
        settings = self._settings.transcription.deepgram
        api_key = self._secret(settings.api_key_env, step=deepgram.ENGINE_NAME)
        if api_key is None:
            return None
        transcriber = DeepgramTranscriber(
            settings=settings,
            language=self._settings.transcription.language,
            api_key=api_key,
            speaker_labeler=self._formatter.speaker_label,
            segment_separator=self._formatter.segment_separator,
        )
        return transcriber, []

    # -- editing -------------------------------------------------------------------

    def _editor(self) -> TranscriptEditor | None:
        editing = self._settings.editing
        if not editing.enabled:
            return None
        api_key = self._secret(editing.llm.api_key_env, step=_EDITING_STEP)
        if api_key is None:
            return None
        if not editing.llm.model:
            logger.warning(self._messages("warning.missing_llm_model"))
            return None
        prompt = self._prompts.load(
            editing.llm.system_prompt,
            speaker_a=self._formatter.speaker_label(_SPEAKER_EXAMPLES[0]),
            speaker_b=self._formatter.speaker_label(_SPEAKER_EXAMPLES[1]),
            separator=self._formatter.speaker_separator.strip(),
        )
        return LlmTranscriptEditor(
            settings=editing.llm,
            api_key=api_key,
            system_prompt=prompt,
            formatter=self._formatter,
            chunker=TextChunker.from_settings(editing.llm.chunk_max_chars, self._settings.format),
        )

    # -- output --------------------------------------------------------------------

    def _writers(self) -> list[TranscriptWriter]:
        writers = []
        for name in self._settings.output.formats:
            builder = _WRITERS.get(name)
            if builder is None:
                raise ConfigurationError("error.unknown_format", format=name, available=_LIST_JOINER.join(_WRITERS))
            writers.append(builder(self))
        return writers

    def _text_writer(self) -> TranscriptWriter:
        return TextWriter(self._formatter, self._settings.output.encoding)

    def _json_writer(self) -> TranscriptWriter:
        return JsonWriter(self._settings.output.encoding, self._settings.output.json_indent)

    def _srt_writer(self) -> TranscriptWriter:
        return SrtWriter(self._formatter, self._settings.output.encoding)

    # -- helpers -------------------------------------------------------------------

    def _secret(self, env_name: str, step: str) -> str | None:
        value = self._environ.get(env_name)
        if not value:
            logger.warning(self._messages("warning.missing_secret", env=env_name, step=step))
            return None
        return value

    def _progress(self) -> Progress:
        if not self._settings.progress.enabled:
            return lambda items: items
        description, unit = self._messages("run.progress"), self._settings.progress.unit

        def wrap(items: Sequence[Path]) -> Iterable[Path]:
            return cast(Iterable[Path], tqdm(items, desc=description, unit=unit))

        return wrap


_EDITING_STEP = "editing"

_TRANSCRIBERS: dict[str, Callable[[PipelineFactory], _BuiltTranscriber | None]] = {
    whisper.ENGINE_NAME: PipelineFactory._whisper,
    deepgram.ENGINE_NAME: PipelineFactory._deepgram,
}

_WRITERS: dict[str, Callable[[PipelineFactory], TranscriptWriter]] = {
    text.FORMAT_NAME: PipelineFactory._text_writer,
    json.FORMAT_NAME: PipelineFactory._json_writer,
    srt.FORMAT_NAME: PipelineFactory._srt_writer,
}
