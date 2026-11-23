"""Ham transkripti OpenRouter uzerinden bir LLM ile redakte eden sinif.

OpenRouter, OpenAI ile uyumlu tek bir API uzerinden farkli saglayicilarin
(Anthropic, OpenAI, Meta, Google, vb.) modellerine erisim sunar. Hangi
modelin kullanilacagi tamamen disaridan (OPENROUTER_MODEL ortam degiskeni
ya da --llm-model CLI argumani) belirlenir; bu dosyada hicbir saglayici
adi, model adi ya da API anahtari sabitlenmez.
"""

from __future__ import annotations

from typing import Any

from .config import LLM_CHUNK_MAX_CHARS
from .provider_settings import OpenRouterSettings
from .text_chunker import TextChunker

SYSTEM_PROMPT = """\
You are a copy editor for speech transcripts. Your ONLY tasks are:
1. Fix punctuation and paragraphing.
2. If the text is already split into turns labelled like "SPEAKER_00:", \
"SPEAKER_01:", NEVER change which sentence belongs to which SPEAKER_XX label \
(the original grouping and turn boundaries must stay exactly as they are). If \
the roles are clearly evident from the content (e.g. "Host:" / "Guest:"), you \
may replace the labels with those names, but use ONE AND THE SAME name for \
each SPEAKER_XX number FROM START TO FINISH (e.g. SPEAKER_00 must always stay \
"Guest:", not sometimes "Guest:" and sometimes the person's name). If there \
are no labels and the speakers cannot be clearly told apart from the text, \
skip this step; do not invent speakers.
3. Trim excessively repeated filler words ("uh", "um", "you know") where this \
does not change the meaning.

NEVER summarise, interpret or change the content. Do not change the order or \
grouping of the turns. NEVER change the language of the text: if the input is \
English the output must be entirely English, if it is German it stays German. \
Do not translate even a single sentence.

The text may contain more than one language (e.g. a German passage in the \
middle of an English conversation). Decide the language per sentence, NOT \
for the chunk as a whole: every sentence stays in the language it has in the \
raw text. An English sentence surrounded by German stays English, and a German \
sentence surrounded by English stays German.

Do NOT correct the speakers' grammar, word choice or pronunciation errors, \
especially in passages spoken in a non-native language. The transcript may be \
used as a verbatim record (e.g. for language-level analysis); wrong \
inflections, wrong articles or word order, made-up or borrowed words (e.g. \
"Marketingstrategies", "Rekirements") must stay as they are. Do not rewrite \
sentences to make them more fluent or correct. You may only add punctuation \
and collapse meaningless stutter repetitions ("wir wir wir" -> "wir").

Do not add any structure that is not in the text, such as headings, bullet \
points or comments. This is copy editing, not summarising or translating. \
Return only the edited text, with no extra explanation."""


class LlmEditor:
    """Ham transkripti, uzun metinlerde parcalara bolerek OpenRouter uzerinden duzenler."""

    def __init__(self, model_name: str | None = None, settings: OpenRouterSettings | None = None) -> None:
        self._settings = settings if settings is not None else OpenRouterSettings.from_env()
        self._model_name = model_name or self._settings.model_name
        self._chunker = TextChunker(LLM_CHUNK_MAX_CHARS)
        self._client: Any | None = None

    @property
    def model_name(self) -> str | None:
        return self._model_name

    def is_ready(self) -> bool:
        """API anahtari, taban URL ve model adi (env ya da CLI'dan) tanimli mi?"""
        return bool(self._settings.api_key and self._settings.base_url and self._model_name)

    @property
    def _client_instance(self) -> Any:
        if self._client is None:
            import openai

            self._client = openai.OpenAI(
                api_key=self._settings.api_key,
                base_url=self._settings.base_url,
            )
        return self._client

    def edit(self, raw_text: str) -> str:
        """Ham metni parcalara bolup her parcayi LLM ile duzenler, sonra birlestirir."""
        chunks = self._chunker.split(raw_text)
        edited_chunks = [self._process_chunk(chunk) for chunk in chunks]
        return "\n\n".join(edited_chunks)

    def _process_chunk(self, chunk: str) -> str:
        response = self._client_instance.chat.completions.create(
            model=self._model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": chunk},
            ],
        )
        return response.choices[0].message.content.strip()
