# 🔐 Backup Automatizado com Restic (AWS, Azure, GCP)

Este projeto fornece uma solução de backup automática e criptografada com [Restic](https://restic.net/), suportando múltiplos provedores de nuvem: **AWS S3**, **Azure Blob Storage** e **Google Cloud Storage**.

---

## 🚀 Funcionalidades

- Backup incremental, seguro e criptografado com Restic
- Suporte a múltiplos diretórios de origem
- Exclusões e tags configuráveis
- Retenção automática de snapshots (ou manual)
- Scripts multiplataforma (Windows/Linux) com `.env`
- Makefile para facilitar uso
- Compatível com `cron`, `Agendador de Tarefas`, pipelines e WSL

---

## 🧰 Pré-requisitos

- Python 3.7+
- Restic instalado: https://restic.net/
- Instalar dependências:
  ```bash
  pip install python-dotenv
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
# Provedor: aws | azure | gcp
STORAGE_PROVIDER=aws
STORAGE_BUCKET=restic-backup-meuservidor
RESTIC_PASSWORD=sua_senha_segura

# Diretórios
BACKUP_SOURCE_DIRS=/etc,/home/user
RESTIC_EXCLUDES=*.log
RESTIC_TAGS=diario,servidor

# Retenção
RETENTION_ENABLED=true
RETENTION_KEEP_DAILY=7
RETENTION_KEEP_WEEKLY=4
RETENTION_KEEP_MONTHLY=6

# Autenticação AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Autenticação Azure
AZURE_ACCOUNT_NAME=...
AZURE_ACCOUNT_KEY=...

# Autenticação GCP
GOOGLE_PROJECT_ID=...
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credenciais.json
```

---

## 📦 Comandos via `make`

| Comando                  | Descrição                                          |
| ------------------------ | -------------------------------------------------- |
| `make backup`            | Executa o backup e aplica retenção se ativada      |
| `make list`              | Lista todos os snapshots no repositório            |
| `make restore`           | Restaura o snapshot mais recente                   |
| `make restore-id ID=xxx` | Restaura um snapshot específico                    |
| `make manual-prune`      | Aplica retenção manual via script                  |
| `make check`             | Verifica Restic, variáveis e acesso ao repositório |
| `make help`              | Mostra a lista de comandos disponíveis             |

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
├── Makefile
├── README.md
├── .gitignore
├── restic_backup.py
├── restore_snapshot.py
├── list_snapshots.py
├── check_restic_access.py
└── manual_prune.py
```

---

## 📄 Licença

MIT License.
