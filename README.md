# 🔐 Backup Automatizado com Restic para AWS S3

Este projeto fornece scripts em Python, um `.env` configurável e um `Makefile` para realizar **backups automatizados com Restic** em buckets S3 da AWS. Ele é multiplataforma (Linux/Windows), com suporte a versionamento, retenção e restauração.

---

## 🚀 Funcionalidades

- Backup incremental e criptografado com Restic
- Suporte a múltiplos diretórios de origem
- Exclusões configuráveis
- Tags para organização dos snapshots
- Política de retenção configurável (diária, semanal, mensal)
- Possibilidade de desativar retenção automática
- Logs por execução
- Verificação de ambiente (`make check`)
- Compatível com AWS S3 via credenciais no `.env`

---

## 📦 Pré-requisitos

- Python 3.7+
- Restic instalado no sistema: https://restic.net/
- Biblioteca Python:
  ```bash
  pip install python-dotenv
  ```

---

## ⚙️ Configuração do `.env`

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Preencha com suas informações:

```dotenv
RESTIC_REPOSITORY=s3:s3.amazonaws.com/seu-nome-do-bucket
RESTIC_PASSWORD=sua_senha_segura

BACKUP_SOURCE_DIRS=C:/Users/Administrator/Documents,D:/Projetos
RESTIC_EXCLUDES=*.log,*.tmp,node_modules
RESTIC_TAGS=diario,servidorX

RETENTION_ENABLED=true
RETENTION_KEEP_DAILY=7
RETENTION_KEEP_WEEKLY=4
RETENTION_KEEP_MONTHLY=6

AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

LOG_DIR=logs
```

---

## 🛠️ Comandos via Makefile

| Comando                 | Descrição                                                   |
| ----------------------- | ----------------------------------------------------------- |
| `make` ou `make help`   | Mostra ajuda                                                |
| `make check`            | Verifica se tudo está pronto (PATH, .env, acesso ao bucket) |
| `make backup`           | Executa backup e aplica retenção (se ativada)               |
| `make list`             | Lista snapshots existentes                                  |
| `make restore`          | Restaura o último snapshot                                  |
| `make restore-id ID=xx` | Restaura snapshot específico                                |
| `make manual-prune`     | Executa retenção manual, útil se `RETENTION_ENABLED=false`  |

---

## 🧪 Verificação rápida

Antes do primeiro backup, execute:

```bash
make check
```

Esse comando validará:

- Presença do Restic no PATH
- Variáveis obrigatórias no `.env`
- Acesso ao bucket S3
- Inicialização do repositório, se necessário

---

## 🔒 Segurança

- Nunca envie o `.env` para um repositório público
- Use variáveis de ambiente ou soluções como AWS Secrets Manager em produção
- Os backups são criptografados pelo próprio Restic com AES-256

---

## 📄 Licença

MIT License.
