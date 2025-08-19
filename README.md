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
# Edite o arquivo .env com suas configuracoes basicas

# Configure as credenciais (OBRIGATORIO)
make setup-credentials
# OU edite manualmente o .env com RESTIC_PASSWORD

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
# Edite o arquivo .env com suas configuracoes basicas

# Configure as credenciais (OBRIGATORIO)
make setup-credentials
# OU edite manualmente o .env com RESTIC_PASSWORD

# Execute a configuracao inicial
make first-run
```

> **📝 Nota para Debian/Ubuntu 24+:** O script automaticamente detecta ambientes Python gerenciados externamente e cria um ambiente virtual (`.venv`) quando necessário. Para ativar manualmente o ambiente virtual:
> ```bash
> source ./activate_venv.sh
> # OU
> source .venv/bin/activate
> ```

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

O arquivo `.env` contem todas as configuracoes necessarias para o SafeStic:

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Configure as credenciais (recomendado)
make setup-credentials

# OU edite manualmente o .env
notepad .env  # Windows
nano .env     # Linux
```

### Configuracoes Essenciais

| Variavel | Descricao | Exemplo |
|----------|-----------|----------|
| `STORAGE_PROVIDER` | Provedor de armazenamento | `local`, `aws`, `azure`, `gcp` |
| `STORAGE_BUCKET` | Destino do backup | `/backup` ou `meu-bucket` |
| `RESTIC_PASSWORD` | **Senha obrigatória** para criptografia | `MinhaSenh@Muito$egura123!` |
| `CREDENTIAL_SOURCE` | Fonte das credenciais | `env`, `keyring`, `aws_secrets` |
| `BACKUP_SOURCE_DIRS` | Diretorios para backup | `/home/user,/etc` |
| `RESTORE_TARGET_DIR` | Diretorio de restauracao | `./restore` |

⚠️ **IMPORTANTE**: 
- O `RESTIC_PASSWORD` é **obrigatório** - sem ele, seus backups são irrecuperáveis!
- Use `make setup-credentials` para configuração segura e interativa
- Consulte o arquivo `.env.example` para todas as opções disponíveis
- Veja `SETUP_SAFESTIC.md` para guia detalhado de configuração

---

## 🔑 Gerenciamento Seguro de Credenciais

O `RESTIC_PASSWORD` é **obrigatório** para criptografar seus backups. O Safestic oferece múltiplas formas seguras de gerenciar credenciais:

### 🔐 Configuracao de Credenciais

O Safestic oferece multiplas opcoes para configurar credenciais de forma segura. O sistema utiliza a variavel `CREDENTIAL_SOURCE` no arquivo `.env` para determinar onde buscar as credenciais.

#### Como Funciona o Sistema de Credenciais

1. **Fonte Primaria**: O sistema busca credenciais na fonte definida por `CREDENTIAL_SOURCE`
2. **Fallback**: Se nao encontrar na fonte primaria, busca no arquivo `.env` como fallback
3. **Prioridade**: keyring > aws_secrets > azure_keyvault > gcp_secrets > sops > env

#### Configuracao Interativa (Recomendado)

```bash
# Configuracao completa interativa
make setup-credentials

# Apenas RESTIC_PASSWORD
make setup-restic-password
```

#### Configuracao por Fonte Especifica

```bash
# Forcar uso do keyring do sistema
make setup-credentials-keyring

# Forcar uso do arquivo .env
make setup-credentials-env
```

#### Verificacao Automatica de Credenciais

O Safestic verifica automaticamente se as credenciais estao configuradas antes de executar operacoes que requerem acesso ao repositorio:

- **Comandos que requerem RESTIC_PASSWORD**: `backup`, `list`, `restore`, `init`, `prune`
- **Comandos que verificam todas as credenciais**: `first-run`
- **Comandos que alertam sobre credenciais**: `setup`, `bootstrap`, `check`

Se as credenciais nao estiverem configuradas, o sistema exibira uma mensagem de erro clara com instrucoes de como configurar.

#### 🏷️ Multiplos Projetos com APP_NAME

