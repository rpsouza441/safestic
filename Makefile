# Caminho para o Python (ajuste conforme necessario)
ifeq ($(OS),Windows_NT)
	PYTHON=python
	VENV_ACTIVATE=.venv\Scripts\Activate.ps1
	VENV_PYTHON=.venv\Scripts\python.exe
else
	PYTHON=python3
	VENV_ACTIVATE=.venv/bin/activate
	VENV_PYTHON=.venv/bin/python
endif

# Verificar se ambiente virtual existe e usar se disponivel
ifeq ($(OS),Windows_NT)
	PYTHON_CMD=$(if $(wildcard .venv\Scripts\python.exe),$(VENV_PYTHON),$(PYTHON))
else
	PYTHON_CMD=$(if $(wildcard .venv/bin/python),$(VENV_PYTHON),$(PYTHON))
endif

.PHONY: backup list restore restore-id restore-file list-files manual-prune check help init dry-run stats validate test-backup test-restore clean prune

.DEFAULT_GOAL := help

## Executa o backup com base nas variaveis do .env
backup:
	@echo "Executando backup com Restic..."
	@echo "Verificando credenciais..."
	@$(PYTHON_CMD) scripts/check_credentials.py --restic-only --quiet || (echo "" && echo "ERRO: RESTIC_PASSWORD nao configurado!" && echo "Execute: make setup-restic-password" && echo "" && exit 1)
	$(PYTHON_CMD) restic_backup.py

## Lista todos os snapshots no repositorio
list:
	@echo "Listando snapshots disponiveis..."
	@$(PYTHON_CMD) scripts/check_credentials.py --restic-only --quiet || (echo "" && echo "ERRO: RESTIC_PASSWORD nao configurado!" && echo "Execute: make setup-restic-password" && echo "" && exit 1)
	$(PYTHON_CMD) list_snapshots.py

## Lista todos os snapshots com tamanho estimado
list-size:
	@echo "Listando snapshots com tamanho estimado..."
	$(PYTHON_CMD) list_snapshots_with_size.py

## Lista arquivos contidos em um snapshot especifico
## Exemplos:
##   make list-files ID=abc123                    # Saida em texto no terminal
##   make list-files ID=abc123 FORMAT=json        # Saida em JSON no terminal
##   make list-files ID=abc123 FORMAT=json OUTPUT=files.json  # Salvar JSON em arquivo
##   make list-files ID=abc123 PRETTY=1           # Formatacao legivel para humanos
list-files:
ifndef ID
	$(error Voce precisa passar o ID do snapshot: make list-files ID=abc123)
endif
	@echo "Listando arquivos do snapshot ID=$(ID)..."
	$(PYTHON_CMD) list_snapshot_files.py --id $(ID)$(if $(FORMAT), --format $(FORMAT))$(if $(OUTPUT), --output $(OUTPUT))$(if $(PRETTY), --pretty)

## Restaura o snapshot mais recente (default = latest)
## Cria estrutura: C:\Restore\AAAA-MM-DD-HHMMSS\<estrutura_original>
restore:
	@echo "Restaurando o ultimo snapshot..."
	@$(PYTHON_CMD) scripts/check_credentials.py --restic-only --quiet || (echo "" && echo "ERRO: RESTIC_PASSWORD nao configurado!" && echo "Execute: make setup-restic-password" && echo "" && exit 1)
	$(PYTHON_CMD) restore_snapshot.py

## Restaura snapshot especifico (ex: make restore-id ID=abc123)
## Cria estrutura: C:\Restore\AAAA-MM-DD-HHMMSS\<estrutura_original>
restore-id:
ifndef ID
	$(error Voce precisa passar o ID do snapshot: make restore-id ID=abc123)
endif
	@echo "Restaurando snapshot ID=$(ID)..."
	@$(PYTHON_CMD) scripts/check_credentials.py --restic-only --quiet || (echo "" && echo "ERRO: RESTIC_PASSWORD nao configurado!" && echo "Execute: make setup-restic-password" && echo "" && exit 1)
	$(PYTHON_CMD) restore_snapshot.py $(ID)

