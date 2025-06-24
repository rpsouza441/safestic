# Caminho para o Python (ajuste conforme necessario)
ifeq ($(OS),Windows_NT)
	PYTHON=python
else
	PYTHON=python3
endif

.PHONY: backup list restore restore-id restore-file list-files manual-prune check help

.DEFAULT_GOAL := help

## Executa o backup com base nas variaveis do .env
backup:
	@echo "Executando backup com Restic..."
	$(PYTHON) restic_backup.py

## Lista todos os snapshots no repositorio
list:
	@echo "Listando snapshots disponiveis..."
	$(PYTHON) list_snapshots.py

## Lista todos os snapshots com tamanho estimado
list-size:
	@echo "Listando snapshots com tamanho estimado..."
	$(PYTHON) list_snapshots_with_size.py

## Lista arquivos contidos em um snapshot especifico (ex: make list-files ID=abc123)
list-files:
ifndef ID
	$(error Voce precisa passar o ID do snapshot: make list-files ID=abc123)
endif
	@echo "Listando arquivos do snapshot ID=$(ID)..."
	$(PYTHON) list_snapshot_files.py $(ID)

## Restaura o snapshot mais recente (default = latest)
restore:
	@echo "Restaurando o ultimo snapshot..."
	$(PYTHON) restore_snapshot.py

## Restaura snapshot especifico (ex: make restore-id ID=abc123)
restore-id:
ifndef ID
	$(error Voce precisa passar o ID do snapshot: make restore-id ID=abc123)
endif
	@echo "Restaurando snapshot ID=$(ID)..."
	$(PYTHON) restore_snapshot.py $(ID)

## Restaura arquivo especifico (ex: make restore-file ID=abc123 FILE=/etc/hosts)
restore-file:
ifndef ID
	$(error Voce precisa passar o ID do snapshot: make restore-file ID=abc123 FILE=/caminho)
endif
ifndef FILE
	$(error Voce precisa passar o caminho do arquivo: make restore-file ID=abc123 FILE=/caminho)
endif
	@echo "Restaurando arquivo $(FILE) do snapshot ID=$(ID)..."
	$(PYTHON) restore_file.py $(ID) $(FILE)

## Aplica retencao manual usando o script Python dedicado
manual-prune:
	@echo "Executando retencao manual via Python..."
	$(PYTHON) manual_prune.py

## Verifica se Restic esta instalado, variaveis estao corretas e repositorio esta acessivel
check:
	@echo "Executando verificacao da configuracao Restic..."
	$(PYTHON) check_restic_access.py

## Exibe o total de dados únicos armazenados no repositório
repo-size:
	@echo "Calculando uso real do repositório..."
	$(PYTHON) repository_stats.py

## Mostra ajuda com todos os comandos disponiveis
help:
	@echo "Comandos disponiveis:"
	@printf "%-45s %s\n" "make backup"              "Executa backup com ou sem retencao"
	@printf "%-45s %s\n" "make list"                "Lista snapshots existentes no repositorio"
	@printf "%-45s %s\n" "make list-size"           "Lista snapshots existentes no repositorio com tamanho estimado"
	@printf "%-45s %s\n" "make list-files ID=xxx"   "Lista arquivos contidos em um snapshot"
	@printf "%-45s %s\n" "make restore"             "Restaura o ultimo snapshot (latest)"
	@printf "%-45s %s\n" "make restore-id ID=xxx"   "Restaura um snapshot especifico por ID"
	@printf "%-45s %s\n" "make restore-file ID=xxx FILE=caminho/arquivo" "Restaura arquivo especifico. Nao comecar com barra"
	@printf "%-45s %s\n" "make manual-prune"        "Aplica retencao manual usando script Python"
	@printf "%-45s %s\n" "make check"               "Valida PATH, .env e acesso ao repositorio Restic"
	@printf "%-45s %s\n" "make help"                "Exibe esta ajuda"
	@printf "%-45s %s\n" "make repo-size"            "Mostra o total em GiB armazenado no repositório (raw data)"
