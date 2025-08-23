# Verificar se ambiente virtual existe e usar se disponivel
ifeq ($(OS),Windows_NT)
PYTHON_CMD=$(if $(wildcard .venv\Scripts\python.exe),$(VENV_PYTHON),$(PYTHON))
else
PYTHON_CMD=$(if $(wildcard .venv/bin/python),$(VENV_PYTHON),$(PYTHON))
endif

# Macros para verificacao de credenciais
CHECK_RESTIC_CREDS = @$(PYTHON_CMD) scripts/check_credentials.py --restic-only --quiet || (echo "" && echo "ERRO: RESTIC_PASSWORD nao configurado!" && echo "Execute: make setup-restic-password" && echo "" && exit 1)
CHECK_ALL_CREDS = @$(PYTHON_CMD) scripts/check_credentials.py --quiet || (echo "" && echo "AVISO: Algumas credenciais nao estao configuradas. Opcoes disponiveis:" && echo "  make setup-credentials        - Configuracao interativa (escolha keyring ou .env)" && echo "  make setup-credentials-keyring - Keyring do sistema (mais seguro)" && echo "  make setup-credentials-env    - Arquivo .env (menos seguro)" && echo "")
CHECK_ALL_CREDS_REQUIRED = @$(PYTHON_CMD) scripts/check_credentials.py || (echo "" && echo "ERRO: Credenciais nao configuradas!" && echo "Opcoes disponiveis:" && echo "  make setup-credentials        - Configuracao interativa (escolha keyring ou .env)" && echo "  make setup-credentials-keyring - Keyring do sistema (mais seguro)" && echo "  make setup-credentials-env    - Arquivo .env (menos seguro)" && echo "" && exit 1)

# Helpers para execucao Python com funcao centralizada
PYTHON_WITH_CREDS = $(PYTHON_CMD) -c "from services.restic_client import ResticClient, load_env_and_get_credential_source; credential_source = load_env_and_get_credential_source(); client = ResticClient(credential_source=credential_source)"
PYTHON_WITH_CONFIG = $(PYTHON_CMD) -c "from services.restic_client import load_env_and_get_credential_source; from services.restic import load_restic_config; credential_source = load_env_and_get_credential_source(); config = load_restic_config(credential_source)"

# Macros para comandos específicos do OS
ifeq ($(OS),Windows_NT)
RUN_SCHEDULE_SCRIPT = @powershell -ExecutionPolicy Bypass -File "scripts/schedule.ps1"
RUN_BACKUP_TASK = @powershell -ExecutionPolicy Bypass -File "scripts\backup_task.ps1"
RUN_PRUNE_TASK = @powershell -ExecutionPolicy Bypass -File "scripts\prune_task.ps1"
CREATE_TEST_DIR = @if not exist "temp\safestic-test" mkdir "temp\safestic-test"
CREATE_TEST_FILE = @echo Arquivo de teste - %date% %time% > "temp\safestic-test\teste.txt"
CLEAN_TEST_DIR = @if exist "temp\safestic-test" rmdir /s /q "temp\safestic-test"
CLEAN_LOGS = @if exist "logs" forfiles /p logs /m *.log /d -30 /c "cmd /c del @path" 2>nul || echo "Nenhum log antigo encontrado"
CLEAN_TEMP = @if exist "temp" rmdir /s /q "temp" 2>nul || echo "Diretorio temp nao existe"
else
RUN_SCHEDULE_SCRIPT = @bash "scripts/schedule.sh"
RUN_BACKUP_TASK = @bash scripts/backup_task.sh
RUN_PRUNE_TASK = @bash scripts/prune_task.sh
CREATE_TEST_DIR = mkdir -p /tmp/safestic-test
CREATE_TEST_FILE = echo "Arquivo de teste - $$(date)" > /tmp/safestic-test/teste.txt
CLEAN_TEST_DIR = rm -rf /tmp/safestic-test
CLEAN_LOGS = find logs -name "*.log" -mtime +30 -delete 2>/dev/null || true
CLEAN_TEMP = rm -rf /tmp/safestic-* 2>/dev/null || true
endif

