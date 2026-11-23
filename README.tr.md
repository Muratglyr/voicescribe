# voicescribe

[English](README.md) | **Türkçe**

Toplantı, podcast, röportaj, ders, sesli not gibi her türlü konuşma kaydının
ses dosyalarını (`.m4a`, `.mp3`, `.wav`, `.mp4`, `.aac`, `.ogg`) alıp:

1. OpenAI Whisper modeliyle **tamamen yerel olarak** (internete ses göndermeden)
   metne çevirir (varsayılan dil İngilizce; `--dil` ile değiştirilebilir),
2. İsteğe bağlı olarak (`--konusmaci-ayir`) ses dosyasındaki farklı konuşmacıları
   Deepgram üzerinden (buluta gönderip) ayırt eder; bu modda transkripsiyon da
   yerel Whisper yerine doğrudan Deepgram'dan alınır,
3. İsteğe bağlı olarak (`--duzenle`) ham transkripti OpenRouter üzerinden bir LLM
   ile noktalanmış, paragraflanmış, okunabilir bir dökümana dönüştürür.

## Mimari

Kod, her biri tek bir sorumluluğa sahip sınıflara bölünmüş, modüler bir
yapıdadır (`voicescribe/` paketi). Modül/sınıf/fonksiyon isimleri
İngilizce, kod içi yorumlar ve kullanıcıya gösterilen mesajlar (CLI
bayrakları dahil) Türkçedir:

| Modül | Sınıf | Sorumluluk |
|---|---|---|
| `config.py` | `AppConfig` | Çalışma zamanı ayarlarını taşıyan değişmez veri sınıfı |
| `exceptions.py` | `TranscriptError` ve alt sınıfları | Proje içi hata hiyerarşisi |
| `provider_settings.py` | `OpenRouterSettings`, `DeepgramSettings` | Dış servis ayarlarını **sadece** ortam değişkenlerinden okuma |
| `file_finder.py` | `AudioFileFinder` | Girdi dosya/klasöründen desteklenen ses dosyalarını bulma |
| `ffmpeg_checker.py` | `FFmpegChecker` | Sistemde ffmpeg kurulu mu, doğrulama |
| `transcriber.py` | `WhisperTranscriber` | Whisper modelini yükleyip ses dosyasını zaman damgalı segmentlere çevirme (yerel, `--konusmaci-ayir` yokken) |
| `deepgram_diarized_transcriber.py` | `DeepgramDiarizedTranscriber` | Deepgram üzerinden tek istekte transkript + konuşmacı etiketli metni alma (`--konusmaci-ayir` ile) |
| `text_chunker.py` | `TextChunker` | Uzun metni LLM bağlam sınırına uygun parçalara bölme |
| `llm_editor.py` | `LlmEditor` | Ham metni OpenRouter üzerinden bir LLM ile redakte etme |
| `pipeline.py` | `TranscriptPipeline` | Yukarıdaki sınıfları bir araya getiren orkestratör |
| `cli.py` | — | Argüman ayrıştırma, `.env` yükleme ve giriş noktası |

**Konuşmacı ayrımı nasıl çalışır?** `--konusmaci-ayir` verildiğinde yerel
Whisper adımı hiç çalışmaz; ses dosyası doğrudan Deepgram'ın `nova-3`
modeline gönderilir ve tek istekte hem transkript hem de kelime/cümle
bazında konuşmacı numarası (`speaker: 0`, `speaker: 1`, ...) döner.
`DeepgramDiarizedTranscriber`, ardışık aynı-konuşmacılı cümleleri birleştirip
metne `KONUSMACI_00: ...` / `KONUSMACI_01: ...` etiketlerini deterministik
olarak ekler (LLM tahmini değil). `--konusmaci-ayir` verilmediğinde ise
transkripsiyon eskisi gibi tamamen yerel Whisper ile yapılır.

