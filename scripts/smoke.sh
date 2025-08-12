#!/usr/bin/env bash
set -euo pipefail

# Simple smoke test for podcast-transcriber, plugin discovery, and JSON metadata.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
VENV_DIR="${ROOT_DIR}/.venv-smoke"
OUT_DIR="${ROOT_DIR}/out"

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

echo "[1/5] Testing JSON export with echo plugin..."
pip -q install -e "${ROOT_DIR}/examples/plugin_echo"
eval ${CLI_BIN} --url "${ROOT_DIR}/tone.wav" --service echo --format json --output "${OUT_DIR}/echo.json"

echo "[2/5] Testing TXT stdout with echo plugin..."
eval ${CLI_BIN} --url "${ROOT_DIR}/tone.wav" --service echo >/dev/null

echo "[3/5] Testing config auto-discovery..."
XDG_CONFIG_HOME="$(mktemp -d)"; export XDG_CONFIG_HOME
mkdir -p "$XDG_CONFIG_HOME/podcast-transcriber"
cat > "$XDG_CONFIG_HOME/podcast-transcriber/config.toml" <<EOF
language = "sv"
format = "txt"
EOF
eval ${CLI_BIN} --url "${ROOT_DIR}/tone.wav" --service echo --output "${OUT_DIR}/echo_config.txt" >/dev/null

echo "[4/5] Attempting Whisper JSON export (skips if deps missing)..."
if python -c "import shutil,sys; sys.exit(0 if shutil.which('ffmpeg') else 1)" && python -c "import whisper" 2>/dev/null; then
  pip -q install -e "${ROOT_DIR}"[whisper] >/dev/null || true
  eval ${CLI_BIN} --url "${ROOT_DIR}/tone.wav" --service whisper --format json --output "${OUT_DIR}/whisper.json"
else
  echo "  Skipped: ffmpeg or openai-whisper not installed."
fi

echo "[5/5] Done. Outputs in ${OUT_DIR}";