**IMPORTANTE**: Se você tem múltiplas instalações do Safestic, use a variável `APP_NAME` para evitar conflitos de credenciais no keyring:

```bash
# No arquivo .env do primeiro projeto
APP_NAME=safestic-projeto-aws
CREDENTIAL_SOURCE=keyring

# No arquivo .env do segundo projeto
APP_NAME=safestic-backup-pessoal
CREDENTIAL_SOURCE=keyring
```

**Como funciona**:
- Cada projeto usa um identificador único no keyring do sistema
- Evita sobrescrever credenciais entre projetos diferentes
- Permite usar senhas diferentes para cada repositório
- Funciona apenas com `CREDENTIAL_SOURCE=keyring`

**Exemplo prático**:
```bash
# Projeto 1: C:\safestic
echo "APP_NAME=safestic-principal" >> .env
make setup-credentials-keyring

# Projeto 2: C:\safestic-aws
echo "APP_NAME=safestic-aws" >> .env
make setup-credentials-keyring
```

### 1. Arquivo .env (Padrão)
```bash
# No arquivo .env
RESTIC_PASSWORD=MinhaSenh@Muito$egura123!
```
⚠️ **Importante**: Nunca commite o arquivo `.env` em repositórios Git!

### 2. Keyring do Sistema (Recomendado)

Armazena credenciais no gerenciador de senhas do sistema operacional:

```bash
# Configurar senha no keyring
python -c "import keyring; keyring.set_password('safestic', 'RESTIC_PASSWORD', 'senha_segura')"

# Configurar no .env
CREDENTIAL_SOURCE=keyring
# RESTIC_PASSWORD não precisa estar no .env quando usando keyring

# Usar credenciais do keyring
make backup
```

**⚠️ Importante sobre Keyring**: 
- Quando `CREDENTIAL_SOURCE=keyring`, o sistema busca `RESTIC_PASSWORD` no keyring do sistema
- Se nao encontrar no keyring, faz fallback para o arquivo `.env`
- Credenciais de nuvem (AWS, Azure, GCP) ainda podem estar no `.env` mesmo usando keyring para `RESTIC_PASSWORD`

### 3. Gerenciadores de Segredos em Nuvem

#### AWS Secrets Manager
```bash
# Criar secret
aws secretsmanager create-secret --name "safestic/RESTIC_PASSWORD" --secret-string "senha_segura"

# Configurar no .env
CREDENTIAL_SOURCE=aws_secrets
AWS_REGION=us-east-1
```

#### Azure Key Vault
```bash
# Criar secret
az keyvault secret set --vault-name "meu-keyvault" --name "RESTIC-PASSWORD" --value "senha_segura"

# Configurar no .env
CREDENTIAL_SOURCE=azure_keyvault
AZURE_KEYVAULT_URL=https://meu-keyvault.vault.azure.net/
```

#### Google Cloud Secret Manager
```bash
# Criar secret
echo -n "senha_segura" | gcloud secrets create RESTIC_PASSWORD --data-file=-

# Configurar no .env
CREDENTIAL_SOURCE=gcp_secrets
GCP_PROJECT_ID=meu-projeto-gcp
```

### 4. SOPS (Arquivo Criptografado)

Para criptografar todo o arquivo `.env`:

```bash
# Instalar SOPS: https://github.com/mozilla/sops/releases

# Criptografar .env
sops -e .env > .env.enc

# Configurar para usar SOPS
CREDENTIAL_SOURCE=sops
SOPS_FILE=.env.enc

# Usar arquivo criptografado
make backup
```

### 🔒 Configuração por Provedor de Nuvem

#### AWS S3 + Secrets Manager
```env
STORAGE_PROVIDER=aws
STORAGE_BUCKET=meu-bucket-backup
CREDENTIAL_SOURCE=aws_secrets
AWS_REGION=us-east-1
# Todas as credenciais (RESTIC_PASSWORD, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) no Secrets Manager
```

