# 🚀 Quickstart

Before running, ensure dependencies are installed. See [Dependencies & Extras](dependencies.md) for core and optional installs. For a full end‑to‑end Docker run, see [End-to-end recipes (Oxford)](#end-to-end-recipes-oxford).

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
- Output: `--format` one of `txt`, `pdf`, `epub`, `mobi`, `azw`, `azw3`, `srt`, `vtt`, `json`, `md`.
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

## Quality presets and speed tips

- Quality presets (Whisper): set via orchestrator YAML `quality: quick|standard|premium`.
  - `quick`: smallest model, fastest (good for CI smoke runs).
  - `standard`: balanced default (recommended for local testing).
  - `premium`: largest model, highest quality (slowest).
- Clip transcription length (orchestrator):
  - YAML: `clip_minutes: N` to pre‑clip audio before transcribing.
  - CLI override: `podcast-cli process --job-id <id> --clip-minutes N`.
- Cache models in Docker: mount a cache volume to reuse Whisper models between runs.
  - Example (our E2E scripts do this): `-v "$(pwd)/.e2e-cache:/root/.cache"`.

## Unicode PDF note

Core PDF fonts do not support full Unicode. Use a Unicode TTF/OTF via `--pdf-font-file`.

- In our Docker images, DejaVu fonts are installed. Recommended path:
  - `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`
- Example:

```bash
./Transcribe_podcast_to_text.sh \
  --url ./examples/tone.wav \
  --service whisper \
  --format pdf \
  --pdf-font-file /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf \
  --output transcript.pdf
```

## Per‑format options via orchestrator outputs

- PDF: `pdf_cover_fullpage: true`, `pdf_first_page_cover_only: true`, `pdf_font_file: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`
- DOCX: `docx_cover_first: true`, `docx_cover_width_inches: 6.0`
- Markdown: `md_include_cover: true`

Example (YAML):

```yaml
outputs:
  - fmt: pdf
    pdf_font_file: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
    pdf_cover_fullpage: true
  - fmt: docx
    docx_cover_first: true
    docx_cover_width_inches: 6.0
  - fmt: md
    md_include_cover: true
```

Kindle formats require Calibre’s `ebook-convert` in PATH; MOBI/AZW/AZW3/KFX are produced by converting a temporary EPUB.

Local development install:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install pytest  # for tests
```

## End-to-end recipes (Oxford)

Use the included YAML recipes to run the full ingest→process flow with Docker.

- Quick (fastest for CI/PR): `examples/recipes/oxford_quick.yml` (small model, `clip_minutes: 1`).
- Standard: `examples/recipes/oxford_cc.yml`.
- Premium: `examples/recipes/oxford_premium.yml`.

Run with the Calibre image to enable Kindle formats:

```bash
docker build -f Dockerfile.calibre -t podcast-transcriber:calibre .
./scripts/e2e_docker.sh -c examples/recipes/oxford_quick.yml -n 2 --fresh-state \
  --dockerfile Dockerfile.calibre --image podcast-transcriber:calibre
```

Customize a copy for your feed:

```yaml
feeds:
  - name: MyFeed
    url: https://example.com/feed.xml
    categories: ["creative commons", "technology"]
service: whisper
quality: standard
clip_minutes: 1
outputs:
  - fmt: epub
  - fmt: pdf
    pdf_font_file: /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
    pdf_cover_fullpage: true
  - fmt: docx
    docx_cover_first: true
    docx_cover_width_inches: 6.0
  - fmt: md
    md_include_cover: true
  - fmt: json
```

Notes

- Use `--fresh-state` to ignore the previous seen‑state and re‑ingest.
- Whisper models are cached in `./.e2e-cache` inside the container for faster runs.
- Prefer AZW3 for Kindle sideloading; KFX output isn’t available in distro Calibre.

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
