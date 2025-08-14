# 🛡️ Guia de Configuracao do Safestic

**Safestic** e uma solucao completa de backup automatizado baseada no Restic, com suporte multiplataforma para Windows e Linux.

## 📋 indice

- [Pre-requisitos](#-pre-requisitos)
- [Instalacao Rapida](#-instalacao-rapida)
- [Instalacao Manual](#-instalacao-manual)
- [Configuracao](#-configuracao)
- [Primeiros Passos](#-primeiros-passos)
- [Agendamento Automatico](#-agendamento-automatico)
- [Comandos Disponiveis](#-comandos-disponiveis)
- [Variaveis de Ambiente](#-variaveis-de-ambiente)
- [Troubleshooting](#-troubleshooting)
- [Manutencao](#-manutencao)

## 🔧 Pre-requisitos

### Requisitos Minimos
- **Python**: 3.10 ou superior
- **Git**: Para clonagem do repositorio
- **Make**: Para execucao dos comandos
- **Restic**: Ferramenta de backup (sera instalado automaticamente)

### Sistemas Suportados
- ✅ **Windows 10/11** (PowerShell 5.1+)
- ✅ **Linux** (Ubuntu, Debian, Fedora, CentOS, Arch, openSUSE)
- ✅ **macOS** (via scripts Linux)

## 🚀 Instalacao Rapida

### Windows (Recomendado)

1. **Clone o repositorio:**
   ```powershell
   git clone <url-do-repositorio> safestic
   cd safestic
   ```

2. **Execute o bootstrap (instala tudo automaticamente):**
   ```powershell
   # Como Administrador (recomendado)
   powershell -ExecutionPolicy Bypass -File scripts\bootstrap_windows.ps1
   
   # OU usando Make (se ja tiver instalado)
   make bootstrap
   ```

3. **Configure e execute primeira vez:**
   ```powershell
   make first-run
   ```

### Linux

1. **Clone o repositorio:**
   ```bash
   git clone <url-do-repositorio> safestic
   cd safestic
   ```

2. **Execute o setup:**
   ```bash
   # Instala dependencias automaticamente
   make setup
   
   # OU manualmente
   bash scripts/setup_linux.sh --assume-yes
   ```

3. **Configure e execute primeira vez:**
   ```bash
   make first-run
   ```

## 🔨 Instalacao Manual

### Windows - Passo a Passo

1. **Instalar dependencias:**
   ```powershell
   # Instalar Git (se nao tiver)
   winget install Git.Git
   
   # Instalar Python 3.10+
   winget install Python.Python.3.12
   
   # Instalar Make (via Git for Windows ou MSYS2)
   winget install Git.Git  # Inclui Git Bash com Make
   ```

2. **Instalar Restic:**
   ```powershell
   # Via Chocolatey
   choco install restic
   
   # OU via Winget
   winget install restic.restic
   
   # OU download manual de: https://github.com/restic/restic/releases
   ```

3. **Configurar projeto:**
   ```powershell
   git clone <url-do-repositorio> safestic
   cd safestic
   pip install -r requirements.txt
   ```

### Linux - Passo a Passo

#### Ubuntu/Debian
```bash
# Atualizar sistema
sudo apt update

# Instalar dependencias
sudo apt install -y git make python3 python3-pip python3-venv curl bzip2

# Instalar Restic
sudo apt install -y restic
# OU download manual se nao estiver disponivel
```

#### Fedora/CentOS/RHEL
```bash
# Instalar dependencias
sudo dnf install -y git make python3 python3-pip curl bzip2

# Instalar Restic
sudo dnf install -y restic
```

#### Arch/Manjaro
```bash
# Instalar dependencias
sudo pacman -S git make python python-pip curl bzip2 restic
```

## ⚙️ Configuracao

### 1. Arquivo de Configuracao (.env)

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configuracoes
nano .env  # Linux
notepad .env  # Windows
```

### 2. Configuracoes Essenciais

**Configuracao minima necessaria:**

```env
# Provedor de armazenamento
STORAGE_PROVIDER=local  # ou aws, azure, gcp

# Para armazenamento local
STORAGE_BUCKET=/caminho/para/backup  # Linux
STORAGE_BUCKET=C:\Backups\Safestic   # Windows

# Senha do repositorio (IMPORTANTE: guarde com seguranca!)
RESTIC_PASSWORD=sua_senha_super_segura_aqui

# Diretorios para backup (separados por virgula)
BACKUP_SOURCE_DIRS=/home/usuario/Documentos,/home/usuario/Projetos
# Windows: BACKUP_SOURCE_DIRS=C:\Users\Usuario\Documents,C:\Users\Usuario\Desktop

# Diretorio de logs
LOG_DIR=./logs
```

### 3. Configuracoes de Nuvem (Opcional)

#### AWS S3
```env
STORAGE_PROVIDER=aws
STORAGE_BUCKET=meu-bucket-backup
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
AWS_DEFAULT_REGION=us-east-1
```

#### Azure Blob Storage
```env
STORAGE_PROVIDER=azure
STORAGE_BUCKET=meu-container
AZURE_ACCOUNT_NAME=minha_conta
AZURE_ACCOUNT_KEY=minha_chave
```

#### Google Cloud Storage
```env
STORAGE_PROVIDER=gcp
STORAGE_BUCKET=meu-bucket-gcp
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credenciais.json
```

### 4. 🔐 Configuração Segura de Senhas (RESTIC_PASSWORD)

O `RESTIC_PASSWORD` é **obrigatório** e criptografa todos os seus backups. **NUNCA perca esta senha** - sem ela, seus backups serão irrecuperáveis!

#### Configuração Interativa (Recomendado)
```bash
# Configuração completa
make setup-credentials

# Apenas RESTIC_PASSWORD
make setup-restic-password
```

#### Opção 1: Arquivo .env (Básico)
```env
# No arquivo .env
RESTIC_PASSWORD=MinhaSenh@Muito$egura123!
```

⚠️ **Atenção**: Mantenha o arquivo `.env` seguro e nunca o commite em repositórios Git!

#### Verificação Automática

O Safestic verifica automaticamente se as credenciais estão configuradas:

- **Comandos críticos** (backup, restore, init) falham se `RESTIC_PASSWORD` não estiver configurado
- **Comandos de setup** alertam sobre credenciais faltantes mas continuam
- **Comando first-run** verifica todas as credenciais antes de prosseguir

Se as credenciais não estiverem configuradas, você verá mensagens como:
```
ERRO: RESTIC_PASSWORD não configurado!
Execute: make setup-restic-password
```

#### Opção 2: Keyring do Sistema (Recomendado)

Armazena a senha no gerenciador de credenciais do sistema operacional:

```bash
# Configurar senha no keyring
python -c "import keyring; keyring.set_password('safestic', 'RESTIC_PASSWORD', 'MinhaSenh@Muito$egura123!')"

# Configurar no .env para usar keyring
CREDENTIAL_SOURCE=keyring
# RESTIC_PASSWORD não precisa estar no .env
```

#### Opção 3: Gerenciadores de Segredos em Nuvem

##### AWS Secrets Manager
```bash
# 1. Criar secret no AWS
aws secretsmanager create-secret \
    --name "safestic/RESTIC_PASSWORD" \
    --secret-string "MinhaSenh@Muito$egura123!" \
    --region us-east-1

# 2. Configurar no .env
CREDENTIAL_SOURCE=aws_secrets
AWS_REGION=us-east-1
# Credenciais AWS já configuradas
```

##### Azure Key Vault
```bash
# 1. Criar secret no Azure
az keyvault secret set \
    --vault-name "meu-keyvault" \
    --name "RESTIC-PASSWORD" \
    --value "MinhaSenh@Muito$egura123!"

# 2. Configurar no .env
CREDENTIAL_SOURCE=azure_keyvault
AZURE_KEYVAULT_URL=https://meu-keyvault.vault.azure.net/
# Autenticação Azure já configurada
```

##### Google Cloud Secret Manager
```bash
# 1. Criar secret no GCP
echo -n "MinhaSenh@Muito$egura123!" | \
    gcloud secrets create RESTIC_PASSWORD --data-file=-

# 2. Configurar no .env
CREDENTIAL_SOURCE=gcp_secrets
GCP_PROJECT_ID=meu-projeto-gcp
# Credenciais GCP já configuradas
```

#### Opção 4: SOPS (Arquivo Criptografado)

Para criptografar todo o arquivo `.env`:

```bash
# 1. Instalar SOPS
# https://github.com/mozilla/sops/releases

# 2. Configurar chave de criptografia (GPG, AWS KMS, etc.)
# Exemplo com GPG:
gpg --generate-key

# 3. Criptografar .env
sops -e .env > .env.enc

# 4. Configurar para usar SOPS
CREDENTIAL_SOURCE=sops
SOPS_FILE=.env.enc
```

#### 🔒 Configuração de Credenciais por Provedor

##### Para AWS S3:
```env
# Opção 1: Arquivo .env
STORAGE_PROVIDER=aws
STORAGE_BUCKET=meu-bucket-backup
RESTIC_PASSWORD=MinhaSenh@Muito$egura123!
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# Opção 2: Credenciais no AWS Secrets Manager
STORAGE_PROVIDER=aws
STORAGE_BUCKET=meu-bucket-backup
CREDENTIAL_SOURCE=aws_secrets
AWS_REGION=us-east-1
# RESTIC_PASSWORD, AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY no Secrets Manager
```

##### Para Azure Blob:
```env
# Opção 1: Arquivo .env
STORAGE_PROVIDER=azure
STORAGE_BUCKET=meu-container
RESTIC_PASSWORD=MinhaSenh@Muito$egura123!
AZURE_ACCOUNT_NAME=minhaconta
AZURE_ACCOUNT_KEY=...

# Opção 2: Credenciais no Azure Key Vault
STORAGE_PROVIDER=azure
STORAGE_BUCKET=meu-container
CREDENTIAL_SOURCE=azure_keyvault
AZURE_KEYVAULT_URL=https://meu-keyvault.vault.azure.net/
# RESTIC_PASSWORD, AZURE_ACCOUNT_NAME e AZURE_ACCOUNT_KEY no Key Vault
```

##### Para Google Cloud Storage:
```env
# Opção 1: Arquivo .env
STORAGE_PROVIDER=gcp
STORAGE_BUCKET=meu-bucket-gcp
RESTIC_PASSWORD=MinhaSenh@Muito$egura123!
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credenciais.json
GOOGLE_PROJECT_ID=meu-projeto

# Opção 2: Credenciais no GCP Secret Manager
STORAGE_PROVIDER=gcp
STORAGE_BUCKET=meu-bucket-gcp
CREDENTIAL_SOURCE=gcp_secrets
GCP_PROJECT_ID=meu-projeto
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credenciais.json
# RESTIC_PASSWORD no Secret Manager
```

## 🎯 Primeiros Passos

### 1. Validar Configuracao
```bash
# Verificar se tudo esta configurado corretamente
make validate

# Verificar setup completo
make validate-setup

# Verificar saude do sistema
make health
```

### 2. Inicializar Repositorio
```bash
# Criar novo repositorio de backup
make init
```

### 3. Primeiro Backup
```bash
# Executar backup completo
make backup

# OU testar primeiro (simulacao)
make dry-run
```

### 4. Verificar Backup
```bash
# Listar snapshots criados
make list

# Ver estatisticas
make stats

# Verificar integridade
make check
```

## 📅 Agendamento Automatico

### Instalar Agendamento

**Windows (Task Scheduler):**
```powershell
# Instalar tarefas agendadas
make schedule-install

# Verificar status
make schedule-status

# Remover agendamento
make schedule-remove
```

**Linux (systemd):**
```bash
# Instalar servicos systemd
make schedule-install

# Verificar status
make schedule-status

# Remover agendamento
make schedule-remove
```

### Configuracao Padrao do Agendamento

- **Backup**: Diario as 02:00 (com delay aleatorio de ate 1h)
- **Prune**: Semanal aos domingos as 03:00 (com delay aleatorio de ate 2h)
- **Verificacao**: Executada apos cada backup/prune

## 📖 Comandos Disponiveis

### Operacoes de Backup
```bash
make backup          # Backup completo
make dry-run         # Simular backup
make test-backup     # Backup de teste
```

### Listagem e Consulta
```bash
make list            # Listar snapshots
make list-size       # Listar com tamanhos
make list-files      # Arquivos do ultimo snapshot
make stats           # Estatisticas detalhadas
make repo-size       # Tamanho do repositorio
```

### Restauracao
```bash
make restore                    # Restaurar ultimo snapshot
make restore-id ID=abc123       # Restaurar snapshot especifico
make restore-file FILE=arquivo  # Restaurar arquivo especifico
make test-restore               # Teste de restauracao
```

### Manutencao
```bash
make prune           # Limpeza automatica
make manual-prune    # Limpeza manual
make forget          # Esquecer snapshots
make check           # Verificar integridade
make rebuild-index   # Reconstruir indice
make repair          # Reparar repositorio (cuidado!)
make clean           # Limpar arquivos temporarios
```

### Configuracao
```bash
make setup           # Instalar dependencias
make bootstrap       # Bootstrap completo (Windows)
make first-run       # Primeira configuracao
make init            # Inicializar repositorio
make validate        # Validar configuracao
make validate-setup  # Validar setup completo
make health          # Verificar saude
```

### Agendamento
```bash
make schedule-install  # Instalar agendamento
make schedule-remove   # Remover agendamento
make schedule-status   # Status do agendamento
```

### Avancado
```bash
make mount           # Montar repositorio como filesystem
make unmount         # Desmontar repositorio
```

## 🔧 Variaveis de Ambiente

### Configuracoes de Armazenamento

| Variavel | Descricao | Exemplo |
|----------|-----------|----------|
| `STORAGE_PROVIDER` | Provedor de armazenamento | `local`, `aws`, `azure`, `gcp` |
| `STORAGE_BUCKET` | Caminho/bucket de destino | `/backup` ou `meu-bucket` |
| `RESTIC_PASSWORD` | Senha do repositorio | `senha_super_segura` |

### Configuracoes de Backup

| Variavel | Descricao | Exemplo |
|----------|-----------|----------|
| `BACKUP_SOURCE_DIRS` | Diretorios para backup | `/home/user/docs,/home/user/pics` |
| `RESTIC_EXCLUDES` | Padroes de exclusao | `*.tmp,*.log,node_modules` |
| `RESTORE_TARGET_DIR` | Diretorio de restauracao | `/restore` |
| `RESTIC_TAGS` | Tags para snapshots | `auto,daily` |

### Configuracoes de Log

| Variavel | Descricao | Exemplo |
|----------|-----------|----------|
| `LOG_DIR` | Diretorio de logs | `./logs` |
| `LOG_LEVEL` | Nivel de log | `INFO`, `DEBUG`, `ERROR` |

### Configuracoes de Retencao

| Variavel | Descricao | Padrao |
|----------|-----------|--------|
| `RETENTION_ENABLED` | Habilitar retencao | `true` |
| `KEEP_HOURLY` | Manter por horas | `24` |
| `KEEP_DAILY` | Manter por dias | `7` |
| `KEEP_WEEKLY` | Manter por semanas | `4` |
| `KEEP_MONTHLY` | Manter por meses | `12` |

### Configuracoes de Nuvem

#### AWS
| Variavel | Descricao |
|----------|----------|
| `AWS_ACCESS_KEY_ID` | Chave de acesso AWS |
| `AWS_SECRET_ACCESS_KEY` | Chave secreta AWS |
| `AWS_DEFAULT_REGION` | Regiao AWS |

#### Azure
| Variavel | Descricao |
|----------|----------|
| `AZURE_ACCOUNT_NAME` | Nome da conta Azure |
| `AZURE_ACCOUNT_KEY` | Chave da conta Azure |

#### Google Cloud
| Variavel | Descricao |
|----------|----------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Caminho para credenciais JSON |
| `GOOGLE_PROJECT_ID` | ID do projeto GCP |

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. "Make nao encontrado" (Windows)
```powershell
# Instalar Git for Windows (inclui Make)
winget install Git.Git

# OU instalar MSYS2
winget install MSYS2.MSYS2

# Reiniciar terminal apos instalacao
```

#### 2. "Python nao encontrado"
```bash
# Linux
sudo apt install python3 python3-pip  # Ubuntu/Debian
sudo dnf install python3 python3-pip  # Fedora

# Windows
winget install Python.Python.3.12
```

#### 3. "Restic nao encontrado"
```bash
# Linux - instalacao manual
wget https://github.com/restic/restic/releases/download/v0.16.4/restic_0.16.4_linux_amd64.bz2
bunzip2 restic_0.16.4_linux_amd64.bz2
sudo mv restic_0.16.4_linux_amd64 /usr/local/bin/restic
sudo chmod +x /usr/local/bin/restic

# Windows
winget install restic.restic
```

#### 4. "Erro de permissao" (Linux)
```bash
# Adicionar usuario ao grupo necessario
sudo usermod -a -G backup $USER

# OU executar com sudo se necessario
sudo make backup
```

#### 5. "Repositorio nao encontrado"
```bash
# Verificar configuracao
make validate

# Inicializar repositorio
make init

# Verificar conectividade
make check
```

### Logs e Diagnostico

```bash
# Ver logs recentes
tail -f logs/safestic.log

# Verificar saude completa
make health

# Validar setup
make validate-setup

# Executar em modo debug
LOG_LEVEL=DEBUG make backup
```

### Recuperacao de Emergencia

```bash
# Verificar integridade do repositorio
make check

# Reconstruir indice se corrompido
make rebuild-index

# Reparar repositorio (ultimo recurso)
make repair
```

## 🛠️ Manutencao

### Manutencao Regular

```bash
# Verificacao semanal
make check

# Limpeza mensal
make prune
make clean

# Verificacao de saude
make health
```

### Monitoramento

```bash
# Status do agendamento
make schedule-status

# Estatisticas do repositorio
make stats

# Tamanho do repositorio
make repo-size
```

### Backup da Configuracao

```bash
# Fazer backup do arquivo .env
cp .env .env.backup

# Fazer backup dos scripts personalizados
tar -czf safestic-config-backup.tar.gz .env scripts/ logs/
```

### Atualizacao

```bash
# Atualizar codigo
git pull origin main

# Atualizar dependencias Python
pip install -r requirements.txt --upgrade

# Verificar se tudo ainda funciona
make validate
```

## 📞 Suporte

### Recursos uteis

- 📚 **Documentacao do Restic**: https://restic.readthedocs.io/
- 🐛 **Reportar Bugs**: [Issues do projeto]
- 💬 **Discussoes**: [Discussions do projeto]
- 📖 **Wiki**: [Wiki do projeto]

### Informacoes do Sistema

```bash
# Coletar informacoes para suporte
echo "=== INFORMAcoES DO SISTEMA ==="
uname -a  # Linux
systeminfo  # Windows

echo "=== VERSoES ==="
python --version
make --version
restic version

echo "=== CONFIGURAcaO ==="
make validate
make health
```

---

**🎉 Parabens!** Voce configurou com sucesso o Safestic. Seus dados agora estao protegidos com backups automaticos e seguros.

> 💡 **Dica**: Execute `make help` a qualquer momento para ver todos os comandos disponiveis.

> ⚠️ **Importante**: Mantenha sua senha do repositorio (`RESTIC_PASSWORD`) em local seguro. Sem ela, nao sera possivel recuperar seus backups!
