# Examples

These files are **synthetic**. The dialogue was written for this repository and
does not come from a real recording.

| File | What it shows |
|---|---|
| `sample_podcast.txt` | Raw output with `--konusmaci-ayir` (Deepgram diarization), no punctuation |
| `sample_podcast_duzenlenmis.txt` | The same transcript after `--duzenle` (LLM copy-editing): punctuation and paragraphs fixed, filler words trimmed, speaker turns and wording unchanged |

Command that produces this pair of files:

```bash
python transkript.py "sample_podcast.m4a" --konusmaci-ayir --duzenle
```
