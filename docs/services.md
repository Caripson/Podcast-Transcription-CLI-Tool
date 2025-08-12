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
- Diarisering: `--speakers N` aktiverar `ShowSpeakerLabels` och grupperar ord till segments per talare.
- MVP status: Minimal integration med tillagd röstdiarisering och word-level parsing (upload → start job → poll → fetch transcript).

## 🟦 GCP Speech‑to‑Text

- Pros: High accuracy.
- Requirements: `google-cloud-speech`, GCP credentials (`GOOGLE_APPLICATION_CREDENTIALS` or ADC).
- Diarisering: `--speakers N` aktiverar diarization; för längre ljud använd `--gcp-longrunning` (long_running_recognize).
- Status: Synkron integration med möjlighet till long‑running och diarization; ordnivå och speaker‑taggar parse:as till segment.

## ➕ Add a new service

Implement `TranscriptionService` and register it in `services.__init__.get_service`.
