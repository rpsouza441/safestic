# Guia de Configuração de Credenciais do Safestic

## Visão Geral

O Safestic agora oferece um sistema robusto e flexível para configuração de credenciais, incluindo o `RESTIC_PASSWORD` obrigatório e credenciais específicas de provedores de nuvem (AWS, Azure, GCP).

## Métodos de Configuração

### 1. Via Makefile (Recomendado)

```bash
# Configuração interativa completa
make setup-credentials

# Configurar apenas RESTIC_PASSWORD
make setup-restic-password

# Forçar uso do keyring do sistema
make setup-credentials-keyring

# Forçar uso do arquivo .env
make setup-credentials-env
```

### 2. Via Script Python Direto

```bash
# Configuração interativa completa
python scripts/setup_credentials.py

# Apenas RESTIC_PASSWORD
python scripts/setup_credentials.py --restic-only

# Forçar fonte específica
python scripts/setup_credentials.py --source keyring
python scripts/setup_credentials.py --source env

# Modo não interativo (para scripts)
python scripts/setup_credentials.py --non-interactive
```

### 3. Via Keyring (Mais Seguro)

```bash
# Configurar RESTIC_PASSWORD via keyring
python -c "import keyring; keyring.set_password('safestic', 'RESTIC_PASSWORD', 'MinhaSenh@Muito$egura123!')"

# Verificar se foi salvo
python -c "import keyring; print('Senha configurada!' if keyring.get_password('safestic', 'RESTIC_PASSWORD') else 'Senha não encontrada')"
```

## Fontes de Credenciais Suportadas

### 🔒 Keyring do Sistema (Recomendado)
- **Mais seguro**: Credenciais criptografadas pelo sistema operacional
- **Não ficam em arquivos de texto**: Reduz risco de exposição
- **Integração nativa**: Funciona com gerenciadores de senha do SO

### 📝 Arquivo .env
- **Prático para desenvolvimento**: Fácil de configurar e testar
- **Menos seguro**: Credenciais em texto plano
- **⚠️ IMPORTANTE**: Nunca commitar arquivo .env no git!

## Credenciais por Provedor

### AWS S3
```bash
# Credenciais necessárias:
- RESTIC_PASSWORD (obrigatório)
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_SESSION_TOKEN (opcional, para credenciais temporárias)
```

### Azure Blob Storage
```bash
# Credenciais necessárias:
- RESTIC_PASSWORD (obrigatório)
- AZURE_ACCOUNT_NAME
- AZURE_ACCOUNT_KEY
```

### Google Cloud Storage
```bash
# Credenciais necessárias:
- RESTIC_PASSWORD (obrigatório)
- GOOGLE_PROJECT_ID
- GOOGLE_APPLICATION_CREDENTIALS (caminho para arquivo JSON)
```

## Validação de Senha RESTIC_PASSWORD

O script valida automaticamente a força da senha do Restic:

