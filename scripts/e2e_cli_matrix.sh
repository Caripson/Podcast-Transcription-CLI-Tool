#!/usr/bin/env bash
set -euo pipefail

# E2E matrix for the single-file CLI (podcast-transcriber):
# - Runs through all output formats with a local test audio
# - Exercises most CLI flags (metadata, PDF/EPUB, TOC, cache, batch/combine)
# - Designed to run in Docker; supports a Calibre image for Kindle formats
#
# Usage examples:
#   scripts/e2e_cli_matrix.sh --rebuild --dockerfile Dockerfile.calibre --image podcast-transcriber:calibre
#   scripts/e2e_cli_matrix.sh --image podcast-transcriber:latest

IMAGE_TAG="podcast-transcriber:latest"
DOCKERFILE="Dockerfile"
OUT_DIR="$(pwd)/out-cli"
REBUILD=0
CACHE_DIR="$(pwd)/.e2e-cache"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rebuild) REBUILD=1; shift ;;
    --image) IMAGE_TAG="$2"; shift 2 ;;
    --dockerfile) DOCKERFILE="$2"; shift 2 ;;
    -o|--out) OUT_DIR="$(realpath -m "$2")"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--rebuild] [--dockerfile Dockerfile|Dockerfile.calibre] [--image tag] [-o outdir]"; exit 0 ;;
  *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# In CI environments, default to rebuild to avoid stale images
if [[ $REBUILD -eq 0 ]]; then
  if [[ "${CI:-}" == "true" || "${GITHUB_ACTIONS:-}" == "true" ]]; then
    REBUILD=1
  fi
fi

mkdir -p "$OUT_DIR" "$CACHE_DIR"

if [[ $REBUILD -eq 1 ]] || ! docker image inspect "$IMAGE_TAG" >/dev/null 2>&1; then
  echo "Building Docker image $IMAGE_TAG using $DOCKERFILE ..."
  docker build -f "$DOCKERFILE" -t "$IMAGE_TAG" .
fi

cat >"$OUT_DIR/config.toml" <<'TOML'
language = "en"
title = "E2E CLI Matrix"
author = "CI"
epub_theme = "reader"
TOML

cat >"$OUT_DIR/list.txt" <<'LIST'
/workspace/tone.wav
/workspace/tone.wav
LIST

# Common flags to exercise argument parsing; most are ignored by whisper, but test coverage for parser
COMMON_ARGS=(
  --language en-US
  --aws-bucket test-bucket --aws-region us-east-1 --auto-language --aws-language-options sv-SE,en-US
  --gcp-alt-languages sv,en-US
  --title "E2E Title"
  --author "E2E Author"
  --epub-css-file /workspace/src/podcast_transcriber/exporters/themes.css
  --epub-theme custom:/workspace/src/podcast_transcriber/exporters/themes.css
  --auto-toc
  --pdf-cover-fullpage
  --pdf-first-page-cover-only
  --pdf-page-size A4
  --pdf-margin 12
  --pdf-orientation portrait
  --pdf-font Arial
  --summarize 2
  --normalize
  --cache-dir /tmp/pt-cache
)

FORMATS=(txt pdf epub mobi azw azw3 srt vtt json md)

echo "Running single-file CLI matrix over formats..."
for fmt in "${FORMATS[@]}"; do
  out="/out/matrix.${fmt}"
  echo "  -> ${fmt}"
  docker run --rm \
    -v "$(pwd)":/workspace \
    -v "$OUT_DIR":/out \
    -v "$CACHE_DIR":/root/.cache \
    "$IMAGE_TAG" \
      --url /workspace/tone.wav \
      --service whisper \
      --format "$fmt" \
      --output "$out" \
      "${COMMON_ARGS[@]}"
done

echo "Running batch mode: --input-file + --combine-into EPUB"
docker run --rm \
  -v "$(pwd)":/workspace \
  -v "$OUT_DIR":/out \
  -v "$CACHE_DIR":/root/.cache \
  "$IMAGE_TAG" \
    --service whisper \
    --input-file /out/list.txt \
    --combine-into /out/combined.epub \
    --config /out/config.toml \
    "${COMMON_ARGS[@]}"

echo "Matrix complete. Outputs in $OUT_DIR"
