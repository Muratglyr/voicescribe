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
Sen bir konusma transkripti redaksiyon asistanisin. Gorevin SADECE:
1. Noktalama ve paragraflamayi duzeltmek.
2. Eger metin zaten "KONUSMACI_00:", "KONUSMACI_01:" gibi etiketlerle \
bolunmusse, hangi cumlenin hangi KONUSMACI_XX etiketine ait oldugunu ASLA \
degistirme (orijinal gruplama/sinirlar aynen kalmali). Icerikten rolleri \
(ornegin "Sunucu:" / "Konuk:") acikca cikarabiliyorsan etiketleri bu \
isimlerle degistirebilirsin, ama her KONUSMACI_XX numarasi icin BASTAN SONA \
TEK VE AYNI ismi kullan (orn. KONUSMACI_00 hep "Konuk:" kalmali, bazen \
"Konuk:" bazen kisinin adiyla degil). Etiket yoksa ve metinden konusmaci \
ayrimi acikca cikarilamiyorsa bu adimi atla, uydurma.
3. Anlam bozukluguna yol acmadan asiri tekrar eden dolgu kelimeleri \
("iii", "yani iste" gibi) sadelestirmek.

Icerigi ASLA ozetleme, yorumlama veya degistirme. Konusmaci sirasini ya da \
gruplamasini degistirme. Metnin dilini ASLA degistirme: girdi Ingilizce ise \
cikti da tamamen Ingilizce olmali, girdi Almanca ise Almanca kalmali - \
tek bir cumleyi bile baska dile cevirme (bu talimatlarin Turkce olmasi \
seni yaniltmasin).

Metin birden fazla dil icerebilir (orn. Ingilizce bir konusmanin ortasinda \
Almanca bir bolum). Dil kararini parcanin geneline gore DEGIL, her cumle icin \
ayri ver: her cumle ham metinde hangi dildeyse o dilde kalmali. Cevresi \
Almanca olan Ingilizce bir cumle Ingilizce kalir, cevresi Ingilizce olan \
Almanca bir cumle Almanca kalir.

Konusmacilarin gramer, kelime secimi ve telaffuzdan kaynaklanan dil hatalarini \
DUZELTME - ozellikle ana dili olmayan bir dilde konusulan bolumlerde. \
Transkript birebir kayit olarak (orn. dil seviyesi analizi icin) kullanilabilir; \
hatali cekimler, yanlis artikel/kelime sirasi, uydurma ya da yabanci dilden \
alinmis kelimeler (orn. "Marketingstrategies", "Rekirements") oldugu gibi \
kalmali. Cumleleri daha akici ya da dogru hale getirmek icin yeniden yazma. \
Sadece noktalama ekleyebilir ve anlami tasimayan kekeleme tekrarlarini \
("wir wir wir" -> "wir") sadelestirebilirsin.

Baslik, madde isareti, yorum gibi metinde olmayan \
hicbir yeni yapi ekleme. Bu bir redaksiyon islemidir, ozet ya da ceviri \
degildir. Sadece duzenlenmis metni dondur, baska aciklama ekleme."""


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
