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
- MVP status: Minimal integration implemented (upload → start job → poll → fetch transcript).

## 🟦 GCP Speech‑to‑Text

- Pros: High accuracy.
- Requirements: `google-cloud-speech`, GCP credentials (`GOOGLE_APPLICATION_CREDENTIALS` or ADC).
- MVP status: Minimal synchronous `recognize()` integration.

## ➕ Add a new service

Implement `TranscriptionService` and register it in `services.__init__.get_service`.

