# Safestic

Safestic é uma ferramenta de backup automatizada que utiliza o Restic para criar backups seguros e eficientes de seus dados importantes.

## Características

- 🔒 **Seguro**: Criptografia AES-256 e autenticação
- 🌐 **Multi-cloud**: Suporte para AWS S3, Azure Blob, Google Cloud Storage e armazenamento local
- 📦 **Deduplicação**: Armazena apenas dados únicos, economizando espaço
- 🔄 **Incremental**: Backups rápidos após o primeiro backup completo
- 📋 **Logging**: Logs detalhados de todas as operações
- ⚙️ **Configurável**: Fácil configuração através de variáveis de ambiente
- 🐍 **Python**: Scripts Python para máxima compatibilidade
- 🛠️ **Makefile**: Interface simples através de comandos make
- 🚀 **Setup Automatizado**: Scripts de instalação para Windows e Linux
- 📅 **Agendamento**: Configuração automática de tarefas agendadas
- 🔧 **Manutenção**: Ferramentas avançadas de reparo e otimização
- 📊 **Monitoramento**: Verificação de saúde e relatórios detalhados

---

## 🚀 Funcionalidades

- Backup incremental, seguro e criptografado com Restic
- Suporte a múltiplos diretórios de origem
- Exclusões e tags configuráveis
- Retenção automática de snapshots (ou manual)
- Scripts multiplataforma (Windows/Linux) com `.env`
- Makefile para facilitar uso
- Compatível com `cron`, `Agendador de Tarefas`, pipelines e WSL
- Restauração de arquivos ou pastas específicas
- Listagem de conteúdo do snapshot antes da restauração
- **Novidades:**
  - Gerenciamento seguro de credenciais (keyring, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager, SOPS)
  - Logging estruturado em formato JSON com níveis e contexto
  - Validação robusta de entrada/saída com Pydantic
  - Suporte a operações assíncronas para melhor desempenho
  - Testes automatizados com pytest (unitários e integração)

---

## Instalação Rápida

### 🚀 Instalação Automática

**Windows (PowerShell como Administrador):**
```powershell
# Clone o repositório
git clone <repository-url>
cd safestic

# Execute o bootstrap (instala todas as dependências)
.\scripts\bootstrap_windows.ps1

# Configure o ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# Execute a configuração inicial
make first-run
```

**Linux/macOS:**
```bash
# Clone o repositório
git clone <repository-url>
cd safestic

# Execute o setup (instala dependências se necessário)
./scripts/setup_linux.sh

# Configure o ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações

# Execute a configuração inicial
make first-run
```

### 📖 Guia Completo

Para instruções detalhadas de instalação e configuração, consulte:
**[SETUP_SAFESTIC.md](SETUP_SAFESTIC.md)**

---

## 🪟 Como usar no Windows

### Opção recomendada: Git Bash

1. Instale o Git for Windows: https://gitforwindows.org/
2. Clique com botão direito na pasta do projeto > **Git Bash Here**
3. Execute:
   ```bash
   make backup
   ```

---

## ⚙️ Configuração do `.env`

Use o arquivo de exemplo:

```bash
cp .env.example .env
```

Edite as variáveis conforme seu provedor:

## Configuração

O arquivo `.env` contém todas as configurações necessárias. Principais variáveis:

### Configurações Básicas
- `STORAGE_PROVIDER`: Provedor de armazenamento (local, aws, azure, gcp)
- `STORAGE_BUCKET`: Caminho ou bucket de armazenamento
- `RESTIC_PASSWORD`: Senha para criptografia
- `BACKUP_SOURCE_DIRS`: Diretórios para backup (separados por vírgula)
- `LOG_DIR`: Diretório para logs
- `LOG_LEVEL`: Nível de log (DEBUG, INFO, WARNING, ERROR)

