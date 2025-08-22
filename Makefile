.PHONY: backup list init dry-run

backup: ; python -m safestic.cli backup
list: ; python -m safestic.cli list
init: ; python -m safestic.cli init
dry-run: ; python -m safestic.cli dry-run
