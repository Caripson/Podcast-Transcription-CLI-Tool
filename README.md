# Podcast Transcription CLI Tool

Transcribe podcasts and other audio from a URL or local file. Choose between local Whisper, AWS Transcribe, or Google Cloud Speech‑to‑Text. Export transcripts to text, subtitles, and e‑books.

Badges

- CI: ![CI](https://github.com/Caripson/Podcast-Transcription-CLI-Tool/actions/workflows/ci.yml/badge.svg)
- Docs: [![Docs](https://github.com/Caripson/Podcast-Transcription-CLI-Tool/actions/workflows/docs.yml/badge.svg)](https://github.com/Caripson/Podcast-Transcription-CLI-Tool/actions/workflows/docs.yml)
- PyPI: [![PyPI - Test](https://img.shields.io/badge/PyPI-test-brightgreen)](https://pypi.org/project/podcast-transcriber/)
- Smoke: [![Smoke](https://github.com/Caripson/Podcast-Transcription-CLI-Tool/actions/workflows/smoke.yml/badge.svg)](https://github.com/Caripson/Podcast-Transcription-CLI-Tool/actions/workflows/smoke.yml)
- Version: ![Version](https://img.shields.io/badge/version-1.4.2-blue)

## Features

- Backends: `--service whisper|aws|gcp` (pluggable architecture).
- Inputs: Local files, direct URLs, YouTube (via `yt-dlp`), and podcast RSS feeds (first enclosure).
- Outputs: `--format txt|pdf|epub|mobi|azw|azw3|kfx|srt|vtt|json|md`.
  - Plus DOCX via optional extra: `docx`.
- Export details:
  - PDF: headers/footers, optional cover page, auto‑TOC from segments, custom fonts and page size.
- EPUB/Kindle: built‑in themes or custom CSS, multi‑chapter from segments, optional cover.
  - DOCX: simple manuscript export with optional cover page (install `[docx]`).
  - Subtitles: SRT/VTT with timestamps and optional speaker labels.
  - JSON: full transcript + segments + word‑level timings (when available).
- Advanced transcription:
  - Speaker diarization: `--speakers N` for AWS/GCP.
  - Whisper chunking: `--chunk-seconds N` for long audio; `--translate` for English translation.
  - GCP long‑running recognition: `--gcp-longrunning`.
- Batch processing: `--input-file list.txt` to process many items into a directory.
- Caching and robustness: retry/backoff for downloads, `--cache-dir` and `--no-cache` for transcript caching.
- Post‑processing: `--normalize` (whitespace/paragraphs), `--summarize N` (naive summary).

## Requirements

- Python 3.9+
- Core dependency: `requests`
- Optional extras (installed only if you use the feature):
  - Whisper: `openai-whisper`, `ffmpeg`
  - AWS: `boto3` + AWS credentials; env var `AWS_TRANSCRIBE_S3_BUCKET`
  - GCP: `google-cloud-speech` + credentials (`GOOGLE_APPLICATION_CREDENTIALS`)
  - PDF: `fpdf2`
  - EPUB/Kindle: `ebooklib` (and Calibre’s `ebook-convert` for Kindle formats)
  - YouTube: `yt-dlp`
  - ID3 cover/title: `mutagen` (optional)

Minimal core-only install (one-liner):

```bash
pip install -e .
```

Extras quick reference:

| Feature | Extra | Install command | Notes |
|---|---|---|---|
| Whisper (local) | `whisper` | `pip install -e .[whisper]` | Requires `ffmpeg` on PATH |
| AWS Transcribe | `aws` | `pip install -e .[aws]` | Needs AWS creds + `AWS_TRANSCRIBE_S3_BUCKET` |
| GCP Speech-to-Text | `gcp` | `pip install -e .[gcp]` | Needs `GOOGLE_APPLICATION_CREDENTIALS` |
| Export formats (PDF/EPUB/Kindle) | `export` | `pip install -e .[export]` | Kindle formats require Calibre `ebook-convert` |
| Developer tools | `dev` | `pip install -e .[dev]` | Includes pytest, etc. |
| Docs | `docs` | `pip install -e .[docs]` | MkDocs + Material |

## Installation

Local (editable) install for development:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Optional extras examples:

```bash
pip install -e .[whisper]
pip install -e .[aws]
pip install -e .[gcp]
pip install -e .[export]
```

## Quickstart

Run via Bash wrapper from source (no package install of this project required):

Note: You still need Python dependencies available in your environment. At minimum, core runs require `requests`. For Whisper/AWS/GCP backends or exports, install the corresponding extras. See Installation below.

```bash
./Transcribe_podcast_to_text.sh --url "https://example.com/audio.mp3" --service whisper --output out.txt
```

Run via Python module or console entrypoint (requires installing the package and its deps):

```bash
python -m podcast_transcriber --url <URL|path> --service <whisper|aws|gcp> --output out.txt
# after install
podcast-transcriber --url <URL|path> --service <whisper|aws|gcp> --output out.txt
```

## Orchestrator CLI (beta)

High‑level pipeline for “ingest → process → send to Kindle” and weekly digests.

- Install extras: `pip install -e .[orchestrator,ingest,templates]` (and optionally `[scheduler,nlp]`).

Subcommands:

- `podcast-cli ingest --config config.yml` — Discover new episodes and create a job.
- `podcast-cli process --job-id <id>` — Transcribe and build EPUB for a job.
  - Ad‑hoc semantic segmentation: add `--semantic` to this command to override YAML.
- `podcast-cli send --job-id <id>` — Email EPUBs to your Kindle address.
- `podcast-cli run --config config.yml` — Run ingest → process → send in one go.
- `podcast-cli digest --feed <name> --weekly` — Build a weekly digest EPUB.

Config (YAML) example:

```yaml
feeds:
  - name: myfeed
    url: https://example.com/podcast.rss
  - name: altfeed-by-id
    podcastindex_feedid: "123456"
  - name: altfeed-by-guid
    podcast_guid: "urn:uuid:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
service: whisper
quality: standard  # quick|standard|premium
language: sv-SE
author: Your Name
output_dir: ./out
kindle:
  to_email: your_name@kindle.com
  from_email: sender@example.com
smtp:
  host: smtp.example.com
  port: 587
  user: smtp-user
  # password set via env only, e.g. SMTP_PASS

# NLP options (optional)
nlp:
  semantic: true      # enable semantic topic segmentation (requires [nlp] extra)
  takeaways: true     # add a simple "Key takeaways" section

# Markdown output (optional)
emit_markdown: true
markdown_template: ./path/to/ebook.md.j2  # omit to use built-in template

Templating and themes:

- The built-in template defines blocks you can override: `front_matter`, `title_page`, `preface`, `content`, and `appendix`.
- Create your own Jinja2 theme that `{% extends %}` the base template at `src/podcast_transcriber/templates/ebook.md.j2`.
- An example template is provided at `examples/templates/ebook_theme_minimal.md.j2`.

Topics and takeaways in Markdown:

- When NLP is enabled (`nlp.semantic: true` and/or `podcast-cli process --semantic`), the Markdown includes a "Topics" section listing chapter titles derived from segmentation.
- When `nlp.takeaways: true`, the Markdown also includes a "Key Takeaways" section with 3–5 concise bullets. If spaCy is installed, noun chunks are used; otherwise a heuristic is applied.
```

Secrets policy: Store SMTP password and API keys in environment variables (e.g. `SMTP_PASS`, cloud provider keys). Ensure your Kindle address whitelists your sender.

Scheduling (optional):

- Install: `pip install -e .[scheduler,orchestrator,ingest]`
- Run once: `podcast-auto-run --config config.yml --once`
- Run hourly/daily: `podcast-auto-run --config config.yml --interval hourly|daily`

Topic segmentation (optional):

- Install: `pip install -e .[nlp]`
- The CLI uses a simple fallback if embeddings are unavailable; with embeddings, segments are formed by semantic similarity dips and “key takeaways” are extracted heuristically.

Bilingual EPUB (premium idea):

- Set `bilingual: true` in config to attempt “Original” + “Translated” sections when using Whisper (translation is toggled internally). If translation fails, it falls back to original only.

## CLI Overview

Required

- `--url`: URL, local file, YouTube link, or RSS feed.
- `--service`: `whisper`, `aws`, or `gcp`.

Input and batch

- `--input-file list.txt`: Process many items (one per line). Requires `--output` to be a directory.
- `--config config.toml`: Provide defaults (e.g., `language`, `format`, `title`, etc.). If omitted, a config is auto-discovered at `~/.config/podcast-transcriber/config.toml` (or `$XDG_CONFIG_HOME/podcast-transcriber/config.toml`).

Output and formats

- `--output`: Output path (or directory for batch); defaults to stdout for `txt`.
- `--format`: `txt`, `pdf`, `epub`, `mobi`, `azw`, `azw3`, `kfx`, `srt`, `vtt`, `json`, `md`.
- `--title`, `--author`: Document metadata.

Interactive mode

- `--interactive`: Guided prompts for `--url`, `--service`, `--format`, `--output`, and optional `--language`. Great for first-time users.

Whisper options

- `--whisper-model base|small|medium|large`
- `--chunk-seconds N`: Split long audio into chunks.
- `--translate`: Whisper translate task (to English).
- `--language`: Hint language code (e.g., `sv`, `en-US`).

AWS options

- `--aws-bucket`, `--aws-region`
- `--auto-language` and `--aws-language-options sv-SE,en-US`
- `--speakers N`: Enable speaker labels.
- `--aws-keep`: Keep uploaded S3 object after job completes.

GCP options

- `--gcp-alt-languages en-US,nb-NO`
- `--speakers N`: Enable diarization.
- `--gcp-longrunning`: Use long running recognition for long audio.

PDF/EPUB options

- PDF: `--pdf-page-size A4|Letter`, `--pdf-orientation portrait|landscape`, `--pdf-margin <mm>`, `--pdf-font Arial`, `--pdf-font-size 12`, `--pdf-font-file path.ttf`, `--pdf-cover-fullpage`, `--pdf-first-page-cover-only`.
- EPUB/Kindle: `--epub-css-file style.css`, `--epub-theme minimal|reader|classic|dark` or `custom:/path.css`, `--cover-image cover.jpg`, `--auto-toc` (creates a simple TOC from segments; PDF also adds header/footer based on title/author).

Caching and logging

- `--cache-dir /path/to/cache`, `--no-cache`
- `--verbose`, `--quiet`

Post‑processing

- `--normalize`: Normalize whitespace/paragraphs
- `--summarize N`: Naive summary (first N sentences)

## Examples

Local Whisper to TXT

```bash
./Transcribe_podcast_to_text.sh \
  --url "https://example.com/podcast.mp3" \
  --service whisper \
  --output transcript.txt
```

AWS with language auto‑detect restricted to Swedish or English (US)

```bash
export AWS_TRANSCRIBE_S3_BUCKET=my-bucket
./Transcribe_podcast_to_text.sh \
  --url "./examples/tone.wav" \
  --service aws \
  --auto-language \
  --aws-language-options sv-SE,en-US \
  --aws-region eu-north-1 \
  --output transcript.txt
```

GCP with alternative languages

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds.json
./Transcribe_podcast_to_text.sh \
  --url "./examples/tone.wav" \
  --service gcp \
  --language sv-SE \
  --gcp-alt-languages en-US,nb-NO \
  --output transcript.txt
```

SRT/VTT with speaker labels (AWS)

```bash
./Transcribe_podcast_to_text.sh \
  --url ./episode.wav \
  --service aws \
  --speakers 2 \
  --format srt \
  --output episode.srt
```

Whisper chunked VTT for a long file

```bash
./Transcribe_podcast_to_text.sh \
  --url ./long.mp3 \
  --service whisper \
  --chunk-seconds 600 \
  --format vtt \
  --output long.vtt
```

EPUB with theme and auto TOC

```bash
./Transcribe_podcast_to_text.sh \
  --url ./episode.mp3 \
  --service whisper \
  --format epub \
  --epub-theme reader \
  --auto-toc \
  --output episode.epub
```

Batch processing to a directory

```bash
cat > list.txt <<EOF
https://example.com/ep1.mp3
https://example.com/ep2.mp3
EOF

./Transcribe_podcast_to_text.sh \
  --service whisper \
  --input-file list.txt \
  --format md \
--output ./out_dir
```

KDP pipeline (EPUB) for a single episode

```bash
./Transcribe_podcast_to_text.sh \
  --url ./episode.mp3 \
  --service whisper \
  --kdp \
  --title "Podcasten: Säsong 1 – Avsnitt 1" \
  --author "Ditt Namn" \
  --description "En transkriberad version av avsnittet..." \
  --keywords "podcast, svensk, teknik" \
  --cover-image ./cover.jpg \
  --output ./episode.epub
```

KDP book from multiple episodes (combine into one EPUB)

```bash
cat > episodes.txt <<EOF
https://example.com/ep1.mp3
https://example.com/ep2.mp3
EOF

./Transcribe_podcast_to_text.sh \
  --service whisper \
  --input-file episodes.txt \
  --combine-into ./podcast-book.epub \
  --kdp \
  --title "Min Podcast – Volym 1" \
  --author "Ditt Namn" \
  --description "Transkriptioner av säsongens bästa avsnitt" \
  --keywords "podcast, svenska, samhälle"
```

DOCX manuscript (requires extra)

```bash
pip install -e .[docx]
./Transcribe_podcast_to_text.sh \
  --url ./episode.mp3 \
  --service whisper \
  --format docx \
  --title "Avsnitt 1" \
  --author "Ditt Namn" \
  --output ./episode.docx
```

## Notes and Tips

- Kindle formats (`mobi|azw|azw3|kfx`) require Calibre’s `ebook-convert` on PATH.
- YouTube extraction requires `yt-dlp`; otherwise HTTP fallback is used.
- ID3 metadata (title/cover) is read when `mutagen` is installed; RSS feeds use the first `<enclosure>` URL.
- AWS/GCP calls are not made during tests; unit tests mock external services.

## Example Plugin + Smoke Test

- Example plugin: `examples/plugin_echo/` registers an `echo` service via entry points. Install with `pip install -e examples/plugin_echo` and use `--service echo`.
- Smoke test script: `scripts/smoke.sh` automates a basic run including plugin discovery and JSON export. Make it executable and run:

```
chmod +x scripts/smoke.sh
./scripts/smoke.sh
```

## JSON Export Schema

When using `--format json`, the file includes additional metadata when available from the downloader (ID3, yt-dlp, etc.).

- Keys:
  - `title`: Document title.
  - `author`: Document author (if provided).
  - `text`: Full transcript.
  - `segments`: List of coalesced segments with `start`, `end`, `text`, and optional `speaker`.
  - `words`: Optional word-level timings when the backend provides them.
  - `source`: Optional object with downloader metadata, for example:
    - `source_url`: Original URL.
    - `local_path`: Local file path used for transcription.
    - `id3_title`, `id3_artist`: From ID3 tags if present.
    - `source_title`: From yt-dlp (e.g., video title).
    - `source_uploader`: From yt-dlp (e.g., channel/uploader).
    - `cover_url`: Thumbnail URL when available.

## Plugins: Add Your Own Service

You can ship third-party services as plugins via Python entry points. Register the entry point group `podcast_transcriber.services` in your package and expose either a subclass of `TranscriptionService` or a zero-argument factory that returns one.

pyproject.toml (in your plugin):

```
[project.entry-points."podcast_transcriber.services"]
myservice = "my_package.my_module:MyService"
```

Your service must implement the `TranscriptionService` interface (see `src/podcast_transcriber/services/base.py`). Once installed, it appears in `--service` choices and in `--interactive` selection.
- Troubleshooting: see `docs/troubleshooting.md` for common issues and fixes.

### Quick Troubleshooting

- ffmpeg (Whisper): install via Homebrew (`brew install ffmpeg`) or apt (`sudo apt-get install -y ffmpeg`).
- ebook-convert (Kindle): install Calibre and ensure `ebook-convert` is on PATH (macOS: `brew install --cask calibre`).
- yt-dlp (YouTube): `pipx install yt-dlp` or `pip install yt-dlp` and ensure it’s on PATH.
- mutagen (ID3 title/cover): `pip install mutagen` to auto‑read MP3 metadata.
- Credentials (AWS/GCP): `pip install boto3` and set `AWS_TRANSCRIBE_S3_BUCKET`; `pip install google-cloud-speech` and set `GOOGLE_APPLICATION_CREDENTIALS`.

## Development

- Run tests with `pytest` (external calls are mocked):
  - `pytest -q`
- Layout:
  - `src/podcast_transcriber/` – core logic and services
  - `tests/` – unit tests with mocks
  - `docs/` – MkDocs documentation
  - `examples/` – `generate_tone.py` creates a tiny WAV demo

## CI/CD

- GitHub Actions runs `pytest` on push/PR (matrix across Python versions and optional extras).
- MkDocs builds and publishes docs to GitHub Pages (see `.github/workflows/docs.yml`).

## Author

Developed by Johan Caripson.

## License

MIT (see LICENSE)

## 📚 Examples

Whisper (local):

```bash
./Transcribe_podcast_to_text.sh \
  --url "https://example.com/podcast.mp3" \
  --service whisper \
  --output transcript.txt
```

AWS with language auto‑detect restricted to Swedish or English (US):

```bash
export AWS_TRANSCRIBE_S3_BUCKET=my-bucket
./Transcribe_podcast_to_text.sh \
  --url "./examples/tone.wav" \
  --service aws \
  --auto-language \
  --aws-language-options sv-SE,en-US \
  --aws-region eu-north-1 \
  --output transcript.txt
```

GCP with alternative languages:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds.json
./Transcribe_podcast_to_text.sh \
  --url "./examples/tone.wav" \
  --service gcp \
  --language sv-SE \
  --gcp-alt-languages en-US,nb-NO \
  --output transcript.txt
```

Kindle formats note: `--format mobi|azw|azw3|kfx` requires Calibre’s `ebook-convert` on PATH.

Utility

- `--credits`: Print maintainer credits and exit.