### ✅ Critérios de Senha Forte:
- Mínimo de 12 caracteres
- Pelo menos 1 letra maiúscula
- Pelo menos 1 letra minúscula
- Pelo menos 1 número
- Pelo menos 1 caractere especial (!@#$%^&*(),.?":{}|<>)

### 💡 Exemplo de Senha Forte:
```
MinhaSenh@Muito$egura123!
```

### ❌ Exemplos de Senhas Fracas:
```
123456          # Muito simples
password        # Muito comum
restic123       # Muito curta e previsível
```

## Fluxo de Configuração Interativa

### 1. Detecção Automática
O script detecta automaticamente:
- Provedor de nuvem configurado no `.env`
- Credenciais necessárias para o provedor
- Disponibilidade do keyring no sistema

### 2. Escolha da Fonte
Se não especificada via `--source`, o usuário pode escolher:
- Keyring do sistema (recomendado)
- Arquivo .env (desenvolvimento)

### 3. Configuração do RESTIC_PASSWORD
- Verificação se já existe
- Validação de força da senha
- Confirmação da senha
- Avisos de segurança

### 4. Configuração de Credenciais da Nuvem
- Links para documentação oficial
- Prompts específicos por tipo de credencial
- Mascaramento de valores sensíveis

## Exemplos Práticos

### Configuração Inicial Completa
```bash
# 1. Configure o provedor no .env
echo "STORAGE_PROVIDER=aws" >> .env
echo "STORAGE_BUCKET=meu-bucket-backup" >> .env

# 2. Execute a configuração interativa
make setup-credentials

# 3. Verifique a configuração
make check

# 4. Inicialize o repositório
make init

# 5. Faça seu primeiro backup
make backup
```

### Configuração Apenas do RESTIC_PASSWORD
```bash
# Via Makefile
make setup-restic-password

# Via script direto
python scripts/setup_credentials.py --restic-only

# Via keyring (programático)
python -c "import keyring; keyring.set_password('safestic', 'RESTIC_PASSWORD', 'MinhaSenh@Muito$egura123!')"
```

### Configuração para Diferentes Ambientes

#### Desenvolvimento (arquivo .env)
```bash
make setup-credentials-env
```

#### Produção (keyring)
```bash
make setup-credentials-keyring
```

#### CI/CD (variáveis de ambiente)
```bash
# Configure via variáveis de ambiente do sistema
export RESTIC_PASSWORD="MinhaSenh@Muito$egura123!"
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
```

## Troubleshooting

### Keyring não disponível
```bash
# Instalar keyring
pip install keyring

# Verificar se funciona
python -c "import keyring; print('Keyring OK')"
```

### Credenciais não encontradas
```bash
# Verificar credenciais no keyring
python -c "import keyring; print(keyring.get_password('safestic', 'RESTIC_PASSWORD'))"

# Verificar arquivo .env
cat .env | grep RESTIC_PASSWORD
```

### Erro de permissão no arquivo .env
```bash
# Verificar permissões
ls -la .env

# Corrigir permissões (Linux/Mac)
chmod 600 .env
```

## Segurança e Boas Práticas

### ✅ Recomendações de Segurança
1. **Use keyring em produção**: Mais seguro que arquivos de texto
2. **Senhas fortes**: Siga os critérios de validação
3. **Backup da senha**: Guarde o RESTIC_PASSWORD em local seguro
4. **Não commite credenciais**: Adicione .env ao .gitignore
5. **Rotação regular**: Troque credenciais periodicamente

### ❌ Evite
1. Senhas fracas ou previsíveis
2. Commitar arquivos .env no git
3. Compartilhar credenciais por email/chat
4. Usar a mesma senha em múltiplos ambientes
5. Deixar credenciais em logs ou outputs

## Integração com Outros Sistemas

### AWS Secrets Manager
```bash
# Configure CREDENTIAL_SOURCE no .env
CREDENTIAL_SOURCE=aws_secrets
AWS_REGION=us-east-1
AWS_SECRET_NAME=safestic/restic-password
```

### Azure Key Vault
```bash
# Configure CREDENTIAL_SOURCE no .env
CREDENTIAL_SOURCE=azure_keyvault
AZURE_KEYVAULT_URL=https://meu-keyvault.vault.azure.net/
```

### Google Cloud Secret Manager
```bash
# Configure CREDENTIAL_SOURCE no .env
CREDENTIAL_SOURCE=gcp_secrets
GCP_PROJECT_ID=meu-projeto
```

### SOPS (Secrets OPerationS)
```bash
# Configure CREDENTIAL_SOURCE no .env
CREDENTIAL_SOURCE=sops
SOPS_FILE=secrets.yaml
```

## 🔍 Verificacao de Credenciais

### Verificacao Manual

Para verificar se as credenciais estao configuradas corretamente:

```bash
# Verificar todas as configuracoes
make validate

# Verificar acesso ao repositorio
make check

# Verificar apenas credenciais (script direto)
python scripts/check_credentials.py

# Verificar apenas RESTIC_PASSWORD
python scripts/check_credentials.py --restic-only
```

### Verificacao Automatica

O Safestic verifica automaticamente as credenciais antes de executar operacoes criticas:

#### Comandos que Requerem RESTIC_PASSWORD
Estes comandos falham se `RESTIC_PASSWORD` nao estiver configurado:
- `make backup`
- `make list` 
- `make restore`
- `make restore-id`
- `make init`
- `make prune`

#### Comandos que Verificam Todas as Credenciais
Estes comandos verificam `RESTIC_PASSWORD` + credenciais do provedor:
- `make first-run` (falha se nao configuradas)

#### Comandos que Apenas Alertam
Estes comandos alertam mas nao falham:
- `make setup`
- `make bootstrap` 
- `make check`

#### Mensagens de Erro/Aviso

**Erro critico (comando falha):**
```
ERRO: RESTIC_PASSWORD nao configurado!
Execute: make setup-restic-password
```

**Aviso (comando continua):**
```
AVISO: Algumas credenciais nao estao configuradas
Execute: make setup-credentials
```

## Comandos de Ajuda

```bash
# Ver todos os comandos disponíveis
make help

# Ajuda do script de credenciais
python scripts/setup_credentials.py --help

# Verificar configuração atual
make check

# Validar setup completo
make validate-setup
```

Este guia fornece todas as informações necessárias para configurar credenciais de forma segura e eficiente no Safestic. Para dúvidas específicas, consulte a documentação completa no README.md.