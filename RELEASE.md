# Release Guide

A quick, repeatable checklist for publishing a new version of Podcast Transcription CLI Tool.

## Prerequisites
- Clean working tree on `main` and passing CI.
- PyPI credentials configured (e.g., `~/.pypirc`) and 2FA ready.
- Tools: `pip install build twine`.

## Versioning & Changelog
- Follow SemVer. Choose the next version: `MAJOR.MINOR.PATCH`.
- Bump in `pyproject.toml` under `[project].version`.
- Update `CHANGELOG.md` with a concise summary of changes.
- Optional: adjust README badges if version is pinned.

## Verify Locally
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pytest -q
chmod +x scripts/smoke.sh && ./scripts/smoke.sh  # optional
```

## Build & Check
```bash
rm -rf dist/
python -m build
python -m twine check dist/*
```

## Publish to TestPyPI (optional dry run)
```bash
python -m twine upload --repository testpypi dist/*
# Install from TestPyPI in a clean env to sanity check if desired
```

## Publish to PyPI
```bash
python -m twine upload dist/*
```

## Tag & Push
```bash
git add -A
git commit -m "release: vX.Y.Z"
sed -n '1,40p' CHANGELOG.md  # sanity review

git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin main --tags
```

## Post-Release
- Create a GitHub Release for tag `vX.Y.Z` and paste highlights from `CHANGELOG.md`.
- Docs: CI builds MkDocs from `docs/` and publishes to Pages (see `.github/workflows/docs.yml`).
- Open an issue for any follow-ups or hotfixes.

Notes
- External tools: Whisper requires `ffmpeg`; Kindle formats rely on Calibre `ebook-convert`.
- Wheels: If adding compiled deps, ensure platform wheels or document build requirements.