# Macros para mensagens comuns
ECHO_CHECKING_CREDS = @echo "Verificando credenciais..."
ECHO_CHECKING_CONFIG = @echo "Verificando configuracao..."
ECHO_CHECKING_INTEGRITY = @echo "Verificando integridade..."
ECHO_LISTING_SNAPSHOTS = @echo "Listando snapshots..."
ECHO_OPERATION_COMPLETE = @echo "Operacao concluida"

.PHONY: backup list restore restore-id restore-file list-files manual-prune check help init dry-run stats validate test-backup test-restore clean prune

.DEFAULT_GOAL := help

## Executa o backup com base nas variaveis do .env
backup:
> @echo "Executando backup com Restic..."
> $(ECHO_CHECKING_CREDS)
> $(CHECK_RESTIC_CREDS)
> $(PYTHON_CMD) restic_backup.py

## Lista todos os snapshots no repositorio
list:
> $(ECHO_LISTING_SNAPSHOTS)
> $(PYTHON_CMD) list_snapshots.py

## Lista todos os snapshots com tamanho estimado
list-size:
> @echo "Listando snapshots com tamanho estimado..."
> $(PYTHON_CMD) list_snapshots_with_size.py

## Lista arquivos contidos em um snapshot especifico
## Exemplos:
##   make list-files ID=abc123                    # Saida em texto no terminal
##   make list-files ID=abc123 FORMAT=json        # Saida em JSON no terminal
##   make list-files ID=abc123 FORMAT=json OUTPUT=files.json  # Salvar JSON em arquivo
##   make list-files ID=abc123 PRETTY=1           # Formatacao legivel para humanos
list-files:
ifndef ID
> $(error Voce precisa passar o ID do snapshot: make list-files ID=abc123)
endif
> @echo "Listando arquivos do snapshot ID=$(ID)..."
> $(PYTHON_CMD) list_snapshot_files.py --id $(ID)$(if $(FORMAT), --format $(FORMAT))$(if $(OUTPUT), --output $(OUTPUT))$(if $(PRETTY), --pretty)

## Restaura o snapshot mais recente (default = latest)
## Cria estrutura: C:\Restore\AAAA-MM-DD-HHMMSS\<estrutura_original>
restore:
> @echo "Restaurando o ultimo snapshot..."
> $(CHECK_RESTIC_CREDS)
> $(PYTHON_CMD) restore_snapshot.py

## Restaura snapshot especifico (ex: make restore-id ID=abc123)
## Cria estrutura: C:\Restore\AAAA-MM-DD-HHMMSS\<estrutura_original>
restore-id:
ifndef ID
> $(error Voce precisa passar o ID do snapshot: make restore-id ID=abc123)
endif
> @echo "Restaurando snapshot ID=$(ID)..."
> $(CHECK_RESTIC_CREDS)
> $(PYTHON_CMD) restore_snapshot.py --id $(ID)

## Restaura arquivo especifico (ex: make restore-file ID=abc123 FILE="C:\Users\Admin\Documents")
## Cria estrutura: C:\Restore\AAAA-MM-DD-HHMMSS\C\Users\Admin\Documents
## Onde AAAA-MM-DD-HHMMSS corresponde à data/hora do snapshot
restore-file:
ifndef ID
> $(error Voce precisa passar o ID do snapshot: make restore-file ID=abc123 FILE="/caminho")
endif
ifndef FILE
> $(error Voce precisa passar o caminho do arquivo: make restore-file ID=abc123 FILE="/caminho")
endif
> @echo "Restaurando arquivo $(FILE) do snapshot ID=$(ID)..."
> $(PYTHON_CMD) restore_file.py $(ID) "$(FILE)"

## Aplica retencao manual usando o script Python dedicado
manual-prune:
> @echo "Executando retencao manual via Python..."
> $(PYTHON_CMD) manual_prune.py

## Verifica se Restic esta instalado, variaveis estao corretas e repositorio esta acessivel
## Verifica se o ambiente está configurado corretamente
verify-env:
> @echo "Verificando ambiente de desenvolvimento..."
> $(PYTHON_CMD) scripts/verify_environment.py

check:
> @echo "Executando verificacao da configuracao Restic..."
> $(ECHO_CHECKING_CREDS)
> $(CHECK_ALL_CREDS)
> $(PYTHON_CMD) check_restic_access.py

