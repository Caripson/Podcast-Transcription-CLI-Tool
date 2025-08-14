# Contributing

Thanks for helping improve Podcast Transcription CLI Tool! This guide covers the basics. For detailed conventions and commands, see Repository Guidelines in [AGENTS.md](AGENTS.md).

## Quick Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
# optional extras for features/docs: [whisper],[aws],[gcp],[export],[docs]
```

## Run & Test

- CLI: `podcast-transcriber --url <URL|path> --service whisper --output out.txt`
- Module: `python -m podcast_transcriber ...`
- Tests: `pytest -q` (single file: `pytest tests/test_cli.py -q`)
- Smoke: `chmod +x scripts/smoke.sh && ./scripts/smoke.sh`

## Branch, Commits, Style

- Branch naming: `feature/<short-topic>` or `fix/<short-topic>`.
- Commits: imperative mood; optional scope (e.g., `cli:`). Keep concise and focused.
  - Examples: `cli: add --gcp-longrunning flag`, `exporters: fix EPUB theme path`.
- Style: Python 3.9+, PEP 8 (4 spaces). Prefer type hints in public APIs. Keep CLI thin; put logic in `src/podcast_transcriber/` modules. Services are pluggable via entry points.

## Pull Requests

1. Ensure tests pass locally: `pytest -q`.
2. Update or add tests for new behavior.
3. Update README/docs/examples for user-facing flags, outputs, or workflows.
4. Fill out the PR template: see `.github/PULL_REQUEST_TEMPLATE.md`.
5. Link related issues and include logs/screenshots for UX/docs changes.
6. CI must be green. Address feedback promptly.

## Security & Config

- Do not commit secrets. Use `.env` (based on `.env.example`) and environment variables (e.g., `AWS_TRANSCRIBE_S3_BUCKET`, `GOOGLE_APPLICATION_CREDENTIALS`).
- External tools: Whisper needs `ffmpeg`; Kindle formats need Calibre `ebook-convert`.

## Docs (optional)

- Preview site: `pip install -e .[docs] && mkdocs serve`
- Build site: `mkdocs build`

Thanks again—your contributions help make transcription easier for everyone!
