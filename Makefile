# Caminho para o Python (ajuste conforme necessario)
ifeq ($(OS),Windows_NT)
	PYTHON=python
else
	PYTHON=python3
endif

.PHONY: backup list restore restore-id restore-file list-files manual-prune check help init dry-run stats validate test-backup test-restore clean prune

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
$(PYTHON) list_snapshot_files.py --id $(ID)

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
$(PYTHON) restore_snapshot.py --id $(ID)

## Restaura arquivo especifico (ex: make restore-file ID=abc123 FILE=/etc/hosts)
restore-file:
ifndef ID
	$(error Voce precisa passar o ID do snapshot: make restore-file ID=abc123 FILE=/caminho)
endif
ifndef FILE
	$(error Voce precisa passar o caminho do arquivo: make restore-file ID=abc123 FILE=/caminho)
endif
	@echo "Restaurando arquivo $(FILE) do snapshot ID=$(ID)..."
$(PYTHON) restore_file.py --id $(ID) --path $(FILE)

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

## Inicializa repositório Restic (apenas se não existir)
init:
	@echo "Inicializando repositório Restic..."
	$(PYTHON) -c "\
from services.restic_client import ResticClient; \
from services.restic import load_restic_config; \
config = load_restic_config(); \
client = ResticClient(config.repository_url, config.environment); \
try: \
    client.list_snapshots(); \
    print('✅ Repositório já existe'); \
except: \
    client.init_repository(); \
    print('✅ Repositório inicializado')"

## Simula backup sem executar (dry-run)
dry-run:
	@echo "Simulando backup (dry-run)..."
	$(PYTHON) -c "\
from services.restic import load_restic_config; \
from pathlib import Path; \
config = load_restic_config(); \
print('📋 Configuração de backup:'); \
print(f'Diretórios: {config.backup_source_dirs}'); \
print(f'Exclusões: {config.excludes}'); \
print(f'Tags: {config.tags}'); \
for dir_path in config.backup_source_dirs: \
    if Path(dir_path).exists(): \
        print(f'✅ {dir_path} - OK'); \
    else: \
        print(f'❌ {dir_path} - NÃO ENCONTRADO')"

## Mostra estatísticas detalhadas do repositório
stats:
	@echo "Obtendo estatísticas detalhadas..."
	$(PYTHON) -c "\
from services.restic_client import ResticClient; \
from services.restic import load_restic_config; \
config = load_restic_config(); \
client = ResticClient(config.repository_url, config.environment); \
stats = client.get_repository_stats(); \
print(f'Total de snapshots: {len(client.list_snapshots())}'); \
print('Executando restic stats...'); \
import subprocess; \
result = subprocess.run(['restic', '-r', config.repository_url, 'stats'], \
                       capture_output=True, text=True, env=config.environment); \
print(result.stdout)"

## Aplica política de retenção (prune)
prune:
	@echo "Aplicando política de retenção..."
	$(PYTHON) manual_prune.py

## Executa todos os checks de validação
validate:
	@echo "Executando validação completa..."
	@echo "1. Verificando configuração..."
	$(PYTHON) check_restic_access.py
	@echo "2. Verificando integridade..."
	$(PYTHON) -c "from services.restic_client import ResticClient; from services.restic import load_restic_config; config = load_restic_config(); ResticClient(config.repository_url, config.environment).check_repository()"
	@echo "3. Listando snapshots..."
	$(PYTHON) list_snapshots.py
	@echo "✅ Validação concluída"

## Cria backup de teste em diretório temporário
test-backup:
	@echo "Criando backup de teste..."
	mkdir -p /tmp/safestic-test
	echo "Arquivo de teste - $$(date)" > /tmp/safestic-test/teste.txt
	BACKUP_SOURCE_DIRS=/tmp/safestic-test RESTIC_TAGS=teste $(PYTHON) restic_backup.py
	rm -rf /tmp/safestic-test
	@echo "✅ Backup de teste concluído"

## Restaura para diretório temporário (teste)
test-restore:
	@echo "Testando restauração..."
	rm -rf /tmp/safestic-restore-test
	mkdir -p /tmp/safestic-restore-test
	RESTORE_TARGET_DIR=/tmp/safestic-restore-test $(PYTHON) restore_snapshot.py
	ls -la /tmp/safestic-restore-test
	@echo "✅ Teste de restauração concluído"

