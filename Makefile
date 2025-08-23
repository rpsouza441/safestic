.PHONY: backup list init dry-run

# Use the system's default Python interpreter, defaulting to python3 when
# `python` is not available (common on many Linux distributions).
PYTHON ?= python3

backup: ; $(PYTHON) -m safestic.cli backup
list: ; $(PYTHON) -m safestic.cli list
init: ; $(PYTHON) -m safestic.cli init
dry-run: ; $(PYTHON) -m safestic.cli dry-run