#### Azure Blob + Key Vault
```env
STORAGE_PROVIDER=azure
STORAGE_BUCKET=meu-container
CREDENTIAL_SOURCE=azure_keyvault
AZURE_KEYVAULT_URL=https://meu-keyvault.vault.azure.net/
# Todas as credenciais (RESTIC_PASSWORD, AZURE_ACCOUNT_NAME, AZURE_ACCOUNT_KEY) no Key Vault
```

#### GCP Storage + Secret Manager
```env
STORAGE_PROVIDER=gcp
STORAGE_BUCKET=meu-bucket-gcp
CREDENTIAL_SOURCE=gcp_secrets
GCP_PROJECT_ID=meu-projeto
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credenciais.json
# RESTIC_PASSWORD no Secret Manager
```

### 📁 Configuração de Diretorios

```env
# Diretorios de origem para backup (obrigatorio)
BACKUP_SOURCE_DIRS=/etc,/home/user,/var/log

# Diretorio de destino para restauracao (obrigatorio)
RESTORE_TARGET_DIR=./meu_restore

# Nota: BACKUP_TARGET_DIR nao existe - o destino do backup e definido por:
# - STORAGE_PROVIDER (local, aws, azure, gcp)
# - STORAGE_BUCKET (nome do bucket/container/diretorio)
# - RESTIC_REPOSITORY (gerado automaticamente baseado nos anteriores)
```

### 🎯 Como Configurar Destinos de Backup

O `STORAGE_BUCKET` define **onde** os backups serão salvos, dependendo do provedor:

#### 📁 **LOCAL** - Armazenamento no Computador
```env
STORAGE_PROVIDER=local
STORAGE_BUCKET=/home/usuario/meus-backups     # Linux
STORAGE_BUCKET=C:\Backups\SafeStic          # Windows
```
**O que acontece**: O diretório será criado automaticamente se não existir.

#### ☁️ **AWS S3** - Amazon Web Services
```env
STORAGE_PROVIDER=aws
STORAGE_BUCKET=meu-bucket-backup-empresa

# Credenciais (se CREDENTIAL_SOURCE=env)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1
```
**O que acontece**: Gera automaticamente `s3:s3.amazonaws.com/meu-bucket-backup-empresa`  
**⚠️ Importante**: O bucket S3 deve existir previamente.

#### 🔵 **AZURE** - Microsoft Azure Blob Storage
```env
STORAGE_PROVIDER=azure
STORAGE_BUCKET=backups-container

# Credenciais (se CREDENTIAL_SOURCE=env)
AZURE_ACCOUNT_NAME=minhacontastorage
AZURE_ACCOUNT_KEY=chave_da_conta...
```
**O que acontece**: Gera automaticamente `azure:minhacontastorage:backups-container:restic`  
**⚠️ Importante**: O container deve existir na conta de storage.

#### 🟡 **GCP** - Google Cloud Storage
```env
STORAGE_PROVIDER=gcp
STORAGE_BUCKET=meu-bucket-gcp-backups

# Credenciais (se CREDENTIAL_SOURCE=env)
GOOGLE_PROJECT_ID=meu-projeto-123
GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/credenciais.json
```
**O que acontece**: Gera automaticamente `gs:meu-bucket-gcp-backups`  
**⚠️ Importante**: O bucket deve existir no projeto GCP.

#### 🔧 **Como o Sistema Funciona**
1. **Você configura**: `STORAGE_PROVIDER` + `STORAGE_BUCKET`
2. **O sistema gera**: `RESTIC_REPOSITORY` automaticamente
3. **O Restic usa**: A URL gerada para salvar os backups

**💡 Resumo**: Não existe `BACKUP_TARGET_DIR` porque o destino é sempre determinado pela combinação `STORAGE_PROVIDER` + `STORAGE_BUCKET` + lógica interna do Restic!

---

## Uso

### ⚠️ Antes de Começar

**IMPORTANTE**: Certifique-se de que as credenciais estão configuradas antes de usar os comandos de backup:

```bash
# Verificar se as credenciais estão configuradas
make check

# Se não estiverem, configure-as:
make setup-credentials

# Ou verifique apenas o RESTIC_PASSWORD:
python scripts/check_credentials.py --restic-only
```

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

## 🔐 Segurança e Melhores Práticas