**Hiçbir sağlayıcı/model adı, API anahtarı ya da servis adresi Python
kaynak kodunda sabit (hardcoded) yazılmaz.** Tüm bu değerler `.env`
dosyasından okunur (bkz. "Ortam Değişkenleri" bölümü); CLI argümanları
verildiğinde ortam değişkenlerini geçersiz kılar. Ağır bağımlılıklar
(`whisper`, `openai`, `requests`) yalnızca gerçekten kullanıldıkları
anda içe aktarılır (tembel/lazy yükleme). Bu sayede `AudioFileFinder`,
`TextChunker`, `DeepgramDiarizedTranscriber` gibi sınıflar bu ağır paketler
kurulu olmasa bile test edilebilir.

## Kurulum

### 1. Python bağımlılıkları

```bash
pip install -r requirements.txt
```

Testleri çalıştırmak için (opsiyonel):

```bash
pip install -r requirements-dev.txt
```

### 2. ffmpeg

Whisper, ses dosyalarını işleyebilmek için sisteminizde **ffmpeg** kurulu
olmasını gerektirir.

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Windows (winget veya Chocolatey):**
```powershell
winget install ffmpeg
# veya
choco install ffmpeg
```
Kurulumdan sonra `ffmpeg`'in PATH'e eklendiğinden emin olun (yeni bir
terminal açıp `ffmpeg -version` ile kontrol edebilirsiniz).

**Linux (Debian/Ubuntu):**
```bash
sudo apt update && sudo apt install ffmpeg
```

### 3. (Opsiyonel) NVIDIA GPU ile hızlandırma

`requirements.txt` varsayılan olarak PyPI'dan **CPU-only** PyTorch kurar.
NVIDIA GPU'nuz varsa yerel Whisper adımı (yani `--konusmaci-ayir`
*kullanılmadığı* durumlar) için ciddi ölçüde hız kazandırır — örneğin 21
dakikalık bir kayıt CPU'da ~11 dakika sürerken, GPU'da (RTX 5060, `small`
modeliyle) ~2.5 dakikaya iniyor. (`--konusmaci-ayir` kullanıldığında
transkripsiyon Deepgram'da bulutta yapıldığı için bu adım GPU'dan
etkilenmez.) Kurulum:

```powershell
# Once requirements.txt'teki CPU surumunu kaldirin
pip uninstall torch torchaudio -y
# Sonra CUDA surumunu kurun (GPU'nuza uygun index'i secin, ornek CUDA 12.8 icin):
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
```

