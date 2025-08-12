# 🚀 Quickstart

Before running, ensure dependencies are installed. See [Dependencies & Extras](dependencies.md) for core and optional installs.

Run via the Bash script:

```bash
./Transcribe_podcast_to_text.sh --url "https://example.com/audio.mp3" --service whisper --output out.txt
```

Or via Python:

```bash
python -m podcast_transcriber --url <URL|path> --service <whisper|aws|gcp> --output out.txt
```

Arguments:

- `--url`: Remote audio URL or local file path.
- `--service`: `whisper`, `aws`, or `gcp`.
- `--language`: Language hint (e.g., `sv`, `en-US`) where supported.
- AWS flags: `--aws-bucket`, `--aws-region`, `--auto-language` (auto-detect when no `--language`).
- AWS optional: `--aws-language-options sv-SE,en-US` to restrict detection languages.
- GCP flags: `--gcp-alt-languages` (comma-separated list of alternates).
- `--output`: Transcript file path; defaults to stdout.
- Output: `--format` one of `txt`, `pdf`, `epub`, `mobi`, `azw`, `azw3`, `kfx`, `srt`, `vtt`, `json`, `md`.
- Metadata: `--title`, `--author` for EPUB/PDF/Kindle.
- EPUB CSS: `--epub-css-file` to embed basic styles into EPUB/Kindle.
 - EPUB theme: `--epub-theme minimal|reader|classic|dark` to enable a built-in CSS.
 - Custom theme: `--epub-theme custom:/absolute/or/relative/path.css`. A sample is provided at `src/podcast_transcriber/exporters/themes.css`.
- TOC and PDF headers/footers: `--auto-toc` enables a simple table of contents from segments; PDF adds title/author header/footer.
- PDF cover options: `--pdf-cover-fullpage` for a dedicated cover page; `--pdf-first-page-cover-only` to start transcript on next page.
 - PDF layout: `--pdf-page-size A4|Letter`, `--pdf-margin <mm>`.
 - PDF orientation: `--pdf-orientation portrait|landscape`.
 - PDF font embedding: `--pdf-font-file path/to/font.ttf` (use with Unicode text).
- Batch and config: `--input-file list.txt` to process many; `--config config.toml` for defaults.
- Cache and verbosity: `--cache-dir`, `--no-cache`, `--verbose`, `--quiet`.
- Post-processing: `--normalize`, `--summarize N`.

Kindle formats require Calibre’s `ebook-convert` in PATH; MOBI/AZW/AZW3/KFX are produced by converting a temporary EPUB.

Local development install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest  # for tests
```

Run tests:

```bash
pytest -q
```

## 📚 Examples

Whisper (local):

```bash
./Transcribe_podcast_to_text.sh \
  --url "https://example.com/podcast.mp3" \
  --service whisper \
  --output transcript.txt
```

AWS with language auto‑detect and options:

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

SRT/VTT export with diarization (AWS):

```bash
./Transcribe_podcast_to_text.sh \
  --url ./examples/tone.wav \
  --service aws \
  --speakers 2 \
  --format srt \
  --output transcript.srt
```