## Exibe o total de dados unicos armazenados no repositorio
repo-size:
> @echo "Calculando uso real do repositorio..."
> $(PYTHON_CMD) repository_stats.py

## Inicializa repositorio Restic (apenas se nao existir)
init:
> @echo "Inicializando repositorio Restic..."
> $(ECHO_CHECKING_CREDS)
> $(CHECK_RESTIC_CREDS)
> $(PYTHON_WITH_CREDS); exec('try:\n    client.check_repository_access()\n    print("[OK] Repositorio ja existe e esta acessivel")\nexcept Exception as e:\n    try:\n        client.init_repository()\n        print("[OK] Repositorio inicializado com sucesso")\n    except Exception as init_error:\n        print(f"[ERRO] Erro ao inicializar repositorio: {init_error}")\n        raise')"

## Simula backup sem executar (dry-run)
dry-run:
> @echo "Simulando backup (dry-run)..."
> $(PYTHON_WITH_CONFIG); from pathlib import Path; print('Configuracao de backup:'); print(f'Diretorios: {config.backup_source_dirs}'); print(f'Exclusoes: {config.restic_excludes}'); print(f'Tags: {config.restic_tags}'); [print(f'{dir_path} - OK') if Path(dir_path).exists() else print(f'{dir_path} - NAO ENCONTRADO') for dir_path in config.backup_source_dirs]"

## Mostra estatisticas detalhadas do repositorio
stats:
> @echo "Obtendo estatisticas detalhadas..."
> $(PYTHON_WITH_CREDS); import json; stats = client.get_repository_stats(); print(json.dumps(stats, indent=2))"

## Aplica politica de retencao (prune)
prune:
> @echo "Aplicando politica de retencao..."
> $(CHECK_RESTIC_CREDS)
> $(PYTHON_CMD) scripts/forget_snapshots.py

## Executa todos os checks de validacao
validate:
> @echo "Executando validacao completa..."
> @echo "1. Verificando configuracao..."
> $(PYTHON_CMD) scripts/validate_config.py
> @echo "2. $(ECHO_CHECKING_INTEGRITY)"
> $(PYTHON_WITH_CREDS); result = client.check_repository_access(); print('[OK] Repositorio acessivel' if result else '[ERRO] Repositorio inacessivel')"
> @echo "3. Listando snapshots..."
> $(PYTHON_WITH_CREDS); snapshots = client.list_snapshots(); print(f'[INFO] Encontrados {len(snapshots)} snapshots no repositorio'); [print(f'  - {s.get("short_id", s.get("id", "N/A"))[:8]} ({s.get("time", "N/A")}) - {s.get("hostname", "N/A")}') for s in snapshots[:5]]; print('  ...') if len(snapshots) > 5 else None"
> @echo "Validacao concluida"

## Cria backup de teste em diretorio temporario
test-backup:
> @echo "Criando backup de teste..."
> $(CREATE_TEST_DIR)
> $(CREATE_TEST_FILE)
ifeq ($(OS),Windows_NT)
> @set BACKUP_SOURCE_DIRS=temp\safestic-test&& set RESTIC_TAGS=teste&& $(PYTHON_CMD) restic_backup.py
else
> BACKUP_SOURCE_DIRS=/tmp/safestic-test RESTIC_TAGS=teste $(PYTHON_CMD) restic_backup.py
endif
> $(CLEAN_TEST_DIR)
> @echo "Backup de teste concluido"

## Restaura para diretorio temporario (teste)
test-restore:
> @echo "Testando restauracao..."
ifeq ($(OS),Windows_NT)
> @if exist "temp\safestic-restore-test" rmdir /s /q "temp\safestic-restore-test"
> @if not exist "temp\safestic-restore-test" mkdir "temp\safestic-restore-test"
> @set RESTORE_TARGET_DIR=temp\safestic-restore-test&& $(PYTHON_CMD) restore_snapshot.py
> @dir "temp\safestic-restore-test"
else
> rm -rf /tmp/safestic-restore-test
> mkdir -p /tmp/safestic-restore-test
> RESTORE_TARGET_DIR=/tmp/safestic-restore-test $(PYTHON_CMD) restore_snapshot.py
> ls -la /tmp/safestic-restore-test
endif
> @echo "Teste de restauracao concluido"

