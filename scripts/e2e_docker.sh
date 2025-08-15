#!/usr/bin/env bash
set -euo pipefail

# End-to-end Docker smoke: ingest -> (limit N) -> process
# Usage: scripts/e2e_docker.sh -c examples/recipes/e2e_whisper.yml -n 2 [-o ./out] [--rebuild]

IMAGE_TAG="podcast-transcriber:latest"
DOCKERFILE="Dockerfile"
RECIPE=""
LIMIT="2"
OUT_DIR="$(pwd)/out"
STATE_DIR="$(pwd)/.e2e-state"
REBUILD=0
FRESH_STATE=0
CACHE_DIR="$(pwd)/.e2e-cache"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--config)
      RECIPE="$2"; shift 2 ;;
    -n|--limit)
      LIMIT="$2"; shift 2 ;;
    -o|--out)
      OUT_DIR="$(realpath -m "$2")"; shift 2 ;;
    --rebuild)
      REBUILD=1; shift ;;
    --image)
      IMAGE_TAG="$2"; shift 2 ;;
    --dockerfile)
      DOCKERFILE="$2"; shift 2 ;;
    --fresh-state)
      FRESH_STATE=1; shift ;;
    -h|--help)
      echo "Usage: $0 -c <recipe.yml> [-n 2] [-o ./out] [--rebuild] [--fresh-state] [--dockerfile FILE] [--image TAG]"; exit 0 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$RECIPE" ]]; then
  echo "Missing -c/--config <recipe.yml>" >&2
  exit 1
fi

if [[ $FRESH_STATE -eq 1 ]] && [[ -d "$STATE_DIR" ]]; then
  echo "Removing previous state at $STATE_DIR ..."
  rm -rf "$STATE_DIR"
fi
mkdir -p "$OUT_DIR" "$STATE_DIR" "$CACHE_DIR"

if [[ $REBUILD -eq 1 ]] || ! docker image inspect "$IMAGE_TAG" >/dev/null 2>&1; then
  echo "Building Docker image $IMAGE_TAG using $DOCKERFILE ..."
  docker build -f "$DOCKERFILE" -t "$IMAGE_TAG" .
fi

echo "Running ingest with recipe: $RECIPE"
JOB_ID=$(docker run --rm \
  -v "$(pwd)":/workspace \
  -v "$STATE_DIR":/root/.local/state/podcast_transcriber \
  -v "$OUT_DIR":/out \
  -v "$CACHE_DIR":/root/.cache \
  -e PYTHONPATH=/workspace/src \
  -e PODCAST_STATE_DIR=/root/.local/state/podcast_transcriber \
  -w /workspace \
  --entrypoint podcast-cli \
  "$IMAGE_TAG" \
  ingest --config "/workspace/$RECIPE" | tr -d '\r' | tail -n1)

if [[ -z "$JOB_ID" ]]; then
  echo "Failed to capture job id from ingest" >&2
  exit 1
fi
if [[ "$JOB_ID" != job-* ]]; then
  echo "Ingest did not find new episodes: $JOB_ID"
  echo "Tip: pass --fresh-state to ignore previously seen items."
  exit 0
fi
echo "Job: $JOB_ID"

# Trim episodes to LIMIT in state to ensure deterministic processing
echo "Limiting episodes to $LIMIT ..."
docker run --rm \
  -v "$STATE_DIR":/root/.local/state/podcast_transcriber \
  -e PODCAST_STATE_DIR=/root/.local/state/podcast_transcriber \
  -e LIMIT="$LIMIT" \
  --entrypoint python \
  "$IMAGE_TAG" \
  - <<'PY'
import json, os
state_path = os.path.expanduser('/root/.local/state/podcast_transcriber/state.json')
with open(state_path, 'r', encoding='utf-8') as f:
    st = json.load(f)
jobs = st.get('jobs', [])
if not jobs:
    raise SystemExit('No jobs found in state')
job = jobs[-1]
eps = job.get('episodes') or []
limit = int(os.environ.get('LIMIT', '2'))
job['episodes'] = eps[:limit]
with open(state_path, 'w', encoding='utf-8') as f:
    json.dump(st, f, ensure_ascii=False, indent=2)
print(f"Limited episodes to {limit} for job {job.get('id')}")
PY

echo "Processing job: $JOB_ID"
docker run --rm \
  -v "$(pwd)":/workspace \
  -v "$STATE_DIR":/root/.local/state/podcast_transcriber \
  -v "$OUT_DIR":/out \
  -v "$CACHE_DIR":/root/.cache \
  -e PYTHONPATH=/workspace/src \
  -e PODCAST_STATE_DIR=/root/.local/state/podcast_transcriber \
  -w /workspace \
  --entrypoint podcast-cli \
  "$IMAGE_TAG" \
  process --job-id "$JOB_ID"

echo "Artifacts in $OUT_DIR"
