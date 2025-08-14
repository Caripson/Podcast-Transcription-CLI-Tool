# Pull Request Checklist

## Summary
- What does this PR change and why?

## Changes
- Key changes (bullets):
  - ...

## How to Test
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]`
- Run: `pytest -q` (or `pytest tests/test_<area>.py -q`)
- Optional smoke: `chmod +x scripts/smoke.sh && ./scripts/smoke.sh`

## Checklist
- [ ] Tests pass locally (`pytest -q`).
- [ ] Added/updated tests for new behavior.
- [ ] Updated docs/README/examples for user‑facing flags or outputs.
- [ ] No secrets committed; `.env` and credentials excluded.
- [ ] Backwards compatible CLI and APIs (or documented breaking changes).
- [ ] Verified main CLIs run: `podcast-transcriber` and/or `podcast-cli`.
- [ ] Considered caching/config impacts (`--cache-dir`, config files).
- [ ] Linked related issues and provided context/screenshots/logs when helpful.

## Type of Change
- [ ] Fix
- [ ] Feature
- [ ] Docs
- [ ] Refactor/Chore
- [ ] CI/CD

## Notes
- Anything reviewers should pay attention to (edge cases, follow‑ups).