## Limpa arquivos temporarios e logs antigos
clean:
> @echo "Limpando arquivos temporarios..."
> $(CLEAN_LOGS)
> $(CLEAN_TEMP)
> @echo "Limpeza concluida"

# Agendamento simplificado - FASE 4
## Instala tarefas agendadas (versao simplificada)
schedule-install:
> @echo "Instalando tarefas agendadas..."
> $(RUN_SCHEDULE_SCRIPT) install

## Remove tarefas agendadas (versao simplificada)
schedule-remove:
> @echo "Removendo tarefas agendadas..."
> $(RUN_SCHEDULE_SCRIPT) remove

## Mostra status das tarefas agendadas (versao simplificada)
schedule-status:
> @echo "Verificando status das tarefas agendadas..."
> $(RUN_SCHEDULE_SCRIPT) status

## Executa backup manualmente (mesmo script das tarefas agendadas)
backup-task:
> @echo "Executando backup via script de tarefa..."
> $(RUN_BACKUP_TASK)

## Executa prune manualmente (mesmo script das tarefas agendadas)
prune-task:
> @echo "Executando prune via script de tarefa..."
> $(RUN_PRUNE_TASK)

# Novos targets - FASE 4
setup:
> @echo "Executando setup do ambiente..."
ifeq ($(OS),Windows_NT)
> @powershell -Command "if (Test-Path 'scripts\bootstrap_windows.ps1') { powershell -ExecutionPolicy Bypass -File 'scripts\bootstrap_windows.ps1' } elseif (Test-Path 'scripts\setup_windows.sh') { bash 'scripts\setup_windows.sh' --assume-yes } else { Write-Host 'Erro: Scripts de setup nao encontrados'; exit 1 }"
else
> @if [ -f "scripts/setup_linux.sh" ]; then \
> bash "scripts/setup_linux.sh" --assume-yes; \
else \
> echo "Erro: Script de setup Linux nao encontrado"; \
> exit 1; \
> fi
endif
> @echo "Verificando credenciais apos setup..."
> $(CHECK_ALL_CREDS)

bootstrap:
> @echo "Executando bootstrap completo..."
ifeq ($(OS),Windows_NT)
> @if exist "scripts\bootstrap_windows.ps1" ( \
> powershell -ExecutionPolicy Bypass -File "scripts\bootstrap_windows.ps1" \
> ) else ( \
> echo "Erro: bootstrap_windows.ps1 nao encontrado" && exit 1 \
> )
else
> @if [ -f "scripts/bootstrap_linux.sh" ]; then \
> chmod +x scripts/bootstrap_linux.sh; \
> bash scripts/bootstrap_linux.sh; \
else \
> echo "Erro: bootstrap_linux.sh nao encontrado" && exit 1; \
> fi
endif

bootstrap-auto:
> @echo "Executando bootstrap automatico (sem interacao)..."
ifeq ($(OS),Windows_NT)
> @if exist "scripts\bootstrap_windows.ps1" ( \
> powershell -ExecutionPolicy Bypass -File "scripts\bootstrap_windows.ps1" -AssumeYes \
> ) else ( \
> echo "Erro: bootstrap_windows.ps1 nao encontrado" && exit 1 \
> )
else
> @if [ -f "scripts/bootstrap_linux.sh" ]; then \
> chmod +x scripts/bootstrap_linux.sh; \
> bash scripts/bootstrap_linux.sh --assume-yes; \
else \
> echo "Erro: bootstrap_linux.sh nao encontrado" && exit 1; \
> fi
endif
> @echo "Verificando credenciais apos bootstrap..."
> $(CHECK_ALL_CREDS)

