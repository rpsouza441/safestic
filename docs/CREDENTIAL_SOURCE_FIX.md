# Correção do CREDENTIAL_SOURCE - Solução para Erro de Validação

## Problema Identificado

O erro `Input should be a valid string` para `restic_password` no Linux ocorria porque:

1. **Makefile**: Os comandos `make init` e `make dry-run` estavam chamando `load_restic_config()` sem parâmetros
2. **Scripts**: `validate_setup.py` e `health_check.py` também usavam o padrão `credential_source="env"`
3. **Resultado**: Mesmo com `CREDENTIAL_SOURCE=keyring` no `.env`, o sistema tentava carregar a senha do arquivo `.env` em vez do keyring

## Solução Implementada

### 1. Correção do Makefile

**Antes:**
```makefile
$(PYTHON_CMD) -c "from services.restic import load_restic_config; config = load_restic_config(); ..."
```

**Depois:**
```makefile
$(PYTHON_CMD) -c "import os; from dotenv import load_dotenv; load_dotenv(); credential_source = os.getenv('CREDENTIAL_SOURCE', 'env'); config = load_restic_config(credential_source); ..."
```

### 2. Correção dos Scripts

**validate_setup.py e health_check.py:**
```python
# Antes
config = load_restic_config()

# Depois
credential_source = os.getenv('CREDENTIAL_SOURCE', 'env')
config = load_restic_config(credential_source)
```

### 3. Script de Teste

Criado `test_keyring_credential_source.py` para validar:
- Detecção correta do `CREDENTIAL_SOURCE`
- Carregamento da `RESTIC_PASSWORD` da fonte correta
- Validação da configuração completa

## Comandos Corrigidos

- ✅ `make init` - Agora lê `CREDENTIAL_SOURCE` do `.env`
- ✅ `make dry-run` - Agora lê `CREDENTIAL_SOURCE` do `.env`
- ✅ Scripts de validação - Agora usam a fonte correta

## Teste da Solução

```bash
# Testar detecção do CREDENTIAL_SOURCE
python test_keyring_credential_source.py

# Testar comandos do Makefile
make init
make dry-run
```

## Fontes de Credenciais Suportadas

| Fonte | Valor no .env | Descrição |
|-------|---------------|----------|
| Arquivo .env | `CREDENTIAL_SOURCE=env` | Credenciais no arquivo `.env` |
| Keyring | `CREDENTIAL_SOURCE=keyring` | Keyring do sistema operacional |
| AWS Secrets | `CREDENTIAL_SOURCE=aws_secrets` | AWS Secrets Manager |
| Azure KeyVault | `CREDENTIAL_SOURCE=azure_keyvault` | Azure Key Vault |
| GCP Secrets | `CREDENTIAL_SOURCE=gcp_secrets` | Google Cloud Secret Manager |
| SOPS | `CREDENTIAL_SOURCE=sops` | Mozilla SOPS |

## Validação

✅ **Windows**: Testado e funcionando  
✅ **Linux**: Problema resolvido - agora detecta keyring corretamente  
✅ **Compatibilidade**: Mantém suporte a todas as fontes de credenciais  

## Arquivos Modificados

- `Makefile` - Comandos `init` e `dry-run`
- `scripts/validate_setup.py` - Função de validação
- `scripts/health_check.py` - Verificação de saúde
- `test_keyring_credential_source.py` - Script de teste (novo)

---

**Resultado**: O erro `Input should be a valid string` foi completamente resolvido. O sistema agora detecta automaticamente a fonte de credenciais configurada no `.env` e carrega a `RESTIC_PASSWORD` da fonte correta (keyring, env, aws_secrets, etc.).