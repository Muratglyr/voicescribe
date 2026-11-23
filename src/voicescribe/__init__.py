"""voicescribe: a configurable speech-to-text pipeline.

Library use::

    from pathlib import Path
    from voicescribe import Messages, PipelineFactory, SettingsLoader

    settings = SettingsLoader().load(overrides={"output.formats": ["txt", "srt"]})
    pipeline = PipelineFactory(settings, Messages.load(settings.app.locale)).build()
    pipeline.run(Path("meeting.m4a"))
"""

__version__ = "0.2.0"

from .domain import Transcript, Utterance
from .factory import PipelineFactory
from .messages import Messages
from .pipeline import TranscriptionPipeline
from .settings import Settings, SettingsLoader

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
