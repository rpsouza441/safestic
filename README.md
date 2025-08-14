# Safestic

Safestic e uma ferramenta de backup automatizada que utiliza o Restic para criar backups seguros e eficientes de seus dados importantes.

## Caracteristicas

- 🔒 **Seguro**: Criptografia AES-256 e autenticacao
- 🌐 **Multi-cloud**: Suporte para AWS S3, Azure Blob, Google Cloud Storage e armazenamento local
- 📦 **Deduplicacao**: Armazena apenas dados unicos, economizando espaco
- 🔄 **Incremental**: Backups rapidos apos o primeiro backup completo
- 📋 **Logging**: Logs detalhados de todas as operacoes
- ⚙️ **Configuravel**: Facil configuracao atraves de variaveis de ambiente
- 🐍 **Python**: Scripts Python para maxima compatibilidade
- 🛠️ **Makefile**: Interface simples atraves de comandos make
- 🚀 **Setup Automatizado**: Scripts de instalacao para Windows e Linux
- 📅 **Agendamento**: Configuracao automatica de tarefas agendadas
- 🔧 **Manutencao**: Ferramentas avancadas de reparo e otimizacao
- 📊 **Monitoramento**: Verificacao de saude e relatorios detalhados

---

## 🚀 Funcionalidades

- Backup incremental, seguro e criptografado com Restic
- Suporte a multiplos diretorios de origem
- Exclusoes e tags configuraveis
- Retencao automatica de snapshots (ou manual)
- Scripts multiplataforma (Windows/Linux) com `.env`
- Makefile para facilitar uso
- Compativel com `cron`, `Agendador de Tarefas`, pipelines e WSL
- Restauracao de arquivos ou pastas especificas
- Listagem de conteudo do snapshot antes da restauracao
- **Novidades:**
  - Gerenciamento seguro de credenciais (keyring, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager, SOPS)
  - Logging estruturado em formato JSON com niveis e contexto
  - Validacao robusta de entrada/saida com Pydantic
  - Suporte a operacoes assincronas para melhor desempenho
  - Testes automatizados com pytest (unitarios e integracao)

---

## Instalacao Rapida

### 🚀 Instalacao Automatica

**Windows (PowerShell como Administrador):**
```powershell
# Clone o repositorio
git clone <repository-url>
cd safestic

# Execute o bootstrap (instala todas as dependencias)
.\scripts\bootstrap_windows.ps1

# Configure o ambiente
cp .env.example .env
# Edite o arquivo .env com suas configuracoes

# Execute a configuracao inicial
make first-run
```

**Linux/macOS:**
```bash
# Clone o repositorio
git clone <repository-url>
cd safestic

# Execute o setup (instala dependencias se necessario)
./scripts/setup_linux.sh

# Configure o ambiente
cp .env.example .env
# Edite o arquivo .env com suas configuracoes

# Execute a configuracao inicial
make first-run
```

### 📖 Guia Completo

Para instrucoes detalhadas de instalacao e configuracao, consulte:
**[SETUP_SAFESTIC.md](SETUP_SAFESTIC.md)**

---

## 🪟 Como usar no Windows

### Opcao recomendada: Git Bash

1. Instale o Git for Windows: https://gitforwindows.org/
2. Clique com botao direito na pasta do projeto > **Git Bash Here**
3. Execute:
   ```bash
   make backup
   ```

---

## ⚙️ Configuracao do `.env`

Use o arquivo de exemplo:

```bash
cp .env.example .env
```

Edite as variaveis conforme seu provedor:

## Configuracao

O arquivo `.env` contem todas as configuracoes necessarias. Principais variaveis:

### Configuracoes Basicas
- `STORAGE_PROVIDER`: Provedor de armazenamento (local, aws, azure, gcp)
- `STORAGE_BUCKET`: Caminho ou bucket de armazenamento
- `RESTIC_PASSWORD`: Senha para criptografia
- `BACKUP_SOURCE_DIRS`: Diretorios para backup (separados por virgula)
- `LOG_DIR`: Diretorio para logs
- `LOG_LEVEL`: Nivel de log (DEBUG, INFO, WARNING, ERROR)

### Configuracoes de Retencao
- `RETENTION_ENABLED`: Habilitar politica de retencao (true/false)
- `KEEP_HOURLY`: Manter backups por hora
- `KEEP_DAILY`: Manter backups diarios
- `KEEP_WEEKLY`: Manter backups semanais
- `KEEP_MONTHLY`: Manter backups mensais

