# Convenience targets for development and release

.PHONY: help venv install dev test lint lint-fix fmt fmt-check docs-serve docs-build smoke build check dist upload-testpypi upload-pypi tag release

help:
	@echo "Common targets:"
	@echo "  make venv            # create .venv"
	@echo "  make dev             # install dev deps (editable)"
	@echo "  make test            # run pytest"
	@echo "  make fmt             # python -m black src tests"
	@echo "  make fmt-check       # python -m black --check"
	@echo "  make lint            # python -m ruff check"
	@echo "  make lint-fix        # python -m ruff check --fix"
	@echo "  make smoke           # run smoke script"
	@echo "  make docs-serve      # serve mkdocs"
	@echo "  make build           # build sdist+wheel"
	@echo "  make release VERSION=X.Y.Z  # build, upload, tag"
	@echo "  make coverage        # run pytest with coverage"
	@echo "  make coverage-html   # run coverage and build HTML report"

venv:
	python -m venv .venv

install:
	. .venv/bin/activate && pip install -e .

dev:
	. .venv/bin/activate && pip install -e .[dev]

test:
	. .venv/bin/activate && pytest -q

coverage:
	python -m pytest --cov=podcast_transcriber --cov-report=term-missing:skip-covered --cov-report=xml

coverage-html:
	python -m pytest --cov=podcast_transcriber --cov-report=html --cov-report=term-missing:skip-covered --cov-report=xml

fmt:
	python -m black src tests || (echo "Black not found. Install dev deps: pip install -e .[dev]" && exit 1)

fmt-check:
	python -m black --check src tests || (echo "Formatting issues or Black missing. Install dev deps: pip install -e .[dev]" && exit 1)

lint:
	python -m ruff check src tests || (echo "Ruff not found. Install dev deps: pip install -e .[dev]" && exit 1)

lint-fix:
	python -m ruff check --fix src tests || (echo "Ruff not found. Install dev deps: pip install -e .[dev]" && exit 1)

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
