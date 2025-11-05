# Minimal Safestic Makefile for Linux and Git Bash (Windows)
SHELL := /bin/bash
.SHELLFLAGS := -eo pipefail -c
.ONESHELL:

PROJECT_ROOT := $(CURDIR)
ENV_FILE ?= $(PROJECT_ROOT)/config/.env
SECRET_FETCH := $(PROJECT_ROOT)/scripts/secret_fetch.sh
PYTHON ?= python3

# Helper snippet to load configuration and prepare credentials
define LOAD_ENV
if [ ! -f "$(ENV_FILE)" ]; then
    echo "Arquivo de configuracao '$(ENV_FILE)' nao encontrado. Execute 'make setup'" >&2
    exit 1
fi
set -a
. "$(ENV_FILE)"
set +a
SECRET_MODE="$${SECRET_MODE:-}"
if [ -z "$$SECRET_MODE" ]; then
    echo "SECRET_MODE nao definido em $(ENV_FILE)." >&2
    exit 1
fi
case "$$SECRET_MODE" in
    file)
        if [ -z "$$RESTIC_PASSWORD_FILE" ]; then
            echo "RESTIC_PASSWORD_FILE nao definido." >&2
            exit 1
        fi
        if [ ! -f "$$RESTIC_PASSWORD_FILE" ]; then
            echo "RESTIC_PASSWORD_FILE '$$RESTIC_PASSWORD_FILE' nao encontrado." >&2
            exit 1
        fi
        chmod 600 "$$RESTIC_PASSWORD_FILE" 2>/dev/null || true
        export RESTIC_PASSWORD_FILE="$$RESTIC_PASSWORD_FILE"
        unset RESTIC_PASSWORD_COMMAND
        ;;
    manager)
        if [ -z "$$RESTIC_SECRET_BACKEND" ]; then
            echo "RESTIC_SECRET_BACKEND nao definido para SECRET_MODE=manager." >&2
            exit 1
        fi
        export RESTIC_PASSWORD_COMMAND="$(SECRET_FETCH) $$RESTIC_SECRET_BACKEND"
        unset RESTIC_PASSWORD_FILE
        ;;
    *)
        echo "SECRET_MODE invalido: '$$SECRET_MODE'. Use 'file' ou 'manager'." >&2
        exit 1
        ;;
esac
if [ -z "$$RESTIC_REPOSITORY" ]; then
    echo "RESTIC_REPOSITORY nao definido." >&2
    exit 1
fi
if [ -n "$$RESTIC_CACHE_DIR" ]; then
    mkdir -p "$$RESTIC_CACHE_DIR"
fi
export SECRET_MODE RESTIC_SECRET_BACKEND
export RESTIC_REPOSITORY RESTIC_CACHE_DIR
endef

.PHONY: help setup credentials check init backup snapshots restore forget-prune unlock rebuild-index recover schedule env-print

help:
	@printf "SafeStic Minimal Wrapper\n\n"
	@printf "Targets:\n"
	@printf "  setup          Prepare config directory and sample env\n"
	@printf "  credentials    Configure secrets interactively\n"
	@printf "  check          Validate dependencies and configuration\n"
	@printf "  init           Initialize restic repository\n"
	@printf "  backup         Run restic backup using INCLUDE_DIRS\n"
	@printf "  snapshots      List snapshots\n"
	@printf "  restore        Restore snapshot (SNAPSHOT=, TARGET=)\n"
	@printf "  forget-prune   Apply retention policy with prune\n"
	@printf "  unlock         Run restic unlock\n"
	@printf "  rebuild-index  Rebuild repository index\n"
	@printf "  recover        Recover repository\n"
	@printf "  schedule       Install/update system schedule\n"
	@printf "  env-print      Show sanitized configuration\n"

setup:
	mkdir -p "$(PROJECT_ROOT)/config"
	if [ ! -f "$(PROJECT_ROOT)/config/.env" ]; then
		cp "$(PROJECT_ROOT)/config/.env.example" "$(PROJECT_ROOT)/config/.env"
	fi
	if [ -f "$(PROJECT_ROOT)/config/restic_password.txt" ]; then
		chmod 600 "$(PROJECT_ROOT)/config/restic_password.txt" 2>/dev/null || true
	fi
	chmod +x "$(SECRET_FETCH)" "$(PROJECT_ROOT)/scripts/schedule.sh"
	printf "Setup concluido. Atualize config/.env com 'make credentials'.\n"

credentials:
	$(PYTHON) "$(PROJECT_ROOT)/scripts/credentials.py"