Doğru CUDA sürümünü seçmek için `nvidia-smi` çıktısındaki sürücü sürümüne
bakıp [pytorch.org/get-started/locally](https://pytorch.org/get-started/locally/)
sayfasındaki uyumluluk tablosunu kullanın. Kurulumdan sonra doğrulayın:

```powershell
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

`True` ve GPU adınızı görüyorsanız hazırsınız — kod tarafında ekstra bir
ayar gerekmez, Whisper GPU varsa otomatik kullanır.

### 4. Ortam değişkenleri (.env) — `--duzenle` ve `--konusmaci-ayir` için

`.env.example` dosyasını `.env` olarak kopyalayın; program başlarken bu
dosyayı otomatik olarak yükler (`python-dotenv`). Elle `export` etmenize
gerek yoktur.

**`--duzenle` için (OpenRouter):**
1. [openrouter.ai](https://openrouter.ai) üzerinden bir hesap açıp API
   anahtarı alın, `OPENROUTER_API_KEY` değerine yazın.
2. `OPENROUTER_MODEL` değerine kullanmak istediğiniz model kimliğini yazın
   (örn. `anthropic/claude-sonnet-5`, `anthropic/claude-haiku-4.5`,
   `openai/gpt-4o-mini`). Güncel model listesi ve fiyatlar:
   [openrouter.ai/models](https://openrouter.ai/models).
3. `OPENROUTER_BASE_URL` zaten dolu gelir (`https://openrouter.ai/api/v1`),
   değiştirmenize gerek yok.

Bu üç değerden biri eksikse program çökmez; `--duzenle` adımını atlayıp
sadece ham transkripti üretir ve terminale bir uyarı basar.

**`--konusmaci-ayir` için (Deepgram):**
1. [console.deepgram.com](https://console.deepgram.com/) üzerinden bir hesap
   açıp API anahtarı alın, `DEEPGRAM_API_KEY` değerine yazın.
2. `DEEPGRAM_MODEL` zaten `nova-3` olarak dolu gelir, değiştirmenize gerek
   yok.

Ücretlidir, kullanım bazlı faturalandırılır (bu yazı itibarıyla ~$0,0043/dk,
20 dakikalık bir kayıt için ~$0,09). `DEEPGRAM_API_KEY` tanımlı değilse
`--konusmaci-ayir` adımı atlanır, transkript yerel Whisper ile ve konuşmacı
etiketi olmadan üretilir. Güncel fiyatlandırma:
[deepgram.com/pricing](https://deepgram.com/pricing).

## Kullanım

```bash
python transkript.py "kayit.m4a"
python transkript.py "kayitlar_klasoru/" --klasor
python transkript.py "kayit.m4a" --model medium
python transkript.py "kayit.m4a" --konusmaci-ayir
python transkript.py "kayit.m4a" --duzenle
python transkript.py "kayit.m4a" --duzenle --llm-model openai/gpt-4o-mini
python transkript.py "kayitlar_klasoru/" --klasor --konusmaci-ayir --duzenle --cikti ./ciktilar
```

### CLI Argümanları

| Argüman | Açıklama | Varsayılan |
|---|---|---|
| `girdi` | Ses dosyası ya da (`--klasor` ile) klasör yolu | — (zorunlu) |
| `--klasor` | Girdinin bir klasör olduğunu belirtir, içindeki tüm desteklenen dosyalar işlenir | kapalı |
| `--model` | Whisper model boyutu: `tiny`, `base`, `small`, `medium`, `large` | `medium` |
| `--dil` | Transkript dili | `en` |
| `--cikti` | Çıktıların yazılacağı klasör | `./ciktilar` |
| `--konusmaci-ayir` | Konuşmacıları Deepgram ile ayırt eder (transkripsiyon da Deepgram'dan alınır; `DEEPGRAM_API_KEY` gerekir) | kapalı |
| `--duzenle` | Ham transkripti OpenRouter üzerinden bir LLM ile düzenler | kapalı |
| `--llm-model` | `--duzenle` için OpenRouter model kimliği | `OPENROUTER_MODEL` ortam değişkeni |

`--llm-model` verilmezse `.env` dosyasındaki `OPENROUTER_MODEL` kullanılır;
ikisi de tanımlı değilse `--duzenle` adımı atlanır. Kod içinde hiçbir
model adı sabitlenmemiştir.

`--konusmaci-ayir` verildiğinde transkripsiyon Deepgram'dan alındığı için
`--model` (Whisper model boyutu) o çalıştırmada göz ardı edilir; `--dil`
ise Deepgram'a da iletilmeye devam eder.

### Whisper Model Boyutları

| Model | Hız | Doğruluk | Not |
|---|---|---|---|
| `tiny` | Çok hızlı | Düşük | Hızlı ön izleme için |
| `base` | Hızlı | Orta-düşük | |
| `small` | Orta | Orta-iyi | Düşük kaliteli/gürültülü kayıtlarda halüsinasyon riski yüksek |
| `medium` | Yavaş | İyi | Varsayılan; gürültülü/düşük kaliteli kayıtlarda `small`'a göre belirgin daha az halüsinasyon |
| `large` | Çok yavaş | En iyi | Yüksek doğruluk gerektiğinde, güçlü donanımda |

## Veri Gizliliği

Varsayılan olarak (yani `--konusmaci-ayir` **kullanılmadığında**) Whisper
transkripsiyonu **tamamen yerel** çalışır; ses dosyanız hiçbir zaman
internete gönderilmez.

`--konusmaci-ayir` kullanıldığında ise ses dosyasının tamamı, transkripsiyon
+ konuşmacı ayrımı için Deepgram'a gönderilir — bu adımda ses artık yerelde
kalmaz. Kayıtlar gerçek kişilere ait olabileceğinden, bu bayrağı
kullanmadan önce ilgili kişilerin kaydın bir bulut hizmetine gönderileceğinden
haberdar olduğundan emin olun.

`--duzenle` bayrağı kullanıldığında ise, o ana kadar üretilmiş **metin**
transkripti (ses değil) OpenRouter üzerinden seçtiğiniz LLM sağlayıcısına
gönderilir.

## Testleri Çalıştırma

```bash
pip install -r requirements-dev.txt
pytest
```