### Configurações de Retenção
- `RETENTION_ENABLED`: Habilitar política de retenção (true/false)
- `KEEP_HOURLY`: Manter backups por hora
- `KEEP_DAILY`: Manter backups diários
- `KEEP_WEEKLY`: Manter backups semanais
- `KEEP_MONTHLY`: Manter backups mensais

### Configurações de Nuvem
- **AWS**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`
- **Azure**: `AZURE_ACCOUNT_NAME`, `AZURE_ACCOUNT_KEY`
- **GCP**: `GOOGLE_APPLICATION_CREDENTIALS`, `GOOGLE_PROJECT_ID`

Veja `.env.example` para todas as opções disponíveis e `SETUP_SAFESTIC.md` para guia detalhado.

```dotenv
# Provedor: aws | azure | gcp | local
STORAGE_PROVIDER=aws
STORAGE_BUCKET=restic-backup-meuservidor

# Fonte de credenciais: env | keyring | aws_secrets | azure_keyvault | gcp_secrets | sops
CREDENTIAL_SOURCE=env

# Diretórios
BACKUP_SOURCE_DIRS=/etc,/home/user
RESTIC_EXCLUDES=*.log
RESTIC_TAGS=diario,servidor
RESTORE_TARGET_DIR=/tmp/restore
LOG_DIR=logs

# Retenção
RETENTION_ENABLED=true
KEEP_DAILY=7
KEEP_WEEKLY=4
KEEP_MONTHLY=6

# Configurações de log
LOG_LEVEL=INFO

# Autenticação AWS
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...

# Autenticação Azure
# AZURE_ACCOUNT_NAME=...
# AZURE_ACCOUNT_KEY=...

# Autenticação GCP
# GOOGLE_PROJECT_ID=...
# GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credenciais.json
```

## 🔑 Gerenciamento Seguro de Credenciais

O projeto suporta várias fontes para armazenamento seguro de credenciais:

### 1. Keyring do Sistema

Armazena credenciais no gerenciador de senhas do sistema operacional:

```bash
# Configurar senha no keyring
python -m examples.secure_credentials --source keyring --action setup --key RESTIC_PASSWORD --value "senha_segura"

# Usar credenciais do keyring
CREDENTIAL_SOURCE=keyring make backup
```

### 2. Serviços de Nuvem

Suporta os principais gerenciadores de segredos em nuvem:

- **AWS Secrets Manager**: Configure `AWS_REGION` e credenciais AWS
- **Azure Key Vault**: Configure `AZURE_KEYVAULT_URL` e autenticação Azure
- **GCP Secret Manager**: Configure `GOOGLE_PROJECT_ID` e autenticação GCP

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
# Verificar saúde do sistema
make health

# Fazer backup
make backup

# Listar snapshots
make list

# Restaurar último backup
make restore

# Verificar integridade
make check

# Limpar snapshots antigos
make prune

# Ver todos os comandos disponíveis
make help
```

### Comandos de Setup e Manutenção

```bash
# Configuração inicial completa
make first-run

# Instalar agendamento automático
make schedule-install

# Verificar status do agendamento
make schedule-status

# Remover agendamento
make schedule-remove

# Reparar repositório
make repair

# Reconstruir índice
make rebuild-index
```

### Comandos Detalhados via `make`

| Comando                            | Descrição                                          |
| ---------------------------------- | -------------------------------------------------- |
| `make backup`                      | Executa o backup e aplica retenção se ativada      |
| `make list`                        | Lista todos os snapshots no repositório            |
| `make list-files ID=xxx`           | Lista conteúdo de um snapshot específico           |
| `make restore`                     | Restaura o snapshot mais recente                   |
| `make restore-id ID=xxx`           | Restaura um snapshot específico                    |
| `make restore-file ID=xxx FILE=xx` | Restaura arquivo específico de um snapshot         |
| `make manual-prune`                | Aplica retenção manual via script Python           |
| `make check`                       | Verifica Restic, variáveis e acesso ao repositório |
| `make help`                        | Mostra a lista de comandos disponíveis             |

## 🔄 Operações Assíncronas

