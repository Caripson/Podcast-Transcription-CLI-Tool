# Podcast Transcription CLI Tool

Transcribe podcasts and other audio from a URL or local file. Choose between local Whisper, AWS Transcribe, or Google Cloud Speech‑to‑Text. Export transcripts to text, subtitles, and e‑books.

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

See Quickstart for usage details.

### Author

Developed by Johan Caripson.
