# Troubleshooting: Erro de Validação RESTIC_PASSWORD no Linux

## Problema

Ao executar `make init` no ambiente Linux, ocorre o seguinte erro:

```
Erro de validacao na configuracao do Restic: 1 validation error for ResticConfig
restic_password
  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
```

## Causa

O erro indica que o `RESTIC_PASSWORD` não está sendo encontrado na fonte de credenciais configurada. Isso pode acontecer por:

1. **Arquivo `.env` não existe** ou não está configurado corretamente
2. **CREDENTIAL_SOURCE** não está definido ou está com valor incorreto
3. **RESTIC_PASSWORD** não está configurado na fonte especificada

## Soluções

### 1. Verificar se o arquivo `.env` existe

```bash
# Verificar se .env existe
ls -la .env

# Se não existir, copiar do exemplo
cp .env.example .env
```

### 2. Configurar CREDENTIAL_SOURCE no .env

Edite o arquivo `.env` e configure a fonte de credenciais:

```bash
# Para usar arquivo .env (menos seguro)
CREDENTIAL_SOURCE=env

# Para usar keyring do sistema (mais seguro)
CREDENTIAL_SOURCE=keyring
```

### 3. Configurar RESTIC_PASSWORD

#### Opção A: Usando arquivo .env (CREDENTIAL_SOURCE=env)

```bash
# Editar .env e adicionar:
RESTIC_PASSWORD=sua_senha_super_secreta
```

#### Opção B: Usando keyring do sistema (CREDENTIAL_SOURCE=keyring)

```bash
# Configurar senha no keyring
make setup-restic-password

# Ou manualmente:
python -c "import keyring; keyring.set_password('safestic', 'RESTIC_PASSWORD', 'sua_senha_super_secreta')"
```

### 4. Configuração Completa do .env

Exemplo de arquivo `.env` mínimo funcional:

```bash
# === Configuração Básica ===
RESTC_REPOSITORY=s3:s3.amazonaws.com/seu-bucket/restic
BACKUP_SOURCE_DIRS=/home/user/Documents,/home/user/Pictures
CREDENTIAL_SOURCE=env

# === Credenciais (se CREDENTIAL_SOURCE=env) ===
RESTIC_PASSWORD=sua_senha_super_secreta
AWS_ACCESS_KEY_ID=sua_access_key
AWS_SECRET_ACCESS_KEY=sua_secret_key
```

### 5. Validação da Configuração

```bash
# Testar configuração de credenciais
make check

# Testar carregamento específico do CREDENTIAL_SOURCE
python test_keyring_credential_source.py

# Validar setup completo
make validate-setup
```

## Comandos de Diagnóstico

### Verificar variáveis de ambiente

```bash
# Verificar se .env está sendo carregado
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('CREDENTIAL_SOURCE:', os.getenv('CREDENTIAL_SOURCE')); print('RESTIC_PASSWORD:', 'CONFIGURADO' if os.getenv('RESTIC_PASSWORD') else 'NÃO CONFIGURADO')"
```

### Testar carregamento de credenciais

```bash
# Testar carregamento manual
python -c "from services.credentials import get_credential; import os; from dotenv import load_dotenv; load_dotenv(); cs = os.getenv('CREDENTIAL_SOURCE', 'env'); pwd = get_credential('RESTIC_PASSWORD', cs); print(f'CREDENTIAL_SOURCE: {cs}'); print(f'RESTIC_PASSWORD: {"ENCONTRADO" if pwd else "NÃO ENCONTRADO"}')"
```

## Configuração Recomendada para Linux

### Para Desenvolvimento/Teste (menos seguro)

```bash
# .env
CREDENTIAL_SOURCE=env
RESTIC_PASSWORD=senha_de_teste
# ... outras credenciais
```

### Para Produção (mais seguro)

```bash
# .env
CREDENTIAL_SOURCE=keyring

# Configurar credenciais no keyring
make setup-credentials-keyring
```

## Troubleshooting Avançado

### Problema: Keyring não funciona no Linux

```bash
# Instalar dependências do keyring
sudo apt-get install python3-keyring

# Ou usar .env como fallback
echo "CREDENTIAL_SOURCE=env" >> .env
echo "RESTIC_PASSWORD=sua_senha" >> .env
```

### Problema: Permissões do arquivo .env

```bash
# Ajustar permissões (apenas proprietário pode ler)
chmod 600 .env
```

### Problema: Diretórios de backup não encontrados

```bash
# Verificar se diretórios existem
python -c "from pathlib import Path; dirs = '/etc,/home/user'.split(','); [print(f'{d}: {"OK" if Path(d).exists() else "NÃO ENCONTRADO"}') for d in dirs]"

# Ajustar BACKUP_SOURCE_DIRS no .env
BACKUP_SOURCE_DIRS=/home/user/Documents,/home/user/Pictures
```

## Comandos de Configuração Rápida

```bash
# Setup completo interativo
make setup-credentials

# Setup apenas RESTIC_PASSWORD
make setup-restic-password

# Setup usando keyring
make setup-credentials-keyring

# Setup usando .env
make setup-credentials-env
```

## Verificação Final

Após configurar, teste com:

```bash
# Verificar credenciais
make check

# Inicializar repositório
make init

# Teste de backup
make dry-run
```

Se ainda houver problemas, verifique os logs detalhados executando os comandos Python diretamente para ver mensagens de erro completas.