## Limpa arquivos temporários e logs antigos
clean:
	@echo "Limpando arquivos temporários..."
	find logs -name "*.log" -mtime +30 -delete 2>/dev/null || true
	rm -rf /tmp/safestic-* 2>/dev/null || true
	@echo "✅ Limpeza concluída"

# Novos targets - FASE 4
setup:
	@echo "Executando setup do ambiente..."
ifeq ($(OS),Windows_NT)
	@if exist "scripts\bootstrap_windows.ps1" ( \
		powershell -ExecutionPolicy Bypass -File "scripts\bootstrap_windows.ps1" \
	) else if exist "scripts\setup_windows.sh" ( \
		bash "scripts\setup_windows.sh" --assume-yes \
	) else ( \
		echo "Erro: Scripts de setup não encontrados" && exit 1 \
	)
else
	@if [ -f "scripts/setup_linux.sh" ]; then \
		bash "scripts/setup_linux.sh" --assume-yes; \
	else \
		echo "Erro: Script de setup Linux não encontrado"; \
		exit 1; \
	fi
endif

bootstrap:
	@echo "Executando bootstrap completo..."
ifeq ($(OS),Windows_NT)
	@if exist "scripts\bootstrap_windows.ps1" ( \
		powershell -ExecutionPolicy Bypass -File "scripts\bootstrap_windows.ps1" \
	) else ( \
		echo "Erro: bootstrap_windows.ps1 não encontrado" && exit 1 \
	)
else
	@echo "Bootstrap não implementado para Linux. Use: make setup"
	@exit 1
endif

first-run: setup
	@echo "Executando primeira configuração..."
	@echo "1. Verificando arquivo .env..."
	@if [ ! -f ".env" ]; then \
		echo "Copiando .env.example para .env..."; \
		cp .env.example .env; \
		echo "ATENÇÃO: Configure o arquivo .env antes de continuar!"; \
	else \
		echo ".env já existe"; \
	fi
	@echo "2. Validando configuração..."
	$(PYTHON) scripts/validate_config.py
	@echo "3. Inicializando repositório (se necessário)..."
	@$(MAKE) init || echo "Repositório já existe ou erro na inicialização"
	@echo "4. Executando verificação..."
	@$(MAKE) check
	@echo "Primeira configuração concluída!"

schedule-install:
	@echo "Instalando agendamento automático..."
ifeq ($(OS),Windows_NT)
	@if exist "scripts\schedule_windows.ps1" ( \
		powershell -ExecutionPolicy Bypass -File "scripts\schedule_windows.ps1" install \
	) else ( \
		echo "Erro: schedule_windows.ps1 não encontrado" && exit 1 \
	)
else
	@if [ -f "scripts/schedule_linux.sh" ]; then \
		bash "scripts/schedule_linux.sh" install; \
	else \
		echo "Erro: schedule_linux.sh não encontrado"; \
		exit 1; \
	fi
endif

schedule-remove:
	@echo "Removendo agendamento automático..."
ifeq ($(OS),Windows_NT)
	@if exist "scripts\schedule_windows.ps1" ( \
		powershell -ExecutionPolicy Bypass -File "scripts\schedule_windows.ps1" remove \
	) else ( \
		echo "Erro: schedule_windows.ps1 não encontrado" && exit 1 \
	)
else
	@if [ -f "scripts/schedule_linux.sh" ]; then \
		bash "scripts/schedule_linux.sh" remove; \
	else \
		echo "Erro: schedule_linux.sh não encontrado"; \
		exit 1; \
	fi
endif

schedule-status:
	@echo "Verificando status do agendamento..."
ifeq ($(OS),Windows_NT)
	@if exist "scripts\schedule_windows.ps1" ( \
		powershell -ExecutionPolicy Bypass -File "scripts\schedule_windows.ps1" status \
	) else ( \
		echo "Erro: schedule_windows.ps1 não encontrado" && exit 1 \
	)
else
	@if [ -f "scripts/schedule_linux.sh" ]; then \
		bash "scripts/schedule_linux.sh" status; \
	else \
		echo "Erro: schedule_linux.sh não encontrado"; \
		exit 1; \
	fi
endif

# Operações avançadas do Restic
forget:
	@echo "Esquecendo snapshots baseado na política de retenção..."
	$(PYTHON) scripts/forget_snapshots.py

