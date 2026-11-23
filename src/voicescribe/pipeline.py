"""Orchestration of transcription, editing, inspection and output.

The pipeline depends only on the protocols in :mod:`voicescribe.ports`; it never
knows which engine, LLM or file format is in use.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

from .audio import AudioSource
from .domain import Transcript
from .messages import Messages
from .ports import Transcriber, TranscriptEditor, TranscriptInspector, TranscriptWriter
from .settings import OutputSettings

logger = logging.getLogger(__name__)

Progress = Callable[[Sequence[Path]], Iterable[Path]]


def _no_progress(items: Sequence[Path]) -> Iterable[Path]:
    return items


class TranscriptionPipeline:
    def __init__(
        self,
        *,
        source: AudioSource,
        transcriber: Transcriber,
        writers: Sequence[TranscriptWriter],
        output: OutputSettings,
        messages: Messages,
        editor: TranscriptEditor | None = None,
        inspector: TranscriptInspector | None = None,
        preflight: Sequence[Callable[[], None]] = (),
        progress: Progress = _no_progress,
    ) -> None:
        self._source = source
        self._transcriber = transcriber
        self._writers = writers
        self._output = output
        self._messages = messages
        self._editor = editor
        self._inspector = inspector
        self._preflight = preflight
        self._progress = progress

    def run(self, input_path: Path, folder_mode: bool = False) -> list[Path]:
        """Process one file or a folder and return the paths of every file written."""
        audio_files = self._source.discover(input_path, folder_mode)  # user errors first
        for check in self._preflight:
            check()
        self._output.directory.mkdir(parents=True, exist_ok=True)

        written: list[Path] = []
        for index, audio_file in enumerate(self._progress(audio_files), start=1):
            logger.info(self._messages("run.processing", index=index, total=len(audio_files), name=audio_file.name))
            written.extend(self.process(audio_file))
        logger.info(self._messages("run.done", count=len(written)))
        return written

    def process(self, audio_file: Path) -> list[Path]:
        logger.info(self._messages("run.transcribing", engine=self._transcriber.name))
        raw = self._transcriber.transcribe(audio_file)
        written = self._write(raw, audio_file.stem)

        if self._editor is not None:
            logger.info(self._messages("run.editing", model=self._editor.name))
            edited = self._editor.edit(raw)
            self._inspect(raw, edited)
            written += self._write(edited, audio_file.stem + self._output.edited_suffix)
        return written

    def _inspect(self, raw: Transcript, edited: Transcript) -> None:
        if self._inspector is None:
            return
        for issue in self._inspector.inspect(raw, edited):
            logger.warning(
                self._messages(
                    "warning.speaker_mixup",
                    snippet=issue.snippet,
                    raw=issue.raw_speaker,
                    edited=issue.edited_speaker,
                    expected=issue.expected_speaker,
                )
            )

    def _write(self, transcript: Transcript, stem: str) -> list[Path]:
        written: list[Path] = []
        for writer in self._writers:
            if not writer.supports(transcript):
                logger.warning(self._messages("warning.no_timestamps", format=writer.format_name, name=stem))
                continue
            path = writer.write(transcript, self._output.directory / stem)
            logger.info(self._messages("run.saved", path=path))
            written.append(path)
        return written
