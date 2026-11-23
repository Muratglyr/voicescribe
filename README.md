# voicescribe

**English** | [Türkçe](README.tr.md)

A modular speech-to-text pipeline for any kind of conversation recording:
meetings, podcasts, interviews, lectures, voice notes. It takes audio files
(`.m4a`, `.mp3`, `.wav`, `.mp4`, `.aac`, `.ogg`) and:

1. **Transcribes them fully locally** with OpenAI Whisper. No audio leaves your
   machine. The default language is English; change it with `--language`.
2. **Optionally separates speakers** (`--diarize`) via Deepgram
   diarization. In this mode transcription is done by Deepgram in the cloud
   instead of local Whisper, and the output is labelled
   `SPEAKER_00: ...` / `SPEAKER_01: ...` deterministically.
3. **Optionally cleans up the transcript** (`--edit`) with an LLM of your
   choice through OpenRouter. It fixes punctuation and paragraphs only. It does
   not summarise, translate or "improve" what people said, and it keeps
   mixed-language passages in their original language.
4. **Checks speaker consistency** after LLM editing and warns you if a turn
   seems to have been attributed to the wrong speaker.

> You can also run it as a module: `python -m voicescribe recording.m4a`.

## Quick start

```bash
pip install -r requirements.txt
# ffmpeg must be installed and on PATH (see "Installation")
python transcribe.py "recording.m4a"
```

Output files are written to `./transcripts/` by default (`--output` to change it).
See [`examples/`](examples/) for what a raw and an edited transcript look like.

## Architecture

Each module has a single responsibility (package: `voicescribe/`):

| Module | Class | Responsibility |
|---|---|---|
| `config.py` | `AppConfig` | Immutable runtime configuration |
| `exceptions.py` | `TranscriptError` + subclasses | Project error hierarchy |
| `provider_settings.py` | `OpenRouterSettings`, `DeepgramSettings` | Read external-service settings **only** from environment variables |
| `file_finder.py` | `AudioFileFinder` | Find supported audio files in a file or folder |
| `ffmpeg_checker.py` | `FFmpegChecker` | Verify ffmpeg is installed |
| `transcriber.py` | `WhisperTranscriber` | Local Whisper transcription with timestamped segments |
| `deepgram_diarized_transcriber.py` | `DeepgramDiarizedTranscriber` | Transcript + speaker labels from Deepgram in one request |
| `text_chunker.py` | `TextChunker` | Split long text into LLM-context-sized chunks |
| `llm_editor.py` | `LlmEditor` | Copy-edit the raw transcript with an LLM via OpenRouter |
| `speaker_consistency.py` | — | Detect turns the LLM moved to the wrong speaker |
| `pipeline.py` | `TranscriptPipeline` | Orchestrates the steps above |
| `cli.py` | — | Argument parsing, `.env` loading, entry point |

No provider name, model name, API key or service URL is hardcoded. All of
them come from `.env` (see below), and CLI arguments override them. Heavy
dependencies (`whisper`, `openai`, `requests`) are imported lazily, so most
classes can be tested without them installed.

## Installation

### 1. Python dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt   # optional, for tests
```

### 2. ffmpeg

Whisper needs **ffmpeg**:

- macOS: `brew install ffmpeg`
- Windows: `winget install ffmpeg` (or `choco install ffmpeg`)
- Debian/Ubuntu: `sudo apt update && sudo apt install ffmpeg`

### 3. (Optional) NVIDIA GPU acceleration

`requirements.txt` installs CPU-only PyTorch. With an NVIDIA GPU, local
Whisper runs several times faster. For example, a 21-minute recording took
about 11 minutes on CPU and about 2.5 minutes on an RTX 5060 with the `small`
model.

```bash
pip uninstall torch torchaudio -y
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
python -c "import torch; print(torch.cuda.is_available())"
```

Choose the CUDA build that matches your driver at
[pytorch.org/get-started/locally](https://pytorch.org/get-started/locally/).

### 4. Environment variables (`.env`)

Copy `.env.example` to `.env`. It is loaded automatically at startup.
**Never commit your `.env` file.** It is already listed in `.gitignore`.

| Variable | Used by | Notes |
|---|---|---|
| `OPENROUTER_API_KEY` | `--edit` | Get one at [openrouter.ai](https://openrouter.ai) |
| `OPENROUTER_BASE_URL` | `--edit` | Pre-filled: `https://openrouter.ai/api/v1` |
| `OPENROUTER_MODEL` | `--edit` | e.g. `anthropic/claude-haiku-4.5`, `openai/gpt-4o-mini` |
| `DEEPGRAM_API_KEY` | `--diarize` | Get one at [console.deepgram.com](https://console.deepgram.com/) |
| `DEEPGRAM_MODEL` | `--diarize` | Pre-filled: `nova-3` |

If a required value is missing, the program does not crash. It skips that
step and prints a warning.

## Usage

```bash
python transcribe.py "recording.m4a"
python transcribe.py "recordings/" --folder
python transcribe.py "recording.m4a" --model medium
python transcribe.py "recording.m4a" --diarize
python transcribe.py "recording.m4a" --edit --llm-model openai/gpt-4o-mini
python transcribe.py "recordings/" --folder --diarize --edit --output ./out
```

| Flag | Meaning | Default |
|---|---|---|
| `input` | Audio file, or folder with `--folder` | required |
| `--folder` | Treat input as a folder and process every supported file | off |
| `--model` | Whisper size: `tiny`, `base`, `small`, `medium`, `large` | `medium` |
| `--language` | Transcript language | `en` |
| `--output` | Output folder | `./transcripts` |
| `--diarize` | Speaker diarization via Deepgram (needs `DEEPGRAM_API_KEY`) | off |
| `--edit` | LLM copy-editing via OpenRouter | off |
| `--llm-model` | OpenRouter model id for `--edit` | `OPENROUTER_MODEL` |

With `--diarize`, `--model` is ignored because transcription happens on
Deepgram. `--language` is still passed through to Deepgram.

### Whisper model sizes

| Model | Speed | Accuracy | Note |
|---|---|---|---|
| `tiny` | very fast | low | quick preview |
| `base` | fast | low-medium | |
| `small` | medium | medium-good | higher hallucination risk on noisy audio |
| `medium` | slow | good | default; noticeably fewer hallucinations on low-quality audio |
| `large` | very slow | best | needs strong hardware |

## Privacy

- **Default mode is fully local.** Whisper runs on your machine and audio is
  never uploaded.
- `--diarize` **uploads the whole audio file** to Deepgram.
- `--edit` sends the **text** transcript (not audio) to the LLM provider you
  choose through OpenRouter.

Recordings usually contain other people's voices. Make sure everyone
recorded knows about it and agrees before you use the cloud options, and check
the laws that apply to you (e.g. GDPR).

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

## License

[MIT](LICENSE)
