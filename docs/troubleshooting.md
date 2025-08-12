# Troubleshooting

Common issues and fixes when running the CLI.

## ffmpeg (Whisper)
- Symptom: Whisper fails with “ffmpeg is required”.
- Fix:
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get update && sudo apt-get install -y ffmpeg`

## ebook-convert (Kindle formats)
- Symptom: `ebook-convert` not found when exporting `mobi|azw|azw3|kfx`.
- Fix: Install Calibre and ensure `ebook-convert` is on PATH.
  - macOS: `brew install --cask calibre`
  - Linux: Use your distro package or download from calibre-ebook.com

## yt-dlp (YouTube URLs)
- Symptom: YouTube download fails or falls back to HTTP.
- Fix: Install `yt-dlp` and ensure it’s on PATH: `pipx install yt-dlp` or `pip install yt-dlp`.

## Mutagen (ID3 cover/title)
- Symptom: No auto title/cover from MP3 files.
- Fix: Install `mutagen`: `pip install mutagen`.

## boto3 and AWS credentials
- Symptom: AWS service fails with import error or credentials error.
- Fix: `pip install boto3`; configure credentials via `aws configure` or env vars.
- Ensure `AWS_TRANSCRIBE_S3_BUCKET` is set (or pass `--aws-bucket`).
- Optionally set region via `--aws-region` or `AWS_REGION`.

## google-cloud-speech and GCP credentials
- Symptom: GCP service fails with import/permission errors.
- Fix: `pip install google-cloud-speech`.
- Set `GOOGLE_APPLICATION_CREDENTIALS=/path/to/creds.json` or use ADC.
- For long audio/diarization, consider `--gcp-longrunning`.

## Calibre output differences
- Symptom: Converted Kindle files differ across systems.
- Fix: Calibre versions vary; ensure consistent version to avoid diffs.

## Unicode in PDF
- Symptom: Non‑ASCII characters missing in PDF.
- Fix: Use `--pdf-font-file /path/to/ttf` to embed a Unicode font (e.g., Noto).

## Large files and timeouts
- Symptom: Downloads/transcriptions time out.
- Fix: Re‑run with `--verbose` to see progress. Consider Whisper `--chunk-seconds`. Network retries are built‑in for downloads.

## Cache not used
- Symptom: Repeated runs don’t reuse results.
- Fix: Ensure `--no-cache` is not set. Cache key includes URL/source, service, language, speakers, whisper options.

## PATH issues
- Symptom: CLI can’t find `ffmpeg`, `ebook-convert`, or `yt-dlp`.
- Fix: Add the install location to your PATH. On macOS with Homebrew: add `/opt/homebrew/bin` (Apple Silicon) or `/usr/local/bin` (Intel).