## Restaura arquivo especifico (ex: make restore-file ID=abc123 FILE="C:\Users\Admin\Documents")
## Cria estrutura: C:\Restore\AAAA-MM-DD-HHMMSS\C\Users\Admin\Documents
## Onde AAAA-MM-DD-HHMMSS corresponde à data/hora do snapshot
restore-file:
ifndef ID
	$(error Voce precisa passar o ID do snapshot: make restore-file ID=abc123 FILE="/caminho")
endif
ifndef FILE
	$(error Voce precisa passar o caminho do arquivo: make restore-file ID=abc123 FILE="/caminho")
endif
	@echo "Restaurando arquivo $(FILE) do snapshot ID=$(ID)..."
	$(PYTHON_CMD) restore_file.py $(ID) "$(FILE)"

## Aplica retencao manual usando o script Python dedicado
manual-prune:
	@echo "Executando retencao manual via Python..."
	$(PYTHON_CMD) manual_prune.py

## Verifica se Restic esta instalado, variaveis estao corretas e repositorio esta acessivel
check:
	@echo "Executando verificacao da configuracao Restic..."
	@echo "Verificando credenciais..."
	@$(PYTHON_CMD) scripts/check_credentials.py --quiet || (echo "" && echo "AVISO: Algumas credenciais nao estao configuradas" && echo "Execute: make setup-credentials" && echo "")
	$(PYTHON_CMD) check_restic_access.py

## Exibe o total de dados unicos armazenados no repositorio
repo-size:
	@echo "Calculando uso real do repositorio..."
	$(PYTHON_CMD) repository_stats.py

## Inicializa repositorio Restic (apenas se nao existir)
init:
	@echo "Inicializando repositorio Restic..."
	@echo "Verificando credenciais..."
	@$(PYTHON_CMD) scripts/check_credentials.py --restic-only --quiet || (echo "" && echo "ERRO: RESTIC_PASSWORD nao configurado!" && echo "Execute: make setup-restic-password" && echo "" && exit 1)
	$(PYTHON_CMD) -c "from services.restic_client import ResticClient; from services.restic import load_restic_config; config = load_restic_config(); client = ResticClient(); exec('try:\n    client.check_repository_access()\n    print(\"Repositorio ja existe\")\nexcept:\n    client.init_repository()\n    print(\"Repositorio inicializado\")')"

## Simula backup sem executar (dry-run)
dry-run:
	@echo "Simulando backup (dry-run)..."
	$(PYTHON_CMD) -c "from services.restic import load_restic_config; from pathlib import Path; config = load_restic_config(); print('Configuracao de backup:'); print(f'Diretorios: {config.backup_source_dirs}'); print(f'Exclusoes: {config.restic_excludes}'); print(f'Tags: {config.restic_tags}'); [print(f'{dir_path} - OK') if Path(dir_path).exists() else print(f'{dir_path} - NAO ENCONTRADO') for dir_path in config.backup_source_dirs]"

## Mostra estatisticas detalhadas do repositorio
stats:
	@echo "Obtendo estatisticas detalhadas..."
	$(PYTHON_CMD) -c "from services.restic_client import ResticClient; ResticClient().show_stats()"

## Aplica politica de retencao (prune)
prune:
	@echo "Aplicando politica de retencao..."
	@$(PYTHON_CMD) scripts/check_credentials.py --restic-only --quiet || (echo "" && echo "ERRO: RESTIC_PASSWORD nao configurado!" && echo "Execute: make setup-restic-password" && echo "" && exit 1)
	$(PYTHON_CMD) scripts/forget_snapshots.py

## Executa todos os checks de validacao
validate:
	@echo "Executando validacao completa..."
	@echo "1. Verificando configuracao..."
	$(PYTHON_CMD) scripts/validate_config.py
	@echo "2. Verificando integridade..."
	$(PYTHON_CMD) -c "from services.restic_client import ResticClient; client = ResticClient(); client.check_repository_access()"
	@echo "3. Listando snapshots..."
	$(PYTHON_CMD) -c "from services.restic_client import ResticClient; ResticClient().list_snapshots()"
	@echo "Validacao concluida"

