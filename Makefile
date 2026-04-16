SHELL := /bin/bash
.DEFAULT_GOAL := help

POETRY ?= poetry
PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON ?= $(VENV)/bin/python
TARGET ?= .
PIP ?= $(VENV_PYTHON) -m pip
TOX_PYTHON ?= $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),$(if $(shell command -v $(POETRY) 2>/dev/null),$(POETRY) run python,$(PYTHON)))
PYTHON_CHECK_PATHS ?= src tests

DEV_PACKAGES := pip setuptools wheel pytest pytest-cov ruff mypy pre-commit tox

.PHONY: help help-all preflight bootstrap venv install build clean clean-deep format format-check lint lint-fix \
	deps pre-commit-install setup all markdown-format markdown-format-check markdown-lint \
	typecheck test test-local check ci tox tox-all vstack-validate vstack-install vstack-install-global vstack-verify

preflight:
	@command -v $(POETRY) >/dev/null 2>&1 || { echo "Poetry not found. Install from https://python-poetry.org/docs/"; exit 1; }

bootstrap: setup

setup: venv deps pre-commit-install

all: check

help:
	@echo "Core targets:"
	@echo "  make setup        - create .venv, install dev tools, install pre-commit hook"
	@echo "  make format       - format Python and Markdown"
	@echo "  make lint         - lint Python"
	@echo "  make test         - run tests on Python 3.11-3.14 via tox"
	@echo "  make test-local   - run pytest on current interpreter only"
	@echo "  make check        - full local quality gate"
	@echo "  make ci           - check + vstack template validation"
	@echo "  make tox          - run pytest across Python 3.11-3.14 (if interpreters are available)"
	@echo "  make clean        - remove build/cache artifacts"
	@echo "  make vstack-install - install generated artifacts into target"
	@echo ""
	@echo "For the full command list: make help-all"

help-all:
	@echo "All available targets:"
	@echo "  make setup               - create .venv, install dev tools, install pre-commit hook"
	@echo "  make bootstrap           - alias for setup"
	@echo "  make venv                - create local .venv"
	@echo "  make deps                - install/update local dev dependencies in .venv"
	@echo "  make pre-commit-install  - install git pre-commit hook"
	@echo "  make install             - install dependencies with Poetry"
	@echo "  make build               - build wheel and sdist"
	@echo "  make clean               - remove build/cache artifacts"
	@echo "  make clean-deep          - remove nested caches/bytecode recursively (keeps .venv)"
	@echo "  make format              - format Python and Markdown"
	@echo "  make format-check        - verify Ruff formatting"
	@echo "  make lint                - run Ruff lint checks"
	@echo "  make lint-fix            - auto-fix Ruff lint issues + reformat Markdown"
	@echo "  make markdown-format     - format Markdown via pre-commit mdformat hook"
	@echo "  make markdown-format-check - run markdown formatting check hook (may rewrite files)"
	@echo "  make markdown-lint       - lint Markdown via pre-commit markdownlint hook"
	@echo "  make typecheck           - run mypy on src/ and tests/"
	@echo "  make test                - run pytest matrix via tox (py311, py312, py313, py314)"
	@echo "  make test-local          - run pytest on current interpreter only"
	@echo "  make check               - run format-check + markdown checks + lint + typecheck + test"
	@echo "  make ci                  - run check + vstack-validate"
	@echo "  make tox                 - run tox pytest matrix (py311, py312, py313, py314)"
	@echo "  make tox-all             - run all tox envs (tests + lint + type)"
	@echo "  make vstack-validate     - run vstack validate"
	@echo "  make vstack-install      - run vstack install --target <path> (default .)"
	@echo "  make vstack-install-global - run vstack install --global"
	@echo "  make vstack-verify       - run vstack verify"

venv:
	$(PYTHON) -m venv $(VENV)

deps:
	$(PIP) install --upgrade $(DEV_PACKAGES)

pre-commit-install:
	$(VENV_PYTHON) -m pre_commit install

install: preflight
	$(POETRY) install

build: preflight
	$(POETRY) build

clean:
	rm -rf build dist
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov
	rm -f .coverage
	rm -rf src/*.egg-info

clean-deep:
	find . -path "./.venv" -prune -o -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".ruff_cache" -o -name ".mypy_cache" -o -name ".hypothesis" -o -name ".tox" -o -name ".nox" -o -name "htmlcov" -o -name "*.egg-info" \) -exec rm -rf {} +
	find . -path "./.venv" -prune -o -type f \( -name "*.pyc" -o -name "*.pyo" -o -name ".coverage" -o -name ".coverage.*" \) -delete
	rm -rf build dist

format:
	$(VENV_PYTHON) -m ruff format $(PYTHON_CHECK_PATHS)
	$(MAKE) markdown-format

format-check:
	$(VENV_PYTHON) -m ruff format --check $(PYTHON_CHECK_PATHS)

lint:
	$(VENV_PYTHON) -m ruff check $(PYTHON_CHECK_PATHS)

lint-fix:
	$(VENV_PYTHON) -m ruff check --fix $(PYTHON_CHECK_PATHS)
	$(MAKE) markdown-format

markdown-format:
	$(VENV_PYTHON) -m pre_commit run mdformat --all-files || $(VENV_PYTHON) -m pre_commit run mdformat --all-files

markdown-format-check:
	$(VENV_PYTHON) -m pre_commit run mdformat --all-files

markdown-lint:
	$(VENV_PYTHON) -m pre_commit run markdownlint-cli2 --all-files

typecheck:
	$(VENV_PYTHON) -m mypy $(PYTHON_CHECK_PATHS)

test-local:
	$(VENV_PYTHON) -m pytest -q

test:
	$(TOX_PYTHON) -m tox -e py311,py312,py313,py314

check: format-check markdown-lint lint typecheck test

ci: check vstack-validate

tox:
	$(TOX_PYTHON) -m tox -e py311,py312,py313,py314

tox-all:
	$(TOX_PYTHON) -m tox

vstack-validate:
	$(VENV_PYTHON) -m vstack validate

vstack-install:
	$(VENV_PYTHON) -m vstack install --target $(TARGET)

vstack-install-global:
	$(VENV_PYTHON) -m vstack install --global

vstack-verify:
	$(VENV_PYTHON) -m vstack verify
