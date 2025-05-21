
# Caminho para o Python (ajuste conforme necessário)
PYTHON=python

.PHONY: backup list restore restore-id manual-prune check help

.DEFAULT_GOAL := help

## Executa o backup com base nas variáveis do .env
backup:
	@echo "🚀 Executando backup com Restic..."
	$(PYTHON) restic_backup.py

## Lista todos os snapshots no repositório
list:
	@echo "📂 Listando snapshots disponíveis..."
	$(PYTHON) list_snapshots.py

## Restaura o snapshot mais recente (default = latest)
restore:
	@echo "♻️ Restaurando o último snapshot..."
	$(PYTHON) restore_snapshot.py

## Restaura snapshot específico (ex: make restore-id ID=abc123)
restore-id:
ifndef ID
	$(error ⚠️  Você precisa passar o ID do snapshot: make restore-id ID=abc123)
endif
	@echo "♻️ Restaurando snapshot ID=$(ID)..."
	$(PYTHON) restore_snapshot.py $(ID)

## Aplica retenção manual (caso tenha desativado no .env)
manual-prune:
	@echo "🧹 Executando retenção manual com forget/prune..."
	restic -r $${RESTIC_REPOSITORY} forget \
		--keep-daily $${RETENTION_KEEP_DAILY:-7} \
		--keep-weekly $${RETENTION_KEEP_WEEKLY:-4} \
		--keep-monthly $${RETENTION_KEEP_MONTHLY:-6} \
		--prune

## Verifica se Restic está instalado, variáveis estão corretas e repositório é acessível
check:
	@echo "🔍 Executando verificação da configuração Restic..."
	$(PYTHON) check_restic_access.py

## Mostra ajuda com todos os comandos disponíveis
help:
	@echo "🛠️ Comandos disponíveis:"
	@echo "  make backup              Executa backup com ou sem retenção"
	@echo "  make list                Lista snapshots existentes no repositório"
	@echo "  make restore             Restaura o último snapshot (latest)"
	@echo "  make restore-id ID=xxx   Restaura um snapshot específico por ID"
	@echo "  make manual-prune        Aplica retenção manual (caso backup pule prune)"
	@echo "  make check               Valida PATH, .env e acesso ao repositório Restic"
	@echo "  make help                Exibe esta ajuda"
