"""voicescribe: a configurable speech-to-text pipeline.

Library use::

    from pathlib import Path
    from voicescribe import Messages, PipelineFactory, SettingsLoader

    settings = SettingsLoader().load(overrides={"output.formats": ["txt", "srt"]})
    pipeline = PipelineFactory(settings, Messages.load(settings.app.locale)).build()
    pipeline.run(Path("meeting.m4a"))
"""

__version__ = "0.2.0"

from voicescribe.application.factory import PipelineFactory
from voicescribe.application.pipeline import TranscriptionPipeline
from voicescribe.config.messages import Messages
from voicescribe.config.settings import Settings, SettingsLoader
from voicescribe.core.domain import Transcript, Utterance

__all__ = [
    "Messages",
    "PipelineFactory",
    "Settings",
    "SettingsLoader",
    "Transcript",
    "TranscriptionPipeline",
    "Utterance",
    "__version__",
]
