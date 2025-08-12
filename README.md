# 🎧 Podcast Transcription CLI Tool (MVP v1)

Command‑line tool to transcribe podcasts and other audio from a URL or file path. Pluggable backends: local Whisper, AWS Transcribe, or Google Cloud Speech‑to‑Text.

## 🚀 Quickstart

- Requirements: Python 3.9+, `requests`. Cloud/backends are optional and only needed if you use them.
- Optional local install:
  - `pip install -e .`
- Run via Bash script:
  - `./Transcribe_podcast_to_text.sh --url "https://example.com/audio.mp3" --service whisper --output out.txt`
- Or via Python entrypoint:
  - `python -m podcast_transcriber --url <URL|path> --service <whisper|aws|gcp> --output out.txt`

## ✨ Features

- Choose backend via `--service`: `whisper`, `aws`, `gcp`.
- Download from URL or use a local file path.
- Write transcript to `--output` or to stdout.
- Easy to add new providers via a common service interface.
- Export to e-book formats: `--format` supports `txt`, `pdf`, `epub`, `mobi`, `azw`, `azw3`, `kfx` (+ `--title`, `--author`).
  - EPUB/Kindle options: `--cover-image` (auto-resized if Pillow is installed), `--epub-css-file` for basic styling.
  - Built-in EPUB themes: `--epub-theme minimal|reader|classic|dark` inject a bundled CSS.
  - PDF layout options: `--pdf-page-size A4|Letter`, `--pdf-margin <mm>`, `--pdf-orientation portrait|landscape`.
  - PDF font embedding: `--pdf-font-file /path/to/font.ttf` for Unicode text.
  - PDF cover options: `--pdf-cover-fullpage` (dedicated cover page), `--pdf-first-page-cover-only` (start transcript next page).

### ☁️ Minimal cloud integrations (MVP)

- AWS Transcribe:
  - Requires: `boto3`, AWS credentials, and `AWS_TRANSCRIBE_S3_BUCKET` set.
  - Flow: Upload to S3, start job, poll for completion, fetch transcript.
  - CLI flags: `--aws-bucket`, `--aws-region`, `--auto-language` (enables IdentifyLanguage when no `--language`).
  - Optional: `--aws-language-options sv-SE,en-US` to limit detection to specific languages.
- GCP Speech‑to‑Text:
  - Requires: `google-cloud-speech` and GCP credentials.
  - Flow: Read file bytes and call synchronous `recognize()`.
  - CLI flags: `--gcp-alt-languages` (comma‑separated alternatives used if provided).

## 🧪 Development

- Run tests with `pytest` (external calls are mocked):
  - `pytest -q`
- Layout:
  - `src/podcast_transcriber/` – core logic and services
  - `tests/` – unit tests with mocks
  - `docs/` – MkDocs documentation
  - `examples/` – `generate_tone.py` creates a tiny WAV demo

## 🤖 CI/CD

- GitHub Actions runs `pytest` on push/PR (matrix across Python versions and optional extras).
- MkDocs builds and publishes docs to GitHub Pages (see `.github/workflows/docs.yml`).

## 📄 License

MIT

---

Badges:

- CI: ![CI](https://github.com/Caripson/Podcast-Transcription-CLI-Tool/actions/workflows/ci.yml/badge.svg)
- Docs: [![Docs](https://github.com/Caripson/Podcast-Transcription-CLI-Tool/actions/workflows/docs.yml/badge.svg)](https://github.com/Caripson/Podcast-Transcription-CLI-Tool/actions/workflows/docs.yml)
- Docs Preview: available on pull requests via workflow artifacts
- PyPI: ![PyPI - Coming Soon](https://img.shields.io/badge/PyPI-coming--soon-lightgrey)

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