## Cria backup de teste em diretorio temporario
test-backup:
	@echo "Criando backup de teste..."
ifeq ($(OS),Windows_NT)
	@if not exist "temp\safestic-test" mkdir "temp\safestic-test"
	@echo Arquivo de teste - %date% %time% > "temp\safestic-test\teste.txt"
	@set BACKUP_SOURCE_DIRS=temp\safestic-test&& set RESTIC_TAGS=teste&& $(PYTHON_CMD) restic_backup.py
	@if exist "temp\safestic-test" rmdir /s /q "temp\safestic-test"
else
	mkdir -p /tmp/safestic-test
	echo "Arquivo de teste - $$(date)" > /tmp/safestic-test/teste.txt
	BACKUP_SOURCE_DIRS=/tmp/safestic-test RESTIC_TAGS=teste $(PYTHON_CMD) restic_backup.py
	rm -rf /tmp/safestic-test
endif
	@echo "Backup de teste concluido"

## Restaura para diretorio temporario (teste)
test-restore:
	@echo "Testando restauracao..."
ifeq ($(OS),Windows_NT)
	@if exist "temp\safestic-restore-test" rmdir /s /q "temp\safestic-restore-test"
	@if not exist "temp\safestic-restore-test" mkdir "temp\safestic-restore-test"
	@set RESTORE_TARGET_DIR=temp\safestic-restore-test&& $(PYTHON_CMD) restore_snapshot.py
	@dir "temp\safestic-restore-test"
else
	rm -rf /tmp/safestic-restore-test
	mkdir -p /tmp/safestic-restore-test
	RESTORE_TARGET_DIR=/tmp/safestic-restore-test $(PYTHON_CMD) restore_snapshot.py
	ls -la /tmp/safestic-restore-test
endif
	@echo "Teste de restauracao concluido"

## Limpa arquivos temporarios e logs antigos
clean:
	@echo "Limpando arquivos temporarios..."
ifeq ($(OS),Windows_NT)
	@if exist "logs" forfiles /p logs /m *.log /d -30 /c "cmd /c del @path" 2>nul || echo "Nenhum log antigo encontrado"
	@if exist "temp" rmdir /s /q "temp" 2>nul || echo "Diretorio temp nao existe"
else
	find logs -name "*.log" -mtime +30 -delete 2>/dev/null || true
	rm -rf /tmp/safestic-* 2>/dev/null || true
endif
	@echo "Limpeza concluida"

# Agendamento simplificado - FASE 4
## Instala tarefas agendadas (versao simplificada)
schedule-install:
	@echo "Instalando tarefas agendadas..."
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -File "scripts/schedule.ps1" install
else
	@bash "scripts/schedule.sh" install
endif

## Remove tarefas agendadas (versao simplificada)
schedule-remove:
	@echo "Removendo tarefas agendadas..."
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -File "scripts/schedule.ps1" remove
else
	@bash "scripts/schedule.sh" remove
endif

## Mostra status das tarefas agendadas (versao simplificada)
schedule-status:
	@echo "Verificando status das tarefas agendadas..."
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -File "scripts/schedule.ps1" status
else
	@bash "scripts/schedule.sh" status
endif

## Executa backup manualmente (mesmo script das tarefas agendadas)
backup-task:
	@echo "Executando backup via script de tarefa..."
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -File "scripts\backup_task.ps1"
else
	@bash scripts/backup_task.sh
endif

## Executa prune manualmente (mesmo script das tarefas agendadas)
prune-task:
	@echo "Executando prune via script de tarefa..."
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -File "scripts\prune_task.ps1"
else
	@bash scripts/prune_task.sh
endif

# Novos targets - FASE 4
setup:
	@echo "Executando setup do ambiente..."
ifeq ($(OS),Windows_NT)
	@if exist "scripts\bootstrap_windows.ps1" ( \
		powershell -ExecutionPolicy Bypass -File "scripts\bootstrap_windows.ps1" \
	) else if exist "scripts\setup_windows.sh" ( \
		bash "scripts\setup_windows.sh" --assume-yes \
	) else ( \
		echo "Erro: Scripts de setup nao encontrados" && exit 1 \
	)
