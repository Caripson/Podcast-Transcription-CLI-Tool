# Convenience targets for development and release

.PHONY: help venv install dev test lint lint-fix fmt fmt-check docs-serve docs-build smoke build check dist upload-testpypi upload-pypi tag release

help:
	@echo "Common targets:"
	@echo "  make venv            # create .venv"
	@echo "  make dev             # install dev deps (editable)"
	@echo "  make test            # run pytest"
	@echo "  make fmt             # run black on src/tests"
	@echo "  make fmt-check       # black --check"
	@echo "  make lint            # ruff check"
	@echo "  make lint-fix        # ruff --fix"
	@echo "  make smoke           # run smoke script"
	@echo "  make docs-serve      # serve mkdocs"
	@echo "  make build           # build sdist+wheel"
	@echo "  make release VERSION=X.Y.Z  # build, upload, tag"

venv:
	python -m venv .venv

install:
	. .venv/bin/activate && pip install -e .

dev:
	. .venv/bin/activate && pip install -e .[dev]

test:
	. .venv/bin/activate && pytest -q

fmt:
	. .venv/bin/activate && black src tests || (echo "Install black via: pip install -e .[dev]" && exit 1)

fmt-check:
	. .venv/bin/activate && black --check src tests || (echo "Install black via: pip install -e .[dev]" && exit 1)

lint:
	. .venv/bin/activate && ruff check src tests || (echo "Install ruff via: pip install -e .[dev]" && exit 1)

lint-fix:
	. .venv/bin/activate && ruff check --fix src tests || (echo "Install ruff via: pip install -e .[dev]" && exit 1)

smoke:
	chmod +x scripts/smoke.sh || true
	./scripts/smoke.sh

docs-serve:
	. .venv/bin/activate && pip install -e .[docs] && mkdocs serve

docs-build:
	. .venv/bin/activate && pip install -e .[docs] && mkdocs build

build:
	. .venv/bin/activate && pip install build twine && python -m build

check:
	. .venv/bin/activate && python -m twine check dist/*

dist: build check

upload-testpypi:
	. .venv/bin/activate && python -m twine upload --repository testpypi dist/*

upload-pypi:
	. .venv/bin/activate && python -m twine upload dist/*

tag:
	@if [ -z "$(VERSION)" ]; then echo "VERSION is required, e.g., make tag VERSION=X.Y.Z"; exit 1; fi
	git tag -a v$(VERSION) -m "v$(VERSION)"
	git push origin v$(VERSION)

release: dist upload-pypi tag
	@echo "Released v$(VERSION)"