### Proteção do RESTIC_PASSWORD

⚠️ **CRÍTICO**: O `RESTIC_PASSWORD` é a chave mestra dos seus backups!

- **NUNCA perca esta senha** - sem ela, seus backups são irrecuperáveis
- **NUNCA commite** o arquivo `.env` em repositórios Git
- **Use senhas fortes** com pelo menos 20 caracteres, incluindo símbolos
- **Faça backup da senha** em local seguro (gerenciador de senhas)
- **Prefira gerenciadores seguros** (keyring, cloud secrets) ao arquivo `.env`

### Recomendações por Ambiente

**Desenvolvimento/Teste:**
```bash
# Use keyring para facilidade
CREDENTIAL_SOURCE=keyring
```

**Produção:**
```bash
# Use gerenciadores de segredos em nuvem
CREDENTIAL_SOURCE=aws_secrets  # ou azure_keyvault, gcp_secrets
```

**Ambientes Críticos:**
```bash
# Use SOPS com criptografia por chave
CREDENTIAL_SOURCE=sops
SOPS_FILE=.env.enc
```

### Exemplo de Senha Forte
```bash
# ✅ Boa: longa, complexa, única
RESTIC_PASSWORD="Meu$afestic2024!Backup#Seguro@Casa789"

# ❌ Ruim: curta, simples, comum
RESTIC_PASSWORD="123456"
```

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
├── services/                   # Módulos Python principais
│   ├── __init__.py            # Inicialização do pacote
│   ├── credentials.py         # Gerenciamento de credenciais
│   ├── logger.py              # Sistema de logging estruturado
│   ├── restic.py              # Configurações do Restic
│   ├── restic_client.py       # Cliente Restic síncrono
│   ├── restic_client_async.py # Cliente Restic assíncrono
│   └── script.py              # Utilitários para scripts
├── scripts/                   # Scripts de automação
│   ├── backup_task.ps1        # Tarefa de backup (Windows)
│   ├── backup_task.sh         # Tarefa de backup (Linux)
│   ├── bootstrap_windows.ps1  # Bootstrap Windows
│   ├── check_credentials.py   # Verificação de credenciais
│   ├── forget_snapshots.py    # Esquecimento de snapshots
│   ├── health_check.py        # Verificação de saúde
│   ├── mount_repo.py          # Montagem do repositório
│   ├── rebuild_index.py       # Reconstrução de índice
│   ├── repair_repo.py         # Reparo do repositório
│   ├── schedule.ps1           # Agendamento Windows
│   ├── schedule.sh            # Agendamento Linux
│   ├── setup_credentials.py   # Configuração de credenciais
│   ├── setup_linux.sh         # Setup Linux
│   ├── setup_windows.sh       # Setup Windows
│   ├── unmount_repo.py        # Desmontagem do repositório
│   ├── validate_config.py     # Validação de configuração
│   └── validate_setup.py      # Validação do setup
├── examples/                  # Exemplos de uso
│   ├── async_backup.py        # Exemplo de backup assíncrono
│   └── secure_credentials.py  # Exemplo de credenciais seguras
├── tests/                     # Testes automatizados
│   ├── __init__.py            # Inicialização dos testes
│   ├── conftest.py            # Configuração do pytest
│   ├── test_logger.py         # Testes do sistema de logging
│   ├── test_restic.py         # Testes das configurações Restic
│   └── test_restic_client.py  # Testes do cliente Restic
├── restore/                   # Diretório de restauração
├── .env.example              # Exemplo de configuração
├── .env                      # Suas configurações (criar)
├── .gitignore                # Arquivos ignorados pelo Git
├── BOOTSTRAP_GUIDE.md        # Guia de bootstrap
├── COMANDOS.md               # Documentação de comandos
├── CREDENTIAL_SETUP_GUIDE.md # Guia de configuração de credenciais
├── Makefile                  # Comandos make
├── pyproject.toml           # Configuração do projeto Python
├── README.md                # Este arquivo
├── requirements.txt          # Dependências Python
└── SETUP_SAFESTIC.md        # Guia completo de instalação
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

