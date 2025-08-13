#!/usr/bin/env bash
set -euo pipefail

# Simple smoke test for podcast-transcriber, plugin discovery, and JSON metadata.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-smoke"
OUT_DIR="${ROOT_DIR}/out"

# Helper to also write messages to GitHub Actions job summary when available
add_summary() {
  local msg="$1"
  if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    echo "$msg" >> "${GITHUB_STEP_SUMMARY}"
  fi
}

python3 -V >/dev/null 2>&1 || { echo "python3 not found"; exit 1; }

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi
source "${VENV_DIR}/bin/activate"

pip -q install --upgrade pip
pip -q install -e "${ROOT_DIR}"[export] || true

mkdir -p "${OUT_DIR}"

# Generate sample tone audio
python "${ROOT_DIR}/examples/generate_tone.py" >/dev/null

CLI_BIN="podcast-transcriber"
if ! command -v "${CLI_BIN}" >/dev/null 2>&1; then
  CLI_BIN="python -m podcast_transcriber"
fi

echo "[1/5] Testing JSON export with echo plugin..."; add_summary "- JSON export with echo plugin"
pip -q install -e "${ROOT_DIR}/examples/plugin_echo"
eval ${CLI_BIN} --url "${ROOT_DIR}/tone.wav" --service echo --format json --output "${OUT_DIR}/echo.json"

echo "[2/5] Testing TXT stdout with echo plugin..."; add_summary "- TXT stdout with echo plugin"
eval ${CLI_BIN} --url "${ROOT_DIR}/tone.wav" --service echo >/dev/null

echo "[3/5] Testing config auto-discovery..."; add_summary "- Config auto-discovery"
XDG_CONFIG_HOME="$(mktemp -d)"; export XDG_CONFIG_HOME
mkdir -p "$XDG_CONFIG_HOME/podcast-transcriber"
cat > "$XDG_CONFIG_HOME/podcast-transcriber/config.toml" <<EOF
language = "sv"
format = "txt"
EOF
eval ${CLI_BIN} --url "${ROOT_DIR}/tone.wav" --service echo --output "${OUT_DIR}/echo_config.txt" >/dev/null

echo "[4/5] Attempting Whisper JSON export (skips if deps missing)..."; add_summary "- Whisper JSON export (skips if deps missing)"
if python -c "import shutil,sys; sys.exit(0 if shutil.which('ffmpeg') else 1)" && python -c "import whisper" 2>/dev/null; then
  pip -q install -e "${ROOT_DIR}"[whisper] >/dev/null || true
  eval ${CLI_BIN} --url "${ROOT_DIR}/tone.wav" --service whisper --format json --output "${OUT_DIR}/whisper.json"
else
  echo "  Skipped: ffmpeg or openai-whisper not installed."; add_summary "  Skipped Whisper: ffmpeg or openai-whisper not installed"
fi

echo "[5/6] Testing orchestrator process with echo plugin + Markdown..."; add_summary "- Orchestrator process + Markdown"

# Gate on Jinja2 presence; orchestrator Markdown requires it
if python - <<'PY'
import sys
try:
    import jinja2  # noqa: F401
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
then
  # Ensure plugin is installed for orchestrator as well
  pip -q install -e "${ROOT_DIR}/examples/plugin_echo" >/dev/null

  # Use isolated state
  export PODCAST_STATE_DIR="$(mktemp -d)"

  python - <<PY
from podcast_transcriber.storage.state import StateStore
from pathlib import Path
import os
out_dir = os.environ.get('OUT_DIR') or '${OUT_DIR}'
store = StateStore()
cfg = {
  'service': 'echo',
  'output_dir': out_dir,
  'author': 'Smoke',
  'emit_markdown': True,
}
ep = {'feed': 'smoke', 'title': 'Tone', 'slug': 'tone', 'source': str(Path('${ROOT_DIR}')/'tone.wav')}
job = store.create_job_with_episodes(cfg, [ep])
print(job['id'])
PY

  JOB_ID=$(python - <<'PY'
from podcast_transcriber.storage.state import StateStore
print(StateStore().state['jobs'][-1]['id'])
PY
  )

  podcast-cli process --job-id "$JOB_ID" >/dev/null

  if test -f "${OUT_DIR}/tone.epub" && test -f "${OUT_DIR}/tone.md"; then
    echo "  Orchestrator OK"; add_summary "  Orchestrator OK"
  else
    echo "  Orchestrator FAILED"; add_summary "  Orchestrator FAILED"; exit 1
  fi
else
  echo "  Skipped orchestrator Markdown test: Jinja2 not installed."; add_summary "  Skipped orchestrator Markdown (no Jinja2)"
fi

echo "[6/6] Done. Outputs in ${OUT_DIR}"; add_summary "- Outputs in ${OUT_DIR}"
