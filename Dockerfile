# syntax=docker/dockerfile:1
FROM python:3.12-slim as app

ARG PIP_EXTRAS="export,templates,ingest,orchestrator,env"
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (keep minimal). ffmpeg is useful for Whisper/local audio tooling.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src ./src

# Install package with selectable extras (comma-separated)
RUN python -m pip install --upgrade pip \
 && python -m pip install ".[${PIP_EXTRAS}]"

# Default to CLI help; override the command at runtime for other entry points.
ENTRYPOINT ["podcast-transcriber"]
CMD ["--help"]

