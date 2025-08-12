# Dependencies & Extras

This tool runs from source or as an installed package. You need Python
dependencies available in your environment even when using the Bash wrapper.

- Python: 3.9+
- Core: `requests` (HTTP, RSS, cover fetching)
- Optional extras (install only what you need):
  - Whisper (local): `openai-whisper`, requires `ffmpeg` in PATH
  - AWS Transcribe: `boto3` + AWS credentials; `AWS_TRANSCRIBE_S3_BUCKET`
  - GCP Speech-to-Text: `google-cloud-speech` + `GOOGLE_APPLICATION_CREDENTIALS`
  - Export formats: `fpdf2` (PDF), `ebooklib` (EPUB); Kindle formats require Calibre `ebook-convert`
  - YouTube: `yt-dlp`
  - ID3 metadata: `mutagen` (optional)

## Minimal core-only install

```bash
pip install -e .
```

## Extras quick reference

| Feature | Extra | Install command | Notes |
|---|---|---|---|
| Whisper (local) | `whisper` | `pip install -e .[whisper]` | Requires `ffmpeg` on PATH |
| AWS Transcribe | `aws` | `pip install -e .[aws]` | Needs AWS creds + `AWS_TRANSCRIBE_S3_BUCKET` |
| GCP Speech-to-Text | `gcp` | `pip install -e .[gcp]` | Needs `GOOGLE_APPLICATION_CREDENTIALS` |
| Export formats (PDF/EPUB/Kindle) | `export` | `pip install -e .[export]` | Kindle formats need Calibre `ebook-convert` |
| Developer tools | `dev` | `pip install -e .[dev]` | Includes pytest, etc. |
| Docs | `docs` | `pip install -e .[docs]` | MkDocs + Material |

## Platform tips

- macOS: Install `ffmpeg` via Homebrew: `brew install ffmpeg`. Calibre: `brew install --cask calibre`.
- Linux: Use your package manager for `ffmpeg` and Calibre, or download from upstream.
- Windows: Install `ffmpeg` and ensure it’s on PATH; Calibre installer adds `ebook-convert`.
