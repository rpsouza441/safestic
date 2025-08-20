# Diagnóstico e Solução: Problemas com Keyring no Linux

## Problema Identificado

O erro `Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]` para `restic_password` indica que o sistema não consegue obter a senha do keyring no Linux.

## Causas Possíveis

### 1. Keyring não funcional em ambiente sem GUI
- Muitos backends de keyring no Linux requerem interface gráfica
- Em ambientes como SSH, WSL, ou servidores sem GUI, o keyring pode falhar
- Backends como `SecretService` precisam de D-Bus e sessão gráfica

### 2. Backend de keyring inadequado
- Linux pode usar diferentes backends: `SecretService`, `KWallet`, `plaintext`, etc.
- Alguns backends não funcionam em todos os ambientes
- Backend `plaintext` pode estar sendo usado como fallback

### 3. Credenciais não armazenadas corretamente
- Senha pode não ter sido salva no keyring
- Nome da aplicação (`APP_NAME`) pode estar incorreto
- Chave da credencial pode estar com nome diferente

### 4. Permissões ou configuração do sistema
- Usuário pode não ter acesso ao keyring
- Serviços de keyring podem não estar rodando
- Configuração do D-Bus pode estar incorreta

## Ferramentas de Diagnóstico

### 1. Script de Diagnóstico Completo
```bash
make debug-keyring
```

Este comando executa `debug_keyring_linux.py` que:
- Verifica se keyring está disponível
- Testa o backend atual
- Verifica se credenciais estão armazenadas
- Testa armazenamento/recuperação
- Analisa o ambiente (GUI, permissões, etc.)

### 2. Detecção Automática de Fonte de Credenciais
```bash
make auto-detect-credentials
```

Este comando executa `auto_detect_credential_source.py` que:
- Analisa o ambiente atual
- Testa funcionalidade do keyring
- Recomenda a melhor fonte de credenciais
- Atualiza automaticamente o `.env` se solicitado

## Soluções

### Solução 1: Usar Arquivo .env (Recomendado para Linux sem GUI)

```bash
# Detectar automaticamente e configurar
make auto-detect-credentials

# Ou configurar manualmente
echo "CREDENTIAL_SOURCE=env" >> .env
make setup-credentials-env
```

### Solução 2: Configurar Keyring Corretamente (Para ambientes com GUI)

```bash
# Diagnosticar primeiro
make debug-keyring

# Se keyring estiver funcional, configurar
make setup-credentials-keyring
```

### Solução 3: Forçar Backend de Keyring Específico

Se o keyring estiver disponível mas usando backend inadequado:

```python
# Adicionar ao início do script ou .env
import keyring
from keyrings.alt import file
keyring.set_keyring(file.PlaintextKeyring())
```

### Solução 4: Configuração Híbrida

Usar keyring quando disponível, fallback para .env:

```bash
# O sistema já faz isso automaticamente
# Mas você pode forçar o fallback
echo "CREDENTIAL_SOURCE=keyring" >> .env
# E manter as credenciais também no .env como backup
```

## Ambientes Específicos

### WSL (Windows Subsystem for Linux)
- Keyring geralmente não funciona
- **Recomendação**: `CREDENTIAL_SOURCE=env`

### SSH/Servidor Remoto
- Sem GUI, keyring limitado
- **Recomendação**: `CREDENTIAL_SOURCE=env`

### Git Bash
- Ambiente Windows, keyring pode funcionar
- **Recomendação**: Testar com `make debug-keyring`

### Desktop Linux (GNOME/KDE)
- Keyring deve funcionar normalmente
- **Recomendação**: `CREDENTIAL_SOURCE=keyring`

## Comandos de Diagnóstico

```bash
# Diagnóstico completo
make debug-keyring

# Detecção automática
make auto-detect-credentials

# Verificar configuração atual
make check

# Testar sem executar
make dry-run

# Configurar credenciais interativamente
make setup-credentials
```

## Logs e Debugging

Para mais informações sobre o que está acontecendo:

```bash
# Executar com logs detalhados
LOG_LEVEL=DEBUG python debug_keyring_linux.py

# Verificar logs do sistema
journalctl --user -u gnome-keyring-daemon
```

## Prevenção

1. **Sempre use detecção automática** em novos ambientes:
   ```bash
   make auto-detect-credentials
   ```

2. **Teste a configuração** antes de usar:
   ```bash
   make check
   make dry-run
   ```

3. **Mantenha backup das credenciais** em local seguro

4. **Documente a configuração** específica do seu ambiente

## Arquivos Relacionados

- `debug_keyring_linux.py` - Script de diagnóstico
- `auto_detect_credential_source.py` - Detecção automática
- `services/credentials.py` - Gerenciamento de credenciais
- `.env` - Configuração de credenciais
- `Makefile` - Comandos de configuração