mount:
	@echo "Montando repositório como sistema de arquivos..."
	@echo "ATENÇÃO: Esta operação requer FUSE (Linux/macOS) ou WinFsp (Windows)"
	$(PYTHON) scripts/mount_repo.py

unmount:
	@echo "Desmontando repositório..."
	$(PYTHON) scripts/unmount_repo.py

rebuild-index:
	@echo "Reconstruindo índice do repositório..."
	$(PYTHON) scripts/rebuild_index.py

repair:
	@echo "Reparando repositório..."
	@echo "ATENÇÃO: Esta operação pode ser destrutiva!"
	@read -p "Tem certeza? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	$(PYTHON) scripts/repair_repo.py

# Utilitários
health:
	@echo "Verificando saúde completa do sistema..."
ifeq ($(OS),Windows_NT)
	@if exist "check-backup-health.sh" ( \
		bash "check-backup-health.sh" \
	) else ( \
		echo "Script de saúde não encontrado" \
	)
else
	@if [ -f "check-backup-health.sh" ]; then \
		bash "check-backup-health.sh"; \
	else \
		echo "Script de saúde não encontrado"; \
	fi
endif

validate-setup:
	@echo "Validando configuração completa do setup..."
ifeq ($(OS),Windows_NT)
	@if exist "validate-setup.sh" ( \
		bash "validate-setup.sh" \
	) else ( \
		echo "Script de validação não encontrado" \
	)
else
	@if [ -f "validate-setup.sh" ]; then \
		bash "validate-setup.sh"; \
	else \
		echo "Script de validação não encontrado"; \
	fi
endif

## Mostra ajuda com todos os comandos disponiveis
help:
	@echo "=== COMANDOS SAFESTIC ==="
	@echo ""
	@echo "📦 OPERAÇÕES DE BACKUP:"
	@echo "  backup          - Executa backup completo"
	@echo "  dry-run         - Simula backup sem executar"
	@echo "  test-backup     - Testa backup com dados de exemplo"
	@echo ""
	@echo "📋 LISTAGEM E CONSULTA:"
	@echo "  list            - Lista snapshots disponíveis"
	@echo "  list-size       - Lista snapshots com tamanhos"
	@echo "  list-files      - Lista arquivos no último snapshot"
	@echo "  stats           - Mostra estatísticas do repositório"
	@echo "  repo-size       - Mostra tamanho do repositório"
	@echo ""
	@echo "🔄 RESTAURAÇÃO:"
	@echo "  restore         - Restaura último snapshot"
	@echo "  restore-id      - Restaura snapshot específico (ID=snapshot_id)"
	@echo "  restore-file    - Restaura arquivo específico (FILE=caminho/arquivo)"
	@echo "  test-restore    - Testa restauração com dados de exemplo"
	@echo ""
	@echo "🧹 MANUTENÇÃO:"
	@echo "  prune           - Remove snapshots antigos (automático)"
	@echo "  manual-prune    - Remove snapshots antigos manualmente"
	@echo "  forget          - Esquece snapshots baseado na política"
	@echo "  check           - Verifica integridade do repositório"
	@echo "  rebuild-index   - Reconstrói índice do repositório"
	@echo "  repair          - Repara repositório (CUIDADO!)"
	@echo "  clean           - Limpa logs e arquivos temporários"
	@echo ""
	@echo "⚙️  CONFIGURAÇÃO:"
	@echo "  setup           - Instala dependências do sistema"
	@echo "  bootstrap       - Bootstrap completo (Windows)"
	@echo "  first-run       - Primeira configuração do projeto"
	@echo "  init            - Inicializa novo repositório"
	@echo "  validate        - Valida configuração e dependências"
	@echo "  validate-setup  - Valida setup completo"
	@echo "  health          - Verifica saúde do sistema"
	@echo ""
	@echo "📅 AGENDAMENTO:"
	@echo "  schedule-install - Instala agendamento automático"
	@echo "  schedule-remove  - Remove agendamento automático"
	@echo "  schedule-status  - Status do agendamento"
	@echo ""
	@echo "🗂️  AVANÇADO:"
	@echo "  mount           - Monta repositório como filesystem"
	@echo "  unmount         - Desmonta repositório"
	@echo ""
	@echo "❓ AJUDA:"
	@echo "  help            - Mostra esta ajuda"
