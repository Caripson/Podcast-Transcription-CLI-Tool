#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 --url <URL|path> --service <whisper|aws|gcp> [--output <file>]" >&2
}

URL=""
SERVICE=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      URL="$2"; shift 2 ;;
    --service)
      SERVICE="$2"; shift 2 ;;
    --output)
      OUTPUT="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$URL" || -z "$SERVICE" ]]; then
  usage; exit 1
fi

if [[ -n "${VIRTUAL_ENV:-}" ]]; then PYTHON="python"; else PYTHON="python3"; fi

# Ensure local src is importable when running from repo without install
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:-}:${SCRIPT_DIR}/src"

CMD=("$PYTHON" -m podcast_transcriber --url "$URL" --service "$SERVICE")
if [[ -n "$OUTPUT" ]]; then
  CMD+=(--output "$OUTPUT")
fi

"${CMD[@]}"
