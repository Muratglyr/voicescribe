# voicescribe

[![CI](https://github.com/Muratglyr/voicescribe/actions/workflows/ci.yml/badge.svg)](https://github.com/Muratglyr/voicescribe/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Typed](https://img.shields.io/badge/typing-mypy%20strict-informational)

**English** | [Türkçe](README.tr.md)

A configurable speech-to-text pipeline for any recording: meetings, podcasts,
interviews, lectures, voice notes.

- **Local transcription** with OpenAI Whisper. Audio never leaves your machine.
- **Speaker diarization** with Deepgram (`SPEAKER_00`, `SPEAKER_01`, ...).
- **LLM copy-editing** through any OpenAI-compatible API (OpenRouter by default).
  It fixes punctuation and paragraphs, and never summarises, translates or "improves"
  what people said.
- **Speaker-consistency check** that warns when an LLM moves a turn to the wrong speaker.
- **Export** as plain text, structured JSON or SRT subtitles.
- **Fully configuration-driven.** Engines, models, prompts, labels, output formats and
  messages all live in TOML and Markdown files, not in code.

## Installation

```bash
pip install "voicescribe[all] @ git+https://github.com/Muratglyr/voicescribe"
```

Install only what you need with extras: `whisper` (local), `deepgram` (cloud
diarization), `llm` (editing). For example: `pip install "voicescribe[whisper]"`.

Whisper also needs [ffmpeg](https://ffmpeg.org/) on your `PATH`
(`brew install ffmpeg`, `winget install ffmpeg`, `sudo apt install ffmpeg`).

## Usage

```bash
voicescribe meeting.m4a                                  # local Whisper -> transcripts/meeting.txt
voicescribe meeting.m4a --format srt --format json       # subtitles + structured output
voicescribe interview.m4a --diarize --edit               # speakers + LLM clean-up
voicescribe recordings/ --folder --language de           # a whole folder, in German
voicescribe meeting.m4a --config team.toml               # your own configuration
python -m voicescribe --help
```

| Flag | Overrides config key |
|---|---|
| `--model` | `transcription.whisper.model` |
| `--language` | `transcription.language` |
| `--output` | `output.directory` |
| `--format` (repeatable) | `output.formats` |
| `--diarize` | `transcription.engine` set to `transcription.diarization_engine` |
| `--edit` / `--llm-model` | `editing.enabled` / `editing.llm.model` |
| `--config` | path to a user TOML file |

## Configuration

Every setting has a default in
[`src/voicescribe/resources/defaults.toml`](src/voicescribe/resources/defaults.toml).
Override only what you need. Later layers win:

1. Packaged defaults
2. A user TOML file: `./voicescribe.toml`, or the file passed with `--config`
   (see [`voicescribe.example.toml`](voicescribe.example.toml))
3. Environment variables `VOICESCRIBE__<SECTION>__<KEY>`, for example
   `VOICESCRIBE__EDITING__LLM__MODEL=openai/gpt-4o-mini`
4. Command-line flags

Unknown keys are rejected, so typos fail loudly instead of being ignored.

**Secrets** never go into config files. The config only names the environment
variable that holds each key (`api_key_env`). Put the keys in `.env`
(see [`.env.example`](.env.example)), which is git-ignored.

**Prompts** are Markdown files in
[`src/voicescribe/resources/prompts/`](src/voicescribe/resources/prompts/). To use your
own, set `editing.llm.system_prompt = "path/to/prompt.md"`. Placeholders such as
`$speaker_a` are filled in from the configured label format.

**Messages** shown by the CLI live in
[`resources/messages/`](src/voicescribe/resources/messages/) (`en`, `tr`). Add a
language by adding a file and setting `app.locale`.

## Architecture

```
src/voicescribe/
├── domain.py        Transcript / Utterance: immutable, engine-independent model
├── ports.py         Protocols: Transcriber, TranscriptEditor, TranscriptWriter, TranscriptInspector
├── pipeline.py      Orchestration; depends only on the protocols
├── factory.py       Composition root: Settings -> wired pipeline (engine/format registries)
├── settings.py      Typed, frozen settings from layered TOML + env + CLI
├── transcribers/    whisper.py, deepgram.py
├── editors/         llm.py (chunked LLM editing), consistency.py (speaker mix-up detection)
├── writers/         text.py, json.py, srt.py
├── formatting.py    Transcript <-> "LABEL: text" rendering, parsing and chunking
├── audio.py         Input discovery, ffmpeg check
├── prompts.py       Prompt templates from files
├── messages.py      Localised user-facing text
├── cli.py           Thin CLI: flags -> config overrides
└── resources/       defaults.toml, prompts/, messages/
```

To add a new speech engine or output format, implement the matching protocol in
`ports.py` and register it in `factory.py`. The pipeline does not change. Heavy
dependencies (`whisper`, `requests`, `openai`) are imported lazily, and a missing
extra produces an install hint instead of a traceback.

You can also use it as a library:

```python
from pathlib import Path
from voicescribe import Messages, PipelineFactory, SettingsLoader

settings = SettingsLoader().load(overrides={"output.formats": ["json"]})
pipeline = PipelineFactory(settings, Messages.load(settings.app.locale)).build()
pipeline.run(Path("meeting.m4a"))
```

## Privacy

- With the default `whisper` engine, everything runs locally.
- `--diarize` uploads the audio file to Deepgram.
- `--edit` sends the transcript text to the LLM provider you configured.

Recordings usually contain other people's voices. Get consent before using the cloud
options, and check the laws that apply to you (e.g. GDPR).

## Development

```bash
pip install -e ".[dev]"
pre-commit install          # ruff, gitleaks and file checks on every commit
ruff check . && ruff format --check .
mypy                        # strict
pytest --cov
```

CI runs lint, strict type checking and tests on Python 3.11 to 3.13, plus a gitleaks
secret scan, on every push and pull request.

### GPU acceleration (optional)

The default PyTorch install is CPU-only. With an NVIDIA GPU, install the CUDA build
from [pytorch.org](https://pytorch.org/get-started/locally/) for a several-fold
speed-up of local Whisper.

## License

[MIT](LICENSE)