O projeto suporta operações assíncronas para melhor desempenho em tarefas de I/O intensivo:

```python
# Exemplo de uso do cliente assíncrono
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

> **Nota:** ao usar `make restore-file`, cada restauração é colocada em um subdiretório com timestamp dentro de `RESTORE_TARGET_DIR` para evitar sobreposições.

## Agendamento Automático

O Safestic pode configurar automaticamente backups regulares:

```bash
# Instalar agendamento (backup diário + limpeza semanal)
make schedule-install

# Verificar status
make schedule-status

# Remover agendamento
make schedule-remove
```

**Windows**: Usa Agendador de Tarefas  
**Linux**: Usa systemd timers

## Monitoramento e Manutenção

```bash
# Verificar saúde geral do sistema
make health

# Validar configuração
make validate

# Reparar problemas no repositório
make repair

# Otimizar repositório
make rebuild-index

# Montar repositório como sistema de arquivos
make mount

# Desmontar repositório
make unmount
```

## Solução de Problemas

Para problemas comuns e soluções, consulte:
- `make health` - Diagnóstico completo
- `make validate` - Verificar configuração
- `SETUP_SAFESTIC.md` - Guia de solução de problemas

---

## 🧪 Verificação rápida

Execute:

```bash
make check
```

Isso verifica:

- Se `restic` está no `PATH`
- Se as variáveis obrigatórias estão presentes
- Se o repositório é acessível (ou será inicializado)

---

## 🔒 Segurança

- Os backups são criptografados com AES-256 pelo próprio Restic
- Nunca suba `.env` em repositórios públicos (já ignorado no `.gitignore`)

---

## Estrutura do Projeto

```
safestic/
├── scripts/                    # Scripts Python e Shell
│   ├── backup.py              # Script de backup
│   ├── restore.py             # Script de restauração
│   ├── list.py                # Listagem de snapshots
│   ├── prune.py               # Limpeza de snapshots
│   ├── check.py               # Verificação de integridade
│   ├── validate_config.py     # Validação de configuração
│   ├── health_check.py        # Verificação de saúde
│   ├── forget_snapshots.py    # Esquecimento de snapshots
│   ├── mount_repo.py          # Montagem do repositório
│   ├── unmount_repo.py        # Desmontagem do repositório
│   ├── rebuild_index.py       # Reconstrução de índice
│   ├── repair_repo.py         # Reparo do repositório
│   ├── bootstrap_windows.ps1  # Bootstrap Windows
│   ├── setup_windows.sh       # Setup Windows (Git Bash)
│   ├── setup_linux.sh         # Setup Linux
│   ├── schedule_windows.ps1   # Agendamento Windows
│   ├── schedule_linux.sh      # Agendamento Linux
│   └── validate-setup.sh      # Validação do setup
├── logs/                      # Arquivos de log
├── .env.example              # Exemplo de configuração
├── .env                      # Suas configurações (criar)
├── Makefile                  # Comandos make
├── requirements.txt          # Dependências Python
├── pyproject.toml           # Configuração do projeto Python
├── README.md                # Este arquivo
└── SETUP_SAFESTIC.md        # Guia completo de instalação
```

---

## Suporte

- 📖 **Documentação**: [SETUP_SAFESTIC.md](SETUP_SAFESTIC.md)
- 🐛 **Issues**: Abra uma issue no GitHub
- 💬 **Discussões**: Use as discussões do GitHub
- 📚 **Restic**: [Documentação oficial do Restic](https://restic.readthedocs.io/)

## Status do Projeto

✅ **Funcionalidades Implementadas:**
- Setup automatizado para Windows e Linux
- Agendamento automático de backups
- Ferramentas avançadas de manutenção e reparo
- Sistema completo de monitoramento e saúde
- Suporte completo multi-cloud
- Interface unificada via Makefile
- Documentação abrangente

🚀 **Pronto para Produção!**

## Contribuição

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo LICENSE para detalhes.