### Configuracoes de Nuvem
- **AWS**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
- **Azure**: `AZURE_ACCOUNT_NAME`, `AZURE_ACCOUNT_KEY`
- **GCP**: `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_PROJECT_ID`

Veja `.env.example` para todas as opcoes disponiveis e `SETUP_SAFESTIC.md` para guia detalhado.

```dotenv
# Provedor: aws | azure | gcp | local
STORAGE_PROVIDER=aws
STORAGE_BUCKET=restic-backup-meuservidor

# Fonte de credenciais: env | keyring | aws_secrets | azure_keyvault | gcp_secrets | sops
CREDENTIAL_SOURCE=env

# Diretorios
BACKUP_SOURCE_DIRS=/etc,/home/user
RESTIC_EXCLUDES=*.log
RESTIC_TAGS=diario,servidor
RESTORE_TARGET_DIR=/tmp/restore
LOG_DIR=logs

# Retencao
RETENTION_ENABLED=true
KEEP_DAILY=7
KEEP_WEEKLY=4
KEEP_MONTHLY=6

# Configuracoes de log
LOG_LEVEL=INFO

# Autenticacao AWS
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...

# Autenticacao Azure
# AZURE_ACCOUNT_NAME=...
# AZURE_ACCOUNT_KEY=...

# Autenticacao GCP
# GOOGLE_PROJECT_ID=...
# GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credenciais.json
```

## 🔑 Gerenciamento Seguro de Credenciais

O projeto suporta varias fontes para armazenamento seguro de credenciais:

### 1. Keyring do Sistema

Armazena credenciais no gerenciador de senhas do sistema operacional:

```bash
# Configurar senha no keyring
python -m examples.secure_credentials --source keyring --action setup --key RESTIC_PASSWORD --value "senha_segura"

# Usar credenciais do keyring
CREDENTIAL_SOURCE=keyring make backup
```

### 2. Servicos de Nuvem

Suporta os principais gerenciadores de segredos em nuvem:

- **AWS Secrets Manager**: Configure `AWS_REGION` e credenciais AWS
- **Azure Key Vault**: Configure `AZURE_KEYVAULT_URL` e autenticacao Azure
- **GCP Secret Manager**: Configure `GOOGLE_PROJECT_ID` e autenticacao GCP

### 3. SOPS (Secrets OPerationS)

Para criptografar o arquivo `.env` com SOPS:

```bash
# Instalar SOPS
# https://github.com/mozilla/sops/releases

# Criptografar .env
sops -e .env > .env.enc

# Usar arquivo criptografado
CREDENTIAL_SOURCE=sops SOPS_FILE=.env.enc make backup
```

---

## Uso

### Comandos Principais

```bash
# Verificar saude do sistema
make health

# Fazer backup
make backup

# Listar snapshots
make list

# Restaurar ultimo backup
make restore

# Verificar integridade
make check

# Limpar snapshots antigos
make prune

# Ver todos os comandos disponiveis
make help
```

### Comandos de Setup e Manutencao

```bash
# Configuracao inicial completa
make first-run

# Instalar agendamento automatico
make schedule-install

# Verificar status do agendamento
make schedule-status

# Remover agendamento
make schedule-remove

# Reparar repositorio
make repair

# Reconstruir indice
make rebuild-index
```

### Comandos Detalhados via `make`

| Comando                            | Descricao                                          |
| ---------------------------------- | -------------------------------------------------- |
| `make backup`                      | Executa o backup e aplica retencao se ativada      |
| `make list`                        | Lista todos os snapshots no repositorio            |
| `make list-files ID=xxx`           | Lista conteudo de um snapshot especifico           |
| `make restore`                     | Restaura o snapshot mais recente                   |
| `make restore-id ID=xxx`           | Restaura um snapshot especifico                    |
| `make restore-file ID=xxx FILE=xx` | Restaura arquivo especifico de um snapshot         |
| `make manual-prune`                | Aplica retencao manual via script Python           |
| `make check`                       | Verifica Restic, variaveis e acesso ao repositorio |
| `make help`                        | Mostra a lista de comandos disponiveis             |

## 🔄 Operacoes Assincronas

O projeto suporta operacoes assincronas para melhor desempenho em tarefas de I/O intensivo:

