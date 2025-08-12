#!/usr/bin/env bash
set -euo pipefail

# Simple pass-through wrapper to run the Python CLI from source.
# For usage and flags, run: python -m podcast_transcriber --help
#
# Developed by Johan Caripson

# Print attribution banner only for help/version to avoid polluting outputs
SHOW_BANNER=false
for arg in "$@"; do
  case "$arg" in
    -h|--help|--credits)
      SHOW_BANNER=true
      break
      ;;
  esac
done

if [[ "$SHOW_BANNER" == true ]]; then
  echo "Podcast Transcription CLI Tool — Developed by Johan Caripson"
fi

if [[ -n "${VIRTUAL_ENV:-}" ]]; then PYTHON="python"; else PYTHON="python3"; fi

# Ensure local src is importable when running from repo without install
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:-}:${SCRIPT_DIR}/src"

exec "$PYTHON" -m podcast_transcriber "$@"