first-run:
> @echo "Executando primeira configuracao..."
> @echo "1. Verificando arquivo .env..."
> @powershell -Command "if (-not (Test-Path '.env')) { Write-Host 'Copiando .env.example para .env...'; Copy-Item '.env.example' '.env'; Write-Host 'ATENCAO: Configure o arquivo .env antes de continuar!' } else { Write-Host '.env ja existe' }"
> @echo "2. $(ECHO_CHECKING_CREDS)"
> $(CHECK_ALL_CREDS_REQUIRED)
> @echo "3. $(ECHO_CHECKING_CONFIG)"
> $(PYTHON_CMD) scripts/validate_config.py
> @echo "4. Inicializando repositorio (se necessario)..."
> @$(MAKE) init || echo "Repositorio ja existe ou erro na inicializacao"
> @echo "5. Executando verificacao..."
> @$(MAKE) check
> @echo "Primeira configuracao concluida!"

# Comandos de agendamento removidos - usar schedule-install, schedule-remove, schedule-status da secao simplificada

# Operacoes avancadas do Restic
forget:
> @echo "Esquecendo snapshots baseado na politica de retencao..."
> $(PYTHON_CMD) scripts/forget_snapshots.py

mount:
> @echo "Montando repositorio como sistema de arquivos..."
> @echo "ATENCAO: Esta operacao requer FUSE (Linux/macOS) ou WinFsp (Windows)"
> $(PYTHON_CMD) scripts/mount_repo.py

unmount:
> @echo "Desmontando repositorio..."
> $(PYTHON_CMD) scripts/unmount_repo.py

rebuild-index:
> @echo "Reconstruindo indice do repositorio..."
> $(PYTHON_CMD) scripts/rebuild_index.py

repair:
> @echo "Reparando repositorio..."
> @echo "ATENCAO: Esta operacao pode ser destrutiva!"
ifeq ($(OS),Windows_NT)
> @set /p confirm="Tem certeza? (y/N): " && if not "!confirm!"=="y" exit 1
> $(PYTHON_CMD) scripts/repair_repo.py
else
> @read -p "Tem certeza? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
> $(PYTHON_CMD) scripts/repair_repo.py
endif

# Utilitarios
## Verifica saude completa do sistema
health:
> @echo "Verificando saude completa do sistema..."
> $(PYTHON_CMD) scripts/health_check.py

## Verifica suporte ao comando mount (WinFsp)
check-mount-support:
> @echo "Verificando suporte ao comando mount..."
> $(PYTHON_CMD) scripts/check_mount_support.py

## Valida configuracao completa do setup
validate-setup:
> @echo "Validando configuracao completa do setup..."
> $(PYTHON_CMD) scripts/validate_setup.py

# Configuracao de credenciais
setup-credentials:
> @echo " Configuracao interativa de credenciais..."
> $(PYTHON_CMD) scripts/setup_credentials.py

setup-restic-password:
> @echo " Configuracao do RESTIC_PASSWORD..."
> $(PYTHON_CMD) scripts/setup_credentials.py --restic-only

setup-credentials-env:
> @echo " Configuracao de credenciais no arquivo .env..."
> $(PYTHON_CMD) scripts/setup_credentials.py --source env

setup-credentials-keyring:
> @echo " Configuracao de credenciais no keyring do sistema..."
> $(PYTHON_CMD) scripts/setup_credentials.py --source keyring

# Comandos de diagnóstico e troubleshooting
diagnose:
> @echo "Executando diagnostico completo..."
> $(ECHO_CHECKING_CONFIG)
> $(PYTHON_CMD) scripts/validate_config.py
> @echo "Verificando acesso ao repositorio..."
> $(PYTHON_CMD) check_restic_access.py

diagnose-azure-linux:
> @echo "Executando diagnostico Azure para Linux..."
> $(PYTHON_CMD) scripts/diagnose_azure_linux.py

test-azure-keyring:
> @echo "Testando credenciais Azure no keyring..."
> $(PYTHON_CMD) tests/test_azure_keyring.py

generate-config-report:
> @echo "Gerando relatorio de configuracao do sistema atual..."
> $(PYTHON_CMD) scripts/compare_configs.py --generate

compare-configs:
> @echo "Para comparar configuracoes, use:"
> @echo "  make generate-config-report  # Gerar relatorio atual"
> @echo "  python scripts/compare_configs.py --compare arquivo1.json arquivo2.json"
> @echo ""
> @echo "Exemplo de uso:"
> @echo "  1. No Windows: make generate-config-report"
> @echo "  2. No Linux: make generate-config-report"
> @echo "  3. Comparar: python scripts/compare_configs.py --compare config_report_windows_*.json config_report_linux_*.json"

