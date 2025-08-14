# Repository Guidelines

## Project Structure & Module Organization
- `src/podcast_transcriber/`: Core package. Key modules: `cli.py` (main CLI), `services/` (Whisper/AWS/GCP backends), `exporters/` (PDF/EPUB/subtitles), `ingestion/`, `nlp/`, `templates/`, `flows/`, `delivery/`, `storage/`, `utils/`.
- `tests/`: Pytest suite with mocks (no real cloud calls). Files follow `test_*.py`.
- `examples/`: Sample audio, templates, and a plugin example.
- `scripts/`: Utility scripts (e.g., `smoke.sh`).
- `docs/` + `mkdocs.yml`: MkDocs site. Built output lives in `site/`.
- `.env.example`: Copy to `.env` for local credentials and settings.

## Build, Test, and Development Commands
- Create env and install: `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]`.
- Run CLI (installed): `podcast-transcriber --url <URL|path> --service whisper --output out.txt`.
- Run from source: `python -m podcast_transcriber ...` or `./Transcribe_podcast_to_text.sh ...`.
- Orchestrator (beta): `podcast-cli run --config config.yml` (see README for subcommands).
- Tests: `pytest -q` (single file: `pytest tests/test_cli.py -q`).
- Smoke test: `chmod +x scripts/smoke.sh && ./scripts/smoke.sh`.
- Docs (optional): `pip install -e .[docs] && mkdocs serve` (build: `mkdocs build`).
- CI-like local run: `bash scripts/ci_local.sh python3.12` (loops extras and runs pytest). 
 - Coverage: `make coverage` (XML + term report), `make coverage-html` for an HTML report in `htmlcov/`.
 - CI coverage threshold: enforced via `--cov-fail-under` (default 45%). Adjust in `.github/workflows/ci.yml` (`COV_MIN`).

## Coding Style & Naming Conventions
- Python 3.9+, PEP 8 (4-space indent). Prefer type hints in public APIs.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep CLIs thin; push logic into modules under `src/podcast_transcriber/`. Keep services pluggable via `project.entry-points`.
- Formatting: Black (`make fmt`, `make fmt-check`). Linting: Ruff (`make lint`, `make lint-fix`). Config in `pyproject.toml`.

## Testing Guidelines
- Framework: `pytest`. Place tests in `tests/` and name `test_*.py` with functions `test_*`.
- External services are mocked; do not hit AWS/GCP in tests. Add fixtures to `tests/conftest.py` if needed.
- Add/extend tests for new flags, formats, or services. Run `pytest -q` before pushing.

## Commit & Pull Request Guidelines
- Commits: Imperative mood, concise summary; optionally include scope (e.g., `cli:`) and reference issues (`#123`).
- PRs: Clear description, motivation, and test plan. Link issues, include screenshots/logs for UX/docs changes.
- Requirements: Passing CI, updated docs/README/examples when user-facing flags or behavior change. Never commit real `.env` or secrets.

## Security & Configuration Tips
- Secrets: Copy `.env.example` to `.env`; never commit `.env`.
- Common env/requirements: `AWS_TRANSCRIBE_S3_BUCKET` (AWS), `GOOGLE_APPLICATION_CREDENTIALS` (GCP), `ffmpeg` for Whisper, Calibre `ebook-convert` for Kindle formats.
- Caching/config: `--cache-dir` supported; auto-config at `~/.config/podcast-transcriber/config.toml` when present.
