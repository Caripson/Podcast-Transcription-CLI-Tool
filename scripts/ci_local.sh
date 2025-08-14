#!/usr/bin/env bash
set -euo pipefail

# Local CI runner to mimic GitHub CI matrix for this repo.
# Usage: scripts/ci_local.sh [python_executable]
# Example: scripts/ci_local.sh python3.12

PYTHON_BIN="${1:-python3}"
EXTRAS=(base aws gcp export templates orchestrator ingest env docx whisper)

echo "Using Python: $(${PYTHON_BIN} --version 2>/dev/null || echo not found)"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-ci-local"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python not found: ${PYTHON_BIN}" >&2
  exit 2
fi

if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip >/dev/null

failures=0

for extra in "${EXTRAS[@]}"; do
  echo "\n=== Running tests for extra: ${extra} ==="
  if [[ "${extra}" == "base" ]]; then
    pip -q install -e .
  else
    pip -q install -e .["${extra}"]
  fi
  # Ensure pytest present
  pip -q install pytest >/dev/null

  # Whisper requires ffmpeg; skip if missing
  if [[ "${extra}" == "whisper" ]]; then
    if ! command -v ffmpeg >/dev/null 2>&1; then
      echo "[skip] ffmpeg not found; skipping whisper extra tests"
      continue
    fi
  fi

  if ! pytest -q; then
    echo "[fail] pytest failed for extra: ${extra}" >&2
    failures=$((failures+1))
  else
    echo "[ok] pytest passed for extra: ${extra}"
  fi
done

if [[ ${failures} -gt 0 ]]; then
  echo "One or more extra suites failed (${failures})" >&2
  exit 1
fi

echo "All selected extras passed."

