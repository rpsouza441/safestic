# 🔐 Backup Automatizado com Restic (AWS, Azure, GCP)

Este projeto fornece uma solução de backup automática e criptografada com [Restic](https://restic.net/), suportando múltiplos provedores de nuvem: **AWS S3**, **Azure Blob Storage**, **Google Cloud Storage** e **armazenamento local**.

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

## 🧰 Pré-requisitos

- Python 3.10+
- Restic instalado: https://restic.net/
- Instalar dependências:
  ```bash
  pip install -r requirements.txt
  ```

### Desenvolvimento e Testes

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements.txt

# Executar testes
pytest

# Verificar cobertura de testes
pytest --cov=services

# Verificar tipagem
mypy services

# Verificar estilo de código
ruff check services
```

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

## 📦 Comandos via `make`

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

## 📁 Estrutura esperada do projeto

```
.
├── .env.example
├── .gitignore
├── Makefile
├── README.md
├── restic_backup.py
├── restore_snapshot.py
├── restore_file.py
├── list_snapshots.py
├── list_snapshot_files.py
├── check_restic_access.py
└── manual_prune.py
```

---

## 📄 Licença

MIT License.
