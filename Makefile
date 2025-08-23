.PHONY: backup list init dry-run

# Determine the appropriate Python interpreter. If a local virtual
# environment exists in .venv, prefer its Python executable. Otherwise,
# fall back to the system's default python3 (or python).
VENV ?= .venv
PYTHON := $(shell \
    if [ -f "$(VENV)/bin/python" ]; then echo "$(VENV)/bin/python"; \
    elif command -v python3 >/dev/null 2>&1; then command -v python3; \
    else command -v python; fi)

# Reusable CLI command to avoid repetition across targets.
CLI = $(PYTHON) -m safestic.cli

COMMANDS := backup list init dry-run

$(COMMANDS):
	$(CLI) $@