## Mostra ajuda com todos os comandos disponiveis
help:
> @echo "SafeStic - Sistema de Backup com Restic"
> @echo ""
> @echo " CONFIGURACAO DE CREDENCIAIS:"
> @echo "  setup-credentials        - Configuracao interativa completa de credenciais"
> @echo "  setup-restic-password    - Configurar apenas RESTIC_PASSWORD"
> @echo "  setup-credentials-env    - Configurar credenciais no arquivo .env"
> @echo "  setup-credentials-keyring - Configurar credenciais no keyring do sistema"
> @echo ""
> @echo " BACKUP:"
> @echo "  backup          - Executa backup completo"
> @echo "  dry-run         - Simula backup sem executar"
> @echo "  test-backup     - Testa backup com dados de exemplo"
> @echo ""
> @echo " LISTAGEM E CONSULTA:"
> @echo "  list            - Lista snapshots disponiveis"
> @echo "  list-size       - Lista snapshots com tamanhos"
> @echo "  list-files      - Lista arquivos no ultimo snapshot"
> @echo "  stats           - Mostra estatisticas do repositorio"
> @echo "  repo-size       - Mostra tamanho do repositorio"
> @echo ""
> @echo " RESTAURACAO:"
> @echo "  restore         - Restaura ultimo snapshot"
> @echo "  restore-id      - Restaura snapshot especifico (ID=snapshot_id)"
> @echo "  restore-file    - Restaura arquivo especifico (FILE=caminho/arquivo)"
> @echo "  test-restore    - Testa restauracao com dados de exemplo"
> @echo ""
> @echo " MANUTENCAO:"
> @echo "  prune           - Remove snapshots antigos (automatico)"
> @echo "  manual-prune    - Remove snapshots antigos manualmente"
> @echo "  forget          - Esquece snapshots baseado na politica"
> @echo "  check           - Verifica integridade do repositorio"
> @echo "  rebuild-index   - Reconstroi indice do repositorio"
> @echo "  repair          - Repara repositorio (CUIDADO!)"
> @echo "  clean           - Limpa logs e arquivos temporarios"
> @echo ""
> @echo " CONFIGURACAO:"
> @echo "  setup           - Instala dependencias do sistema"
> @echo "  bootstrap       - Bootstrap completo (Windows/Linux)"
> @echo "  bootstrap-auto  - Bootstrap automatico sem interacao"
> @echo "  first-run       - Primeira configuracao do projeto"
> @echo "  init            - Inicializa novo repositorio"
> @echo "  verify-env      - Verifica ambiente de desenvolvimento"
> @echo "  validate        - Valida configuracao e dependencias"
> @echo "  validate-setup  - Valida setup completo"
> @echo "  health          - Verifica saude do sistema"
> @echo ""
> @echo " AGENDAMENTO:"
> @echo "  schedule-install - Instala agendamento automatico"
> @echo "  schedule-remove  - Remove agendamento automatico"
> @echo "  schedule-status  - Status do agendamento"
> @echo ""
> @echo " DIAGNOSTICO E TROUBLESHOOTING:"
> @echo "  diagnose              - Diagnostico completo do sistema"
> @echo "  diagnose-azure-linux  - Diagnostico especifico Azure no Linux"
> @echo "  test-azure-keyring    - Testa credenciais Azure no keyring"
> @echo "  generate-config-report - Gera relatorio de configuracao"
> @echo "  compare-configs       - Instrucoes para comparar configuracoes"
> @echo ""
> @echo "  AVANCADO:"
> @echo "  mount           - Monta repositorio como filesystem"
> @echo "  unmount         - Desmonta repositorio"
> @echo ""
> @echo " EXEMPLOS DE USO:"
> @echo "  make setup-credentials     # Configuracao interativa completa"
> @echo "  make setup-restic-password # Configurar apenas a senha do Restic"
> @echo "  make first-run            # Primeira configuracao do projeto"
> @echo "  make backup               # Fazer backup"
> @echo ""
> @echo " AJUDA:"
> @echo "  help            - Mostra esta ajuda"

