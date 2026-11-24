# voicescribe

[English](README.md) | **Türkçe**

Toplantı, podcast, röportaj, ders ya da sesli not gibi her türlü kayıt için
yapılandırılabilir bir speech-to-text pipeline'ı.

- **Yerel transkripsiyon:** OpenAI Whisper ile çalışır, ses bilgisayarınızdan çıkmaz.
- **Konuşmacı ayrımı:** Deepgram ile yapılır (`SPEAKER_00`, `SPEAKER_01`, ...).
- **LLM ile düzenleme:** OpenAI uyumlu herhangi bir API üzerinden çalışır (varsayılan:
  OpenRouter). Sadece noktalama ve paragrafları düzeltir; özetlemez, çevirmez ve
  söylenenleri değiştirmez.
- **Konuşmacı tutarlılık kontrolü:** LLM bir konuşmayı yanlış kişiye atarsa uyarır.
- **Dışa aktarma:** Düz metin, yapılandırılmış JSON ya da SRT altyazı olarak.
- **Tamamen config tabanlı:** Motorlar, modeller, prompt'lar, etiketler, çıktı
  formatları ve mesajlar kodda değil, TOML ve Markdown dosyalarında tutulur.

## Kurulum

```bash
pip install "voicescribe[all] @ git+https://github.com/Muratglyr/voicescribe"
```

Sadece ihtiyacınız olanı kurmak için extra'ları kullanabilirsiniz: `whisper` (yerel),
`deepgram` (bulutta konuşmacı ayrımı), `llm` (düzenleme). Whisper için sistemde
[ffmpeg](https://ffmpeg.org/) kurulu olmalıdır.

## Kullanım

```bash
voicescribe toplanti.m4a                                 # yerel Whisper -> transcripts/toplanti.txt
voicescribe toplanti.m4a --format srt --format json      # altyazı + yapılandırılmış çıktı
voicescribe roportaj.m4a --diarize --edit                # konuşmacılar + LLM düzenleme
voicescribe kayitlar/ --folder --language tr             # bir klasörün tamamı, Türkçe
voicescribe toplanti.m4a --config ekip.toml              # kendi yapılandırmanız
```

## Yapılandırma

Tüm ayarların varsayılan değerleri
[`src/voicescribe/resources/defaults.toml`](src/voicescribe/resources/defaults.toml)
dosyasında durur. Sadece değiştirmek istediklerinizi yazmanız yeterlidir. Katmanlar
şu sırayla uygulanır, sonraki öncekini ezer:

1. Paketle gelen varsayılanlar
2. Kullanıcı TOML dosyası: `./voicescribe.toml` ya da `--config` ile verilen dosya
   (bkz. [`voicescribe.example.toml`](voicescribe.example.toml))
3. Ortam değişkenleri: `VOICESCRIBE__<BOLUM>__<ANAHTAR>`
4. Komut satırı bayrakları

Arayüzü Türkçe kullanmak için config dosyanıza `[app]` altında `locale = "tr"` yazın.

**Gizli anahtarlar** hiçbir zaman config dosyalarına yazılmaz. Config yalnızca
anahtarın hangi ortam değişkeninde durduğunu belirtir; anahtarların kendisi `.env`
dosyasında tutulur. **Prompt'lar** `resources/prompts/` altındaki Markdown dosyalarıdır;
kendi prompt'unuzu `editing.llm.system_prompt` ile verebilirsiniz.

Mimari, kütüphane olarak kullanım ve geliştirme ortamı için
[İngilizce README](README.md)'ye bakın.

## Yazılar

- [Your LLM Is Quietly Changing Who Said What](https://medium.com/@muratglyr33/your-llm-is-quietly-changing-who-said-what-53708eb9dea5) (İngilizce): konuşmacı tutarlılık kontrolünün nasıl çalıştığı, neden gerektiği ve sınırları.

## Lisans

[MIT](LICENSE)