else
	@if [ -f "scripts/setup_linux.sh" ]; then \
		bash "scripts/setup_linux.sh" --assume-yes; \
	else \
		echo "Erro: Script de setup Linux nao encontrado"; \
		exit 1; \
	fi
endif
	@echo "Verificando credenciais apos setup..."
	@$(PYTHON_CMD) scripts/check_credentials.py --quiet || (echo "" && echo "AVISO: Configure as credenciais com: make setup-credentials" && echo "")

bootstrap:
	@echo "Executando bootstrap completo..."
ifeq ($(OS),Windows_NT)
	@if exist "scripts\bootstrap_windows.ps1" ( \
		powershell -ExecutionPolicy Bypass -File "scripts\bootstrap_windows.ps1" \
	) else ( \
		echo "Erro: bootstrap_windows.ps1 nao encontrado" && exit 1 \
	)
else
	@echo "Bootstrap nao implementado para Linux. Use: make setup"
	@exit 1
endif
	@echo "Verificando credenciais apos bootstrap..."
	@$(PYTHON_CMD) scripts/check_credentials.py --quiet || (echo "" && echo "AVISO: Configure as credenciais com: make setup-credentials" && echo "")

first-run:
	@echo "Executando primeira configuracao..."
	@echo "1. Verificando arquivo .env..."
	@powershell -Command "if (-not (Test-Path '.env')) { Write-Host 'Copiando .env.example para .env...'; Copy-Item '.env.example' '.env'; Write-Host 'ATENCAO: Configure o arquivo .env antes de continuar!' } else { Write-Host '.env ja existe' }"
	@echo "2. Verificando credenciais..."
	@$(PYTHON_CMD) scripts/check_credentials.py || (echo "" && echo "ERRO: Credenciais nao configuradas!" && echo "Execute: make setup-credentials" && echo "" && exit 1)
	@echo "3. Validando configuracao..."
	$(PYTHON_CMD) scripts/validate_config.py
	@echo "4. Inicializando repositorio (se necessario)..."
	@$(MAKE) init || echo "Repositorio ja existe ou erro na inicializacao"
	@echo "5. Executando verificacao..."
	@$(MAKE) check
	@echo "Primeira configuracao concluida!"

# Comandos de agendamento removidos - usar schedule-install, schedule-remove, schedule-status da secao simplificada

# Operacoes avancadas do Restic
forget:
	@echo "Esquecendo snapshots baseado na politica de retencao..."
	$(PYTHON_CMD) scripts/forget_snapshots.py

mount:
	@echo "Montando repositorio como sistema de arquivos..."
	@echo "ATENCAO: Esta operacao requer FUSE (Linux/macOS) ou WinFsp (Windows)"
	$(PYTHON_CMD) scripts/mount_repo.py

unmount:
	@echo "Desmontando repositorio..."
	$(PYTHON_CMD) scripts/unmount_repo.py

rebuild-index:
	@echo "Reconstruindo indice do repositorio..."
	$(PYTHON_CMD) scripts/rebuild_index.py

repair:
	@echo "Reparando repositorio..."
	@echo "ATENCAO: Esta operacao pode ser destrutiva!"
ifeq ($(OS),Windows_NT)
	@set /p confirm="Tem certeza? (y/N): " && if not "!confirm!"=="y" exit 1
	$(PYTHON_CMD) scripts/repair_repo.py
else
	@read -p "Tem certeza? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	$(PYTHON_CMD) scripts/repair_repo.py
endif

# Utilitarios
## Verifica saude completa do sistema
health:
	@echo "Verificando saude completa do sistema..."
	$(PYTHON_CMD) scripts/health_check.py

## Verifica suporte ao comando mount (WinFsp)
check-mount-support:
	@echo "Verificando suporte ao comando mount..."
	$(PYTHON_CMD) scripts/check_mount_support.py

## Valida configuracao completa do setup
validate-setup:
	@echo "Validando configuracao completa do setup..."
	$(PYTHON_CMD) scripts/validate_setup.py

