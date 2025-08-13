# 📝 Changelog

All notable changes to this project are documented here.

## [0.1.0] - 2025-08-12
- 🎉 Initial MVP: CLI, service stubs, downloader, tests with mocks, docs via MkDocs, GitHub Actions CI.

## [1.1.0] - 2025-08-12
- Export: Added SRT/VTT/JSON/Markdown formats. PDF now supports headers/footers and a simple TOC; EPUB splits into chapters.
- Services: Whisper returns segments and word‑level timings; optional chunking (`--chunk-seconds`) and translate. AWS/GCP diarization with `--speakers` and GCP long‑running option.
- Sources: YouTube via `yt-dlp` and basic RSS enclosure support.
- CLI: Batch mode (`--input-file`), config (`--config`), caching (`--cache-dir`, `--no-cache`), verbosity, normalize/summarize post‑processing, EPUB custom themes via `custom:/path.css`.
- Downloader: HTTP retry/backoff and simple progress indicator with `--verbose`.
- AWS: Cleans up S3 input object unless `--aws-keep`.
- Docs: README overhaul; MkDocs usage/services/examples updated; Troubleshooting page added.

## [1.2.0] - 2025-08-12
- Config: Auto-discovery of default config at `$XDG_CONFIG_HOME/podcast-transcriber/config.toml` or `~/.config/podcast-transcriber/config.toml` (overridden by `--config`).
- Export(JSON): Includes downloader metadata (`source` block) such as original URL, local path, ID3 title/artist, yt-dlp title/uploader, and cover URL when available.
- CLI: Added `--interactive` guided mode that prompts for URL, service, format, output, and language.
- Plugins: Introduced formal plugin architecture for services using entry points under `podcast_transcriber.services`. Built-ins are also exposed via entry points.

## [1.3.0] - 2025-08-13
- KDP pipeline helpers:
  - New `--kdp` flag applies sane defaults (normalize text, EPUB with TOC, metadata pass-through).
  - Batch combiner: `--combine-into` merges multiple `--input-file` sources into one EPUB/DOCX/MD/TXT book with chapters.
- EPUB: Adds basic metadata (language, description, keywords) for better KDP ingestion.
- DOCX: New `--format docx` (requires `python-docx` or extra `[docx]`).

## [1.4.0] - 2025-08-13
- Orchestrator CLI: `podcast-cli` with `ingest`, `process`, `send`, `run`, and `digest` commands.
- Real ingestion: feed discovery via `feedparser` and duplicate avoidance using persistent state.
- NLP stubs: semantic topic segmentation (optional `sentence-transformers`) and simple key takeaways.
- Bilingual EPUB (premium mode): builds Original + Translated sections with Whisper translate when enabled.
- Templates: Jinja2 template and renderer for markdown manuscripts; ready for themed ebooks.
- Scheduler: `podcast-auto-run` using APScheduler for hourly/daily runs.
- Docs/help: switched to English; README updated with orchestrator usage, scheduling, and security notes.

## [1.4.1] - 2025-08-13
- Orchestrator: optional Markdown rendering via Jinja2 templates (`emit_markdown`, `markdown_template`).
- Ingestion: PodcastIndex lookups by feed URL, feed ID, or podcast GUID (when API env vars are set).
- NLP: feature flag for semantic topic segmentation (`nlp.semantic`) and key takeaways (`nlp.takeaways`).

## [1.4.2] - 2025-08-13
- CLI: `podcast-cli process` accepts `--semantic` to force semantic segmentation for ad-hoc runs.
- Templates: Base markdown template now includes overrideable blocks (`front_matter`, `title_page`, `preface`, `content`, `appendix`).
- Examples: Added `examples/config.sample.yml` and `examples/templates/ebook_theme_minimal.md.j2`.
