# Troubleshooting Azure no Linux

Este guia ajuda a resolver problemas específicos do Azure quando executando SafeStic no Linux, especialmente em containers Docker.

## Problemas Comuns

### 1. Repositório "existe" mas não consegue acessar

**Sintomas:**
- `make init` mostra "[OK] Repositorio ja existe e esta acessivel"
- `make check` falha com "Nao foi possivel acessar o repositorio"
- `make check` falha ao tentar inicializar

**Possíveis Causas:**

#### A. Diferenças de Conectividade de Rede
- **Container Docker**: Containers podem ter restrições de rede
- **Firewall**: Linux pode ter regras de firewall diferentes
- **Proxy**: Configurações de proxy podem diferir

#### B. Diferenças de Configuração
- **Variáveis de ambiente**: Podem não estar sendo carregadas corretamente
- **Encoding**: Diferenças na codificação de caracteres
- **Paths**: Caminhos de arquivo podem diferir

#### C. Problemas de Dependências
- **Keyring**: Sistema de keyring pode não estar disponível
- **SSL/TLS**: Certificados podem estar desatualizados
- **Python**: Versões diferentes podem causar problemas

## Diagnóstico Passo a Passo

### Passo 1: Execute o Diagnóstico Automático

```bash
make diagnose-azure-linux
```

Este comando executa uma verificação completa e identifica problemas comuns.

### Passo 2: Verificação Manual das Credenciais

```bash
# Verificar se as variáveis estão definidas
echo "RESTIC_REPOSITORY: $RESTIC_REPOSITORY"
echo "AZURE_ACCOUNT_NAME: $AZURE_ACCOUNT_NAME"
echo "STORAGE_BUCKET: $STORAGE_BUCKET"

# Verificar se a chave está definida (sem mostrar o valor)
if [ -n "$AZURE_ACCOUNT_KEY" ]; then
    echo "AZURE_ACCOUNT_KEY: Definida (${#AZURE_ACCOUNT_KEY} caracteres)"
else
    echo "AZURE_ACCOUNT_KEY: NÃO DEFINIDA"
fi
```

### Passo 3: Teste de Conectividade

```bash
# Testar conectividade básica
ping -c 3 azure.microsoft.com
ping -c 3 login.microsoftonline.com

# Testar resolução DNS
nslookup ${AZURE_ACCOUNT_NAME}.blob.core.windows.net
```

### Passo 4: Teste Direto com Restic

```bash
# Carregar variáveis do .env
source .env

# Testar comando direto
restic -r "$RESTIC_REPOSITORY" snapshots

# Se falhar, tentar inicializar
restic -r "$RESTIC_REPOSITORY" init
```

## Soluções Específicas

### Problema: Container Docker sem Conectividade

**Solução 1: Verificar Rede do Container**
```bash
# Verificar se o container tem acesso à internet
curl -I https://azure.microsoft.com

# Verificar DNS
cat /etc/resolv.conf
```

**Solução 2: Executar com Rede do Host**
```bash
docker run --network host ...
```

### Problema: Credenciais não Carregadas

**Solução 1: Verificar Arquivo .env**
```bash
# Verificar se o arquivo existe e tem as permissões corretas
ls -la .env

# Verificar conteúdo (cuidado com credenciais)
grep -v "KEY\|PASSWORD" .env
```

**Solução 2: Reconfigurar Credenciais**
```bash
# Usar arquivo .env (mais compatível com containers)
make setup-credentials-env

# Ou reconfigurar completamente
rm .env
make setup-credentials
```

### Problema: Keyring não Disponível

**Sintomas:**
- Erros relacionados a `keyring`
- `ModuleNotFoundError: No module named 'secretstorage'`

**Solução:**
```bash
# Instalar dependências do keyring
sudo apt-get update
sudo apt-get install -y python3-secretstorage python3-keyring

# Ou usar arquivo .env em vez do keyring
export CREDENTIAL_SOURCE=env
make setup-credentials-env
```

### Problema: SSL/TLS

**Sintomas:**
- Erros de certificado SSL
- `SSL: CERTIFICATE_VERIFY_FAILED`

**Solução:**
```bash
# Atualizar certificados
sudo apt-get update
sudo apt-get install -y ca-certificates

# Verificar data/hora do sistema
date
```

### Problema: Diferenças de Encoding

**Solução:**
```bash
# Definir encoding UTF-8
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

# Adicionar ao .bashrc para persistir
echo 'export LANG=C.UTF-8' >> ~/.bashrc
echo 'export LC_ALL=C.UTF-8' >> ~/.bashrc
```

## Comparação Windows vs Linux

### Diferenças Conhecidas

| Aspecto | Windows | Linux |
|---------|---------|-------|
| Keyring | Windows Credential Store | GNOME Keyring / KWallet |
| Rede | Geralmente sem proxy | Pode ter proxy corporativo |
| SSL | Certificados do Windows | Certificados do sistema |
| Encoding | CP1252/UTF-16 | UTF-8 |
| Paths | Backslash (\\) | Forward slash (/) |

### Configuração Recomendada para Linux

```bash
# 1. Usar arquivo .env em vez de keyring
export CREDENTIAL_SOURCE=env

# 2. Definir encoding
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

# 3. Verificar conectividade
ping -c 3 azure.microsoft.com

# 4. Configurar credenciais
make setup-credentials-env

# 5. Testar
make diagnose-azure-linux
```

## Logs Detalhados

Para obter logs mais detalhados:

```bash
# Habilitar logs verbosos do restic
export RESTIC_VERBOSE=2

# Executar com logs Python
export PYTHONPATH=.
python -u check_restic_access.py
```

## Quando Pedir Ajuda

Se os passos acima não resolverem, colete as seguintes informações:

1. **Saída do diagnóstico:**
   ```bash
   make diagnose-azure-linux > diagnostico.txt 2>&1
   ```

2. **Informações do sistema:**
   ```bash
   uname -a
   python3 --version
   restic version
   ```

3. **Configuração (sem credenciais):**
   ```bash
   grep -v "KEY\|PASSWORD" .env
   ```

4. **Logs de erro completos:**
   ```bash
   make check > erro_completo.txt 2>&1
   ```

## Prevenção

Para evitar problemas futuros:

1. **Use containers com rede adequada**
2. **Mantenha certificados atualizados**
3. **Use arquivo .env em ambientes containerizados**
4. **Teste conectividade regularmente**
5. **Mantenha logs de configuração funcionais**