# Configuracao de credenciais
setup-credentials:
	@echo " Configuracao interativa de credenciais..."
	$(PYTHON_CMD) scripts/setup_credentials.py

setup-restic-password:
	@echo " Configuracao do RESTIC_PASSWORD..."
	$(PYTHON_CMD) scripts/setup_credentials.py --restic-only

setup-credentials-env:
	@echo " Configuracao de credenciais no arquivo .env..."
	$(PYTHON_CMD) scripts/setup_credentials.py --source env

setup-credentials-keyring:
	@echo " Configuracao de credenciais no keyring do sistema..."
	$(PYTHON_CMD) scripts/setup_credentials.py --source keyring

## Mostra ajuda com todos os comandos disponiveis
help:
	@echo "SafeStic - Sistema de Backup com Restic"
	@echo ""
	@echo " CONFIGURACAO DE CREDENCIAIS:"
	@echo "  setup-credentials        - Configuracao interativa completa de credenciais"
	@echo "  setup-restic-password    - Configurar apenas RESTIC_PASSWORD"
	@echo "  setup-credentials-env    - Configurar credenciais no arquivo .env"
	@echo "  setup-credentials-keyring - Configurar credenciais no keyring do sistema"
	@echo ""
	@echo " BACKUP:"
	@echo "  backup          - Executa backup completo"
	@echo "  dry-run         - Simula backup sem executar"
	@echo "  test-backup     - Testa backup com dados de exemplo"
	@echo ""
	@echo " LISTAGEM E CONSULTA:"
	@echo "  list            - Lista snapshots disponiveis"
	@echo "  list-size       - Lista snapshots com tamanhos"
	@echo "  list-files      - Lista arquivos no ultimo snapshot"
	@echo "  stats           - Mostra estatisticas do repositorio"
	@echo "  repo-size       - Mostra tamanho do repositorio"
	@echo ""
	@echo " RESTAURACAO:"
	@echo "  restore         - Restaura ultimo snapshot"
	@echo "  restore-id      - Restaura snapshot especifico (ID=snapshot_id)"
	@echo "  restore-file    - Restaura arquivo especifico (FILE=caminho/arquivo)"
	@echo "  test-restore    - Testa restauracao com dados de exemplo"
	@echo ""
	@echo " MANUTENCAO:"
	@echo "  prune           - Remove snapshots antigos (automatico)"
	@echo "  manual-prune    - Remove snapshots antigos manualmente"
	@echo "  forget          - Esquece snapshots baseado na politica"
	@echo "  check           - Verifica integridade do repositorio"
	@echo "  rebuild-index   - Reconstroi indice do repositorio"
	@echo "  repair          - Repara repositorio (CUIDADO!)"
	@echo "  clean           - Limpa logs e arquivos temporarios"
	@echo ""
	@echo "  CONFIGURACAO:"
	@echo "  setup           - Instala dependencias do sistema"
	@echo "  bootstrap       - Bootstrap completo (Windows)"
	@echo "  first-run       - Primeira configuracao do projeto"
	@echo "  init            - Inicializa novo repositorio"
	@echo "  validate        - Valida configuracao e dependencias"
	@echo "  validate-setup  - Valida setup completo"
	@echo "  health          - Verifica saude do sistema"
	@echo ""
	@echo " AGENDAMENTO:"
	@echo "  schedule-install - Instala agendamento automatico"
	@echo "  schedule-remove  - Remove agendamento automatico"
	@echo "  schedule-status  - Status do agendamento"
	@echo ""
	@echo "  AVANCADO:"
	@echo "  mount           - Monta repositorio como filesystem"
	@echo "  unmount         - Desmonta repositorio"
	@echo ""
	@echo " EXEMPLOS DE USO:"
	@echo "  make setup-credentials     # Configuracao interativa completa"
	@echo "  make setup-restic-password # Configurar apenas a senha do Restic"
	@echo "  make first-run            # Primeira configuracao do projeto"
	@echo "  make backup               # Fazer backup"
	@echo ""
	@echo " AJUDA:"
	@echo "  help            - Mostra esta ajuda"