check:
	command -v restic >/dev/null 2>&1 || { echo "restic nao encontrado no PATH." >&2; exit 1; }
	$(LOAD_ENV)
	printf "SECRET_MODE: %s\n" "$$SECRET_MODE"
	if [ "$$SECRET_MODE" = "file" ]; then
		UNAME=$$(uname -s 2>/dev/null || echo "")
		if [ "$$UNAME" = "Linux" ]; then
			PERM=$$(stat -c "%a" "$$RESTIC_PASSWORD_FILE")
		else
			PERM=$$(stat -c "%a" "$$RESTIC_PASSWORD_FILE" 2>/dev/null || echo "600")
		fi
		printf "RESTIC_PASSWORD_FILE: %s (perms %s)\n" "$$RESTIC_PASSWORD_FILE" "$$PERM"
	else
		case "$$RESTIC_SECRET_BACKEND" in
			aws) CLI=aws ;;
			azure) CLI=az ;;
			gcp) CLI=gcloud ;;
			*) echo "Backend desconhecido: $$RESTIC_SECRET_BACKEND" >&2; exit 1 ;;
		esac
		command -v "$$CLI" >/dev/null 2>&1 || { echo "CLI $$CLI faltando." >&2; exit 1; }
		printf "RESTIC_SECRET_BACKEND: %s (CLI: %s)\n" "$$RESTIC_SECRET_BACKEND" "$$CLI"
	fi
	printf "RESTIC_REPOSITORY: %s\n" "$$RESTIC_REPOSITORY"
	printf "Check concluido.\n"

init:
	$(LOAD_ENV)
	restic init

backup:
	$(LOAD_ENV)
	INCLUDE_DIRS_ARRAY=($${INCLUDE_DIRS:-})
	if [ $${#INCLUDE_DIRS_ARRAY[@]} -eq 0 ]; then
		echo "INCLUDE_DIRS nao configurado." >&2
		exit 1
	fi
	CMD=(restic backup)
	if [ -n "$$RESTIC_CACHE_DIR" ]; then
		CMD+=(--cache-dir "$$RESTIC_CACHE_DIR")
	fi
	if [ -n "$$TAG" ]; then
		for tag in $$TAG; do CMD+=(--tag "$$tag"); done
	fi
	if [ -n "$$EXCLUDE_FILE" ]; then
		CMD+=(--exclude-file "$$EXCLUDE_FILE")
	fi
	if [ -n "$$EXCLUDE_PATTERNS" ]; then
		for pattern in $$EXCLUDE_PATTERNS; do CMD+=(--exclude "$$pattern"); done
	fi
	for dir in "$${INCLUDE_DIRS_ARRAY[@]}"; do
		CMD+=("$$dir")
	done
	echo "Executando: $${CMD[*]}"
	"$${CMD[@]}"

snapshots:
	$(LOAD_ENV)
	restic snapshots

restore:
	$(LOAD_ENV)
	SNAPSHOT="${SNAPSHOT:-latest}"
	TARGET="${TARGET:-$(PROJECT_ROOT)/restore}"
	mkdir -p "$$TARGET"
	restic restore "$$SNAPSHOT" --target "$$TARGET"

forget-prune:
	$(LOAD_ENV)
	CMD=(restic forget --prune)
	if [ -n "$$KEEP_DAILY" ]; then CMD+=(--keep-daily "$$KEEP_DAILY"); fi
	if [ -n "$$KEEP_WEEKLY" ]; then CMD+=(--keep-weekly "$$KEEP_WEEKLY"); fi
	if [ -n "$$KEEP_MONTHLY" ]; then CMD+=(--keep-monthly "$$KEEP_MONTHLY"); fi
	if [ -n "$$KEEP_YEARLY" ]; then CMD+=(--keep-yearly "$$KEEP_YEARLY"); fi
	echo "Executando: $${CMD[*]}"
	"$${CMD[@]}"

unlock:
	$(LOAD_ENV)
	restic unlock

rebuild-index:
	$(LOAD_ENV)
	restic rebuild-index

recover:
	$(LOAD_ENV)
	restic recover

schedule:
	$(LOAD_ENV)
	"$(PROJECT_ROOT)/scripts/schedule.sh" install

env-print:
	$(LOAD_ENV)
	printf "RESTIC_REPOSITORY=%s\n" "$$RESTIC_REPOSITORY"
	printf "SECRET_MODE=%s\n" "$$SECRET_MODE"
	if [ "$$SECRET_MODE" = "file" ]; then
		printf "RESTIC_PASSWORD_FILE=%s\n" "$$RESTIC_PASSWORD_FILE"
	else
		printf "RESTIC_SECRET_BACKEND=%s\n" "$$RESTIC_SECRET_BACKEND"
	fi
	printf "INCLUDE_DIRS=%s\n" "$$INCLUDE_DIRS"
	printf "EXCLUDE_FILE=%s\n" "$$EXCLUDE_FILE"
	printf "EXCLUDE_PATTERNS=%s\n" "$$EXCLUDE_PATTERNS"
	printf "TAG=%s\n" "$$TAG"
	printf "RESTIC_CACHE_DIR=%s\n" "$$RESTIC_CACHE_DIR"
	printf "KEEP_DAILY=%s\n" "$$KEEP_DAILY"
	printf "KEEP_WEEKLY=%s\n" "$$KEEP_WEEKLY"
	printf "KEEP_MONTHLY=%s\n" "$$KEEP_MONTHLY"
	printf "KEEP_YEARLY=%s\n" "$$KEEP_YEARLY"
	printf "SCHEDULE_CRON=%s\n" "$$SCHEDULE_CRON"
	printf "SCHEDULE_WIN_TIME=%s\n" "$$SCHEDULE_WIN_TIME"
	printf "SCHEDULE_WIN_DAYS=%s\n" "$$SCHEDULE_WIN_DAYS"
