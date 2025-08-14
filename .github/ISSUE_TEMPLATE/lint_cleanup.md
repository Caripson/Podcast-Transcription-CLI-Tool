---
name: "Chore: Lint/Format Cleanup"
about: Track Ruff/Black cleanup in phases to keep diffs reviewable
labels: ["chore", "tech-debt"]
---

## Summary
Adopt consistent formatting (Black) and linting (Ruff) across the repo. Execute in small, low-risk phases.

## Context
- Config: see `pyproject.toml` for `[tool.black]` and `[tool.ruff]`.
- Make targets: `make fmt`, `make fmt-check`, `make lint`, `make lint-fix`.

## Plan (Phased)
- [x] Phase 0: Add config + Makefile targets (fmt/lint); PR includes AGENTS.md updates.
- [x] Phase 1: Format tests and utils only (ruff format) and apply safe fixes (`ruff check --fix`).
- [ ] Phase 2: Import order fixes (I001) across `src/` (no behavior changes).
- [ ] Phase 3: Long lines (E501): wrap or split; limited `# noqa: E501` allowed for URLs/strings.
- [ ] Phase 4: Modern typing upgrades (UP006/UP035) across `src/`.
- [ ] Phase 5: Remaining fixables (F401 unused imports, minor style) with `--fix` and small manual touches.

## Acceptance Criteria
- `make fmt-check` passes.
- `make lint` shows no errors for the targeted phase paths.
- `make test` remains green after each phase.

## Notes
- Avoid refactors while cleaning style. Keep diffs mechanical and scoped.
- If a rule causes noisy changes, propose narrowing or ignoring per-file.

