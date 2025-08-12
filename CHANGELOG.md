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
