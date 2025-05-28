# Caminho para o Python (ajuste conforme necessário)
PYTHON=python

.PHONY: backup list restore restore-id manual-prune check help

.DEFAULT_GOAL := help

## Executa o backup com base nas variáveis do .env
backup:
	@echo "Executando backup com Restic..."
	$(PYTHON) restic_backup.py

## Lista todos os snapshots no repositório
list:
	@echo "Listando snapshots disponíveis..."
	$(PYTHON) list_snapshots.py

## Lista arquivos contidos em um snapshot específico (ex: make list-files ID=abc123)
list-files:
ifndef ID
	$(error ⚠️  Você precisa passar o ID do snapshot: make list-files ID=abc123)
endif
	@echo "📂 Listando arquivos do snapshot ID=$(ID)..."
	$(PYTHON) list_snapshot_files.py $(ID)

## Restaura o snapshot mais recente (default = latest)
restore:
	@echo "Restaurando o último snapshot..."
	$(PYTHON) restore_snapshot.py

## Restaura snapshot específico (ex: make restore-id ID=abc123)
restore-id:
ifndef ID
	$(error  Você precisa passar o ID do snapshot: make restore-id ID=abc123)
endif
	@echo "Restaurando snapshot ID=$(ID)..."
	$(PYTHON) restore_snapshot.py $(ID)

## Restaura arquivo específico (ex: make restore-file ID=abc123 FILE=/etc/hosts)
restore-file:
ifndef ID
	$(error ⚠️  Você precisa passar o ID do snapshot: make restore-file ID=abc123 FILE=/caminho)
endif
ifndef FILE
	$(error ⚠️  Você precisa passar o caminho do arquivo: make restore-file ID=abc123 FILE=/caminho)
endif
	@echo "♻️ Restaurando arquivo $(FILE) do snapshot ID=$(ID)..."
	$(PYTHON) restore_file.py $(ID) $(FILE)


## Aplica retenção manual usando o script Python dedicado
manual-prune:
	@echo "Executando retenção manual via Python..."
	$(PYTHON) manual_prune.py

## Verifica se Restic está instalado, variáveis estão corretas e repositório é acessível
check:
	@echo "Executando verificação da configuração Restic..."
	$(PYTHON) check_restic_access.py

## Mostra ajuda com todos os comandos disponíveis
help:
	@echo "Comandos disponíveis:"
	@echo "  make backup              Executa backup com ou sem retenção"
	@echo "  make list                Lista snapshots existentes no repositório"
	@echo "  make list-files ID=xxx   Lista arquivos contidos em um snapshot"
	@echo "  make restore             Restaura o último snapshot (latest)"
	@echo "  make restore-id ID=xxx   Restaura um snapshot específico por ID"
	@echo "  make restore-file ID=xxx FILE=/caminho Arquivo específico de um snapshot"
	@echo "  make manual-prune        Aplica retenção manual usando script Python"
	@echo "  make check               Valida PATH, .env e acesso ao repositório Restic"
	@echo "  make help                Exibe esta ajuda"