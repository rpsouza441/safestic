# 🛡️ Guia de Configuração do Safestic

**Safestic** é uma solução completa de backup automatizado baseada no Restic, com suporte multiplataforma para Windows e Linux.

## 📋 Índice

- [Pré-requisitos](#-pré-requisitos)
- [Instalação Rápida](#-instalação-rápida)
- [Instalação Manual](#-instalação-manual)
- [Configuração](#-configuração)
- [Primeiros Passos](#-primeiros-passos)
- [Agendamento Automático](#-agendamento-automático)
- [Comandos Disponíveis](#-comandos-disponíveis)
- [Variáveis de Ambiente](#-variáveis-de-ambiente)
- [Troubleshooting](#-troubleshooting)
- [Manutenção](#-manutenção)

## 🔧 Pré-requisitos

### Requisitos Mínimos
- **Python**: 3.10 ou superior
- **Git**: Para clonagem do repositório
- **Make**: Para execução dos comandos
- **Restic**: Ferramenta de backup (será instalado automaticamente)

### Sistemas Suportados
- ✅ **Windows 10/11** (PowerShell 5.1+)
- ✅ **Linux** (Ubuntu, Debian, Fedora, CentOS, Arch, openSUSE)
- ✅ **macOS** (via scripts Linux)

## 🚀 Instalação Rápida

### Windows (Recomendado)

1. **Clone o repositório:**
   ```powershell
   git clone <url-do-repositorio> safestic
   cd safestic
   ```

2. **Execute o bootstrap (instala tudo automaticamente):**
   ```powershell
   # Como Administrador (recomendado)
   powershell -ExecutionPolicy Bypass -File scripts\bootstrap_windows.ps1
   
   # OU usando Make (se já tiver instalado)
   make bootstrap
   ```

3. **Configure e execute primeira vez:**
   ```powershell
   make first-run
   ```

### Linux

1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio> safestic
   cd safestic
   ```

2. **Execute o setup:**
   ```bash
   # Instala dependências automaticamente
   make setup
   
   # OU manualmente
   bash scripts/setup_linux.sh --assume-yes
   ```

3. **Configure e execute primeira vez:**
   ```bash
   make first-run
   ```

## 🔨 Instalação Manual

### Windows - Passo a Passo

1. **Instalar dependências:**
   ```powershell
   # Instalar Git (se não tiver)
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

# Instalar dependências
sudo apt install -y git make python3 python3-pip python3-venv curl bzip2

# Instalar Restic
sudo apt install -y restic
# OU download manual se não estiver disponível
```

#### Fedora/CentOS/RHEL
```bash
# Instalar dependências
sudo dnf install -y git make python3 python3-pip curl bzip2

# Instalar Restic
sudo dnf install -y restic
```

#### Arch/Manjaro
```bash
# Instalar dependências
sudo pacman -S git make python python-pip curl bzip2 restic
```

## ⚙️ Configuração

### 1. Arquivo de Configuração (.env)

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env  # Linux
notepad .env  # Windows
```

### 2. Configurações Essenciais

**Configuração mínima necessária:**

```env
# Provedor de armazenamento
STORAGE_PROVIDER=local  # ou aws, azure, gcp

# Para armazenamento local
STORAGE_BUCKET=/caminho/para/backup  # Linux
STORAGE_BUCKET=C:\Backups\Safestic   # Windows

# Senha do repositório (IMPORTANTE: guarde com segurança!)
RESTIC_PASSWORD=sua_senha_super_segura_aqui

# Diretórios para backup (separados por vírgula)
BACKUP_SOURCE_DIRS=/home/usuario/Documentos,/home/usuario/Projetos
# Windows: BACKUP_SOURCE_DIRS=C:\Users\Usuario\Documents,C:\Users\Usuario\Desktop

# Diretório de logs
LOG_DIR=./logs
```

### 3. Configurações de Nuvem (Opcional)

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

## 🎯 Primeiros Passos

### 1. Validar Configuração
```bash
# Verificar se tudo está configurado corretamente
make validate

# Verificar setup completo
make validate-setup

# Verificar saúde do sistema
make health
```

### 2. Inicializar Repositório
```bash
# Criar novo repositório de backup
make init
```

### 3. Primeiro Backup
```bash
# Executar backup completo
make backup

# OU testar primeiro (simulação)
make dry-run
```

### 4. Verificar Backup
```bash
# Listar snapshots criados
make list

# Ver estatísticas
make stats

# Verificar integridade
make check
```

## 📅 Agendamento Automático

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
# Instalar serviços systemd
make schedule-install

# Verificar status
make schedule-status

# Remover agendamento
make schedule-remove
```

### Configuração Padrão do Agendamento

- **Backup**: Diário às 02:00 (com delay aleatório de até 1h)
- **Prune**: Semanal aos domingos às 03:00 (com delay aleatório de até 2h)
- **Verificação**: Executada após cada backup/prune

## 📖 Comandos Disponíveis

### Operações de Backup
```bash
make backup          # Backup completo
make dry-run         # Simular backup
make test-backup     # Backup de teste
```

### Listagem e Consulta
```bash
make list            # Listar snapshots
make list-size       # Listar com tamanhos
make list-files      # Arquivos do último snapshot
make stats           # Estatísticas detalhadas
make repo-size       # Tamanho do repositório
```

### Restauração
```bash
make restore                    # Restaurar último snapshot
make restore-id ID=abc123       # Restaurar snapshot específico
make restore-file FILE=arquivo  # Restaurar arquivo específico
make test-restore               # Teste de restauração
```

### Manutenção
```bash
make prune           # Limpeza automática
make manual-prune    # Limpeza manual
make forget          # Esquecer snapshots
make check           # Verificar integridade
make rebuild-index   # Reconstruir índice
make repair          # Reparar repositório (cuidado!)
make clean           # Limpar arquivos temporários
```

### Configuração
```bash
make setup           # Instalar dependências
make bootstrap       # Bootstrap completo (Windows)
make first-run       # Primeira configuração
make init            # Inicializar repositório
make validate        # Validar configuração
make validate-setup  # Validar setup completo
make health          # Verificar saúde
```

### Agendamento
```bash
make schedule-install  # Instalar agendamento
make schedule-remove   # Remover agendamento
make schedule-status   # Status do agendamento
```

### Avançado
```bash
make mount           # Montar repositório como filesystem
make unmount         # Desmontar repositório
```

## 🔧 Variáveis de Ambiente

### Configurações de Armazenamento

| Variável | Descrição | Exemplo |
|----------|-----------|----------|
| `STORAGE_PROVIDER` | Provedor de armazenamento | `local`, `aws`, `azure`, `gcp` |
| `STORAGE_BUCKET` | Caminho/bucket de destino | `/backup` ou `meu-bucket` |
| `RESTIC_PASSWORD` | Senha do repositório | `senha_super_segura` |

### Configurações de Backup

| Variável | Descrição | Exemplo |
|----------|-----------|----------|
| `BACKUP_SOURCE_DIRS` | Diretórios para backup | `/home/user/docs,/home/user/pics` |
| `RESTIC_EXCLUDES` | Padrões de exclusão | `*.tmp,*.log,node_modules` |
| `RESTORE_TARGET_DIR` | Diretório de restauração | `/restore` |
| `RESTIC_TAGS` | Tags para snapshots | `auto,daily` |

### Configurações de Log

| Variável | Descrição | Exemplo |
|----------|-----------|----------|
| `LOG_DIR` | Diretório de logs | `./logs` |
| `LOG_LEVEL` | Nível de log | `INFO`, `DEBUG`, `ERROR` |

### Configurações de Retenção

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `RETENTION_ENABLED` | Habilitar retenção | `true` |
| `KEEP_HOURLY` | Manter por horas | `24` |
| `KEEP_DAILY` | Manter por dias | `7` |
| `KEEP_WEEKLY` | Manter por semanas | `4` |
| `KEEP_MONTHLY` | Manter por meses | `12` |

### Configurações de Nuvem

#### AWS
| Variável | Descrição |
|----------|----------|
| `AWS_ACCESS_KEY_ID` | Chave de acesso AWS |
| `AWS_SECRET_ACCESS_KEY` | Chave secreta AWS |
| `AWS_DEFAULT_REGION` | Região AWS |

#### Azure
| Variável | Descrição |
|----------|----------|
| `AZURE_ACCOUNT_NAME` | Nome da conta Azure |
| `AZURE_ACCOUNT_KEY` | Chave da conta Azure |

#### Google Cloud
| Variável | Descrição |
|----------|----------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Caminho para credenciais JSON |
| `GOOGLE_PROJECT_ID` | ID do projeto GCP |

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. "Make não encontrado" (Windows)
```powershell
# Instalar Git for Windows (inclui Make)
winget install Git.Git

# OU instalar MSYS2
winget install MSYS2.MSYS2

# Reiniciar terminal após instalação
```

#### 2. "Python não encontrado"
```bash
# Linux
sudo apt install python3 python3-pip  # Ubuntu/Debian
sudo dnf install python3 python3-pip  # Fedora

# Windows
winget install Python.Python.3.12
```

#### 3. "Restic não encontrado"
```bash
# Linux - instalação manual
wget https://github.com/restic/restic/releases/download/v0.16.4/restic_0.16.4_linux_amd64.bz2
bunzip2 restic_0.16.4_linux_amd64.bz2
sudo mv restic_0.16.4_linux_amd64 /usr/local/bin/restic
sudo chmod +x /usr/local/bin/restic

# Windows
winget install restic.restic
```

#### 4. "Erro de permissão" (Linux)
```bash
# Adicionar usuário ao grupo necessário
sudo usermod -a -G backup $USER

# OU executar com sudo se necessário
sudo make backup
```

#### 5. "Repositório não encontrado"
```bash
# Verificar configuração
make validate

# Inicializar repositório
make init

# Verificar conectividade
make check
```

### Logs e Diagnóstico

```bash
# Ver logs recentes
tail -f logs/safestic.log

# Verificar saúde completa
make health

# Validar setup
make validate-setup

# Executar em modo debug
LOG_LEVEL=DEBUG make backup
```

### Recuperação de Emergência

```bash
# Verificar integridade do repositório
make check

# Reconstruir índice se corrompido
make rebuild-index

# Reparar repositório (último recurso)
make repair
```

## 🛠️ Manutenção

### Manutenção Regular

```bash
# Verificação semanal
make check

# Limpeza mensal
make prune
make clean

# Verificação de saúde
make health
```

### Monitoramento

```bash
# Status do agendamento
make schedule-status

# Estatísticas do repositório
make stats

# Tamanho do repositório
make repo-size
```

### Backup da Configuração

```bash
# Fazer backup do arquivo .env
cp .env .env.backup

# Fazer backup dos scripts personalizados
tar -czf safestic-config-backup.tar.gz .env scripts/ logs/
```

### Atualização

```bash
# Atualizar código
git pull origin main

# Atualizar dependências Python
pip install -r requirements.txt --upgrade

# Verificar se tudo ainda funciona
make validate
```

## 📞 Suporte

### Recursos Úteis

- 📚 **Documentação do Restic**: https://restic.readthedocs.io/
- 🐛 **Reportar Bugs**: [Issues do projeto]
- 💬 **Discussões**: [Discussions do projeto]
- 📖 **Wiki**: [Wiki do projeto]

### Informações do Sistema

```bash
# Coletar informações para suporte
echo "=== INFORMAÇÕES DO SISTEMA ==="
uname -a  # Linux
systeminfo  # Windows

echo "=== VERSÕES ==="
python --version
make --version
restic version

echo "=== CONFIGURAÇÃO ==="
make validate
make health
```

---

**🎉 Parabéns!** Você configurou com sucesso o Safestic. Seus dados agora estão protegidos com backups automáticos e seguros.

> 💡 **Dica**: Execute `make help` a qualquer momento para ver todos os comandos disponíveis.

> ⚠️ **Importante**: Mantenha sua senha do repositório (`RESTIC_PASSWORD`) em local seguro. Sem ela, não será possível recuperar seus backups!