#!/usr/bin/env bash
set -euo pipefail

# Simple pass-through wrapper to run the Python CLI from source.
# For usage and flags, run: python -m podcast_transcriber --help

if [[ -n "${VIRTUAL_ENV:-}" ]]; then PYTHON="python"; else PYTHON="python3"; fi

# Ensure local src is importable when running from repo without install
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:-}:${SCRIPT_DIR}/src"

exec "$PYTHON" -m podcast_transcriber "$@"
