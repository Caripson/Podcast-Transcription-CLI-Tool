# ☁️ Services

The tool supports multiple transcription services behind a common interface.

## 🖥️ Whisper (local)

- Pros: Private, free, runs locally.
- Requirements: `ffmpeg`, `openai-whisper`.
- Install:
  ```bash
  # macOS e.g.
  brew install ffmpeg
  pip install openai-whisper
  ```

## 🟧 AWS Transcribe

- Pros: Scalability, robust managed service.
- Requirements: `boto3`, AWS credentials, and `AWS_TRANSCRIBE_S3_BUCKET` set.
- Diarization: `--speakers N` enables `ShowSpeakerLabels` and groups words into speaker segments.
- MVP status: Minimal integration with speaker diarization and word-level parsing (upload → start job → poll → fetch transcript).

## 🟦 GCP Speech‑to‑Text

- Pros: High accuracy.
- Requirements: `google-cloud-speech`, GCP credentials (`GOOGLE_APPLICATION_CREDENTIALS` or ADC).
- Diarization: `--speakers N` enables diarization; for long audio use `--gcp-longrunning` (long_running_recognize).
- Status: Synchronous integration with optional long‑running and diarization; word‑level timestamps and speaker tags are parsed into segments.

## ➕ Add a new service

Prefer plugins via entry points so new services can ship as separate packages without modifying this repo.

- See: Plugins guide (`plugins.md`) and the example plugin at `examples/plugin_echo/`.
- Quick start:
  - Implement `TranscriptionService` in your package.
  - Register an entry point under `podcast_transcriber.services`.
  - Install your package; it will appear as a valid `--service` value and in interactive mode.
