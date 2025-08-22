# Correção Rápida - Problemas Azure no Linux

## Problemas Identificados e Soluções

### 1. ❌ Erro: `validate_config.py: No such file or directory`

**Problema:** O comando `make diagnose` estava tentando executar `validate_config.py` na raiz, mas o arquivo está em `scripts/validate_config.py`.

**✅ Solução:** Corrigido no Makefile
```makefile
# Antes
$(PYTHON_CMD) validate_config.py

# Depois  
$(PYTHON_CMD) scripts/validate_config.py
```

### 2. ❌ Erro: `syntax error near unexpected token '('` no Windows

**Problema:** Sintaxe incorreta das condicionais do Windows no Makefile.

**✅ Solução:** Corrigido para usar PowerShell nativo
```makefile
# Antes (sintaxe inválida)
@if exist "scripts\bootstrap_windows.ps1" ( \
	powershell -ExecutionPolicy Bypass -File "scripts\bootstrap_windows.ps1" \
) else if exist "scripts\setup_windows.sh" ( \
	bash "scripts\setup_windows.sh" --assume-yes \
) else ( \
	echo "Erro: Scripts de setup nao encontrados" && exit 1 \
)

# Depois (PowerShell nativo)
@powershell -Command "if (Test-Path 'scripts\bootstrap_windows.ps1') { powershell -ExecutionPolicy Bypass -File 'scripts\bootstrap_windows.ps1' } elseif (Test-Path 'scripts\setup_windows.sh') { bash 'scripts\setup_windows.sh' --assume-yes } else { Write-Host 'Erro: Scripts de setup nao encontrados'; exit 1 }"
```

### 3. ❌ Erro: `python-dotenv: NÃO INSTALADO` no Linux

**Problema:** Dependência `python-dotenv` não instalada no ambiente virtual Linux.

**✅ Solução:** Instalar dependências
```bash
# No Linux
source .venv/bin/activate
pip install -r requirements.txt
# ou
pip install python-dotenv
```

### 4. ❌ Credenciais Azure não carregadas do keyring

**Problema:** Variáveis `AZURE_ACCOUNT_NAME`, `AZURE_ACCOUNT_KEY`, `RESTIC_PASSWORD` não definidas.

**✅ Soluções:**

#### Opção A: Configurar credenciais no keyring
```bash
make setup-credentials
# ou
python scripts/setup_credentials.py --source keyring
```

#### Opção B: Usar arquivo .env (menos seguro)
```bash
# Editar .env
CREDENTIAL_SOURCE=env
AZURE_ACCOUNT_NAME=sua_conta_azure
AZURE_ACCOUNT_KEY=sua_chave_azure
RESTIC_PASSWORD=sua_senha_restic
```

#### Opção C: Verificar keyring no Linux
```bash
# Testar keyring
make test-azure-keyring

# Se keyring não funcionar, instalar dependências
sudo apt-get update
sudo apt-get install -y python3-keyring gnome-keyring

# Ou usar backend alternativo
pip install keyrings.alt
```

## Comandos de Diagnóstico Adicionados

### Novos comandos disponíveis:

```bash
# Diagnóstico completo (corrigido)
make diagnose

# Diagnóstico específico Azure Linux
make diagnose-azure-linux

# Teste específico do keyring Azure
make test-azure-keyring

# Gerar relatório de configuração
make generate-config-report

# Comparar configurações entre sistemas
make compare-configs
```

## Fluxo de Correção Recomendado

### No Linux:

1. **Instalar dependências:**
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Testar diagnóstico:**
   ```bash
   make diagnose
   ```

3. **Configurar credenciais:**
   ```bash
   make setup-credentials
   ```

4. **Testar keyring:**
   ```bash
   make test-azure-keyring
   ```

5. **Verificar Azure:**
   ```bash
   make diagnose-azure-linux
   ```

### No Windows:

1. **Testar setup corrigido:**
   ```powershell
   make setup
   ```

2. **Verificar funcionamento:**
   ```powershell
   make diagnose
   ```

## Comparação de Configurações

### Para identificar diferenças entre Windows e Linux:

```bash
# No Windows
make generate-config-report

# No Linux  
make generate-config-report

# Comparar
python scripts/compare_configs.py --compare config_report_windows_*.json config_report_linux_*.json
```

## Verificação Final

Após aplicar as correções, execute:

```bash
# Diagnóstico completo
make diagnose

# Se Azure, teste específico
make diagnose-azure-linux

# Teste de inicialização
make init

# Teste de backup
make dry-run
```

## Problemas Conhecidos

### Linux + Docker + Azure
- **Conectividade:** Verificar se o container tem acesso à internet
- **Keyring:** Pode não funcionar em containers - usar `CREDENTIAL_SOURCE=env`
- **Encoding:** Diferenças entre Windows e Linux podem afetar credenciais

### Soluções para Container Docker:
```bash
# No container, usar .env em vez de keyring
echo "CREDENTIAL_SOURCE=env" >> .env

# Configurar credenciais diretamente
echo "AZURE_ACCOUNT_NAME=sua_conta" >> .env
echo "AZURE_ACCOUNT_KEY=sua_chave" >> .env
echo "RESTIC_PASSWORD=sua_senha" >> .env
```

## Logs e Debug

Para debug avançado:
```bash
# Logs detalhados
export LOG_LEVEL=DEBUG
make diagnose-azure-linux

# Teste manual do restic
restic -r azure:seu-container:restic snapshots
```

---

**Nota:** Todas as correções foram aplicadas automaticamente. Os comandos `make diagnose`, `make setup` e os novos comandos de diagnóstico devem funcionar corretamente agora.