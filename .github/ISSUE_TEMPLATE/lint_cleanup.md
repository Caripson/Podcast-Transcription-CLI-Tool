---
name: "Chore: Lint/Format Cleanup"
about: Track Ruff formatter + linter cleanup in phases to keep diffs reviewable
labels: ["chore", "tech-debt"]
---

## Summary
Adopt consistent formatting (Ruff formatter) and linting (Ruff) across the repo. Execute in small, low‑risk phases. Black is optional and may be kept for local preference, but CI and Make targets use Ruff.

## Context
- Config: see `pyproject.toml` for `[tool.ruff]` (and `[tool.black]` kept for optional local use).
- Make targets: `make fmt`/`make fmt-check` (Ruff format), `make lint`/`make lint-fix` (Ruff check).

## Plan (Phased)
- [x] Phase 0: Confirm config + Makefile targets (fmt/lint); update AGENTS.md/README if needed.
- [x] Phase 1: Format tests and utils (Ruff format) and apply safe fixes (`ruff check --fix`).
- [ ] Phase 2: Import order fixes (I001) across `src/` (no behavior changes).
- [ ] Phase 3: Long lines (E501): selectively wrap/split; allow limited `# noqa: E501` for URLs/strings; E501 remains ignored globally for now.
- [ ] Phase 4: Modern typing upgrades (UP006/UP035) across `src/` where safe.
- [ ] Phase 5: Remaining fixables (e.g., F401 unused imports, minor style) with `--fix` and small manual changes.

## Acceptance Criteria
- `make fmt-check` passes.
- `make lint` shows no errors for the targeted phase paths.
- Tests remain green (`pytest -q`) after each phase.

## Notes
- Avoid refactors while cleaning style. Keep diffs mechanical and scoped.
- If any rule causes noisy changes, propose narrowing scope or adding per-file ignores.
