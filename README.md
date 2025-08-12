# Podcast Transcription CLI Tool

Transcribe podcasts and other audio from a URL or local file. Choose between local Whisper, AWS Transcribe, or Google Cloud Speech‑to‑Text. Export transcripts to text, subtitles, and e‑books.

Badges

- CI: ![CI](https://github.com/Caripson/Podcast-Transcription-CLI-Tool/actions/workflows/ci.yml/badge.svg)
- Docs: [![Docs](https://github.com/Caripson/Podcast-Transcription-CLI-Tool/actions/workflows/docs.yml/badge.svg)](https://github.com/Caripson/Podcast-Transcription-CLI-Tool/actions/workflows/docs.yml)
- PyPI: [![PyPI - Test](https://img.shields.io/badge/PyPI-test-brightgreen)](https://pypi.org/project/podcast-transcriber/)

## Features

- Backends: `--service whisper|aws|gcp` (pluggable architecture).
- Inputs: Local files, direct URLs, YouTube (via `yt-dlp`), and podcast RSS feeds (first enclosure).
- Outputs: `--format txt|pdf|epub|mobi|azw|azw3|kfx|srt|vtt|json|md`.
- Export details:
  - PDF: headers/footers, optional cover page, auto‑TOC from segments, custom fonts and page size.
  - EPUB/Kindle: built‑in themes or custom CSS, multi‑chapter from segments, optional cover.
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

Run via Bash wrapper (works without installing):

```bash
./Transcribe_podcast_to_text.sh --url "https://example.com/audio.mp3" --service whisper --output out.txt
```

Run via Python module or console entrypoint:

```bash
python -m podcast_transcriber --url <URL|path> --service <whisper|aws|gcp> --output out.txt
# after install
podcast-transcriber --url <URL|path> --service <whisper|aws|gcp> --output out.txt
```

## CLI Overview

Required

- `--url`: URL, local file, YouTube link, or RSS feed.
- `--service`: `whisper`, `aws`, or `gcp`.

Input and batch

- `--input-file list.txt`: Process many items (one per line). Requires `--output` to be a directory.
- `--config config.toml`: Provide defaults (e.g., `language`, `format`, `title`, etc.).

Output and formats

- `--output`: Output path (or directory for batch); defaults to stdout for `txt`.
- `--format`: `txt`, `pdf`, `epub`, `mobi`, `azw`, `azw3`, `kfx`, `srt`, `vtt`, `json`, `md`.
- `--title`, `--author`: Document metadata.

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

## Notes and Tips

- Kindle formats (`mobi|azw|azw3|kfx`) require Calibre’s `ebook-convert` on PATH.
- YouTube extraction requires `yt-dlp`; otherwise HTTP fallback is used.
- ID3 metadata (title/cover) is read when `mutagen` is installed; RSS feeds use the first `<enclosure>` URL.
- AWS/GCP calls are not made during tests; unit tests mock external services.
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