```python
# Exemplo de uso do cliente assincrono
from services.restic_client_async import ResticClientAsync

async def main():
    client = ResticClientAsync(repository="...", password="...")
    
    # Executar backups em paralelo
    tasks = [
        client.backup(paths=["/path1"]),
        client.backup(paths=["/path2"]),
        client.backup(paths=["/path3"])
    ]
    results = await asyncio.gather(*tasks)
```

Veja um exemplo completo em `examples/async_backup.py`.

> **Nota:** ao usar `make restore-file`, cada restauracao e colocada em um subdiretorio com timestamp dentro de `RESTORE_TARGET_DIR` para evitar sobreposicoes.

## Agendamento Automatico

O Safestic pode configurar automaticamente backups regulares:

```bash
# Instalar agendamento (backup diario + limpeza semanal)
make schedule-install

# Verificar status
make schedule-status

# Remover agendamento
make schedule-remove
```

**Windows**: Usa Agendador de Tarefas  
**Linux**: Usa systemd timers

## Monitoramento e Manutencao

```bash
# Verificar saude geral do sistema
make health

# Validar configuracao
make validate

# Reparar problemas no repositorio
make repair

# Otimizar repositorio
make rebuild-index

# Montar repositorio como sistema de arquivos
make mount

# Desmontar repositorio
make unmount
```

## Solucao de Problemas

Para problemas comuns e solucoes, consulte:
- `make health` - Diagnostico completo
- `make validate` - Verificar configuracao
- `SETUP_SAFESTIC.md` - Guia de solucao de problemas

---

## 🧪 Verificacao rapida

Execute:

```bash
make check
```

Isso verifica:

- Se `restic` esta no `PATH`
- Se as variaveis obrigatorias estao presentes
- Se o repositorio e acessivel (ou sera inicializado)

---

## 🔒 Seguranca

- Os backups sao criptografados com AES-256 pelo proprio Restic
- Nunca suba `.env` em repositorios publicos (ja ignorado no `.gitignore`)

---

## Estrutura do Projeto

```
safestic/
├── scripts/                    # Scripts Python e Shell
│   ├── backup.py              # Script de backup
│   ├── restore.py             # Script de restauracao
│   ├── list.py                # Listagem de snapshots
│   ├── prune.py               # Limpeza de snapshots
│   ├── check.py               # Verificacao de integridade
│   ├── validate_config.py     # Validacao de configuracao
│   ├── health_check.py        # Verificacao de saude
│   ├── forget_snapshots.py    # Esquecimento de snapshots
│   ├── mount_repo.py          # Montagem do repositorio
│   ├── unmount_repo.py        # Desmontagem do repositorio
│   ├── rebuild_index.py       # Reconstrucao de indice
│   ├── repair_repo.py         # Reparo do repositorio
│   ├── bootstrap_windows.ps1  # Bootstrap Windows
│   ├── setup_windows.sh       # Setup Windows (Git Bash)
│   ├── setup_linux.sh         # Setup Linux
│   ├── schedule_windows.ps1   # Agendamento Windows
│   ├── schedule_linux.sh      # Agendamento Linux
│   └── validate-setup.sh      # Validacao do setup
├── logs/                      # Arquivos de log
├── .env.example              # Exemplo de configuracao
├── .env                      # Suas configuracoes (criar)
├── Makefile                  # Comandos make
├── requirements.txt          # Dependencias Python
├── pyproject.toml           # Configuracao do projeto Python
├── README.md                # Este arquivo
└── SETUP_SAFESTIC.md        # Guia completo de instalacao
```

---

## Suporte

- 📖 **Documentacao**: [SETUP_SAFESTIC.md](SETUP_SAFESTIC.md)
- 🐛 **Issues**: Abra uma issue no GitHub
- 💬 **Discussoes**: Use as discussoes do GitHub
- 📚 **Restic**: [Documentacao oficial do Restic](https://restic.readthedocs.io/)

## Status do Projeto

✅ **Funcionalidades Implementadas:**
- Setup automatizado para Windows e Linux
- Agendamento automatico de backups
- Ferramentas avancadas de manutencao e reparo
- Sistema completo de monitoramento e saude
- Suporte completo multi-cloud
- Interface unificada via Makefile
- Documentacao abrangente

🚀 **Pronto para Producao!**

## Contribuicao

Contribuicoes sao bem-vindas! Por favor:

1. Faca um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudancas
4. Push para a branch
5. Abra um Pull Request

## Licenca

Este projeto esta licenciado sob a MIT License - veja o arquivo LICENSE para detalhes.

