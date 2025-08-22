# Correção de Dependências no Linux

Este documento explica como resolver o erro `ModuleNotFoundError: No module named 'pythonjsonlogger'` e outros problemas de dependências no Linux.

## Problema Identificado

O erro ocorre quando:
1. O ambiente virtual não está ativo
2. As dependências não foram instaladas corretamente
3. O `python-json-logger` não está disponível

## Solução Rápida

### 1. Verificar o Ambiente

```bash
# Verificar se o ambiente está configurado corretamente
make verify-env
```

### 2. Ativar o Ambiente Virtual

```bash
# No Linux/Unix
source .venv/bin/activate

# Verificar se está ativo (deve mostrar (.venv) no prompt)
which python
```

### 3. Reinstalar Dependências

```bash
# Método 1: Via pyproject.toml (recomendado)
pip install -e .

# Método 2: Via requirements.txt (fallback)
pip install -r requirements.txt

# Método 3: Instalar dependência específica
pip install python-json-logger>=2.0.0
```

### 4. Verificar Instalação

```bash
# Testar importação
python -c "import pythonjsonlogger; print('OK')"

# Verificar ambiente completo
python scripts/verify_environment.py
```

### 5. Executar Verificação

```bash
# Agora deve funcionar
make check
```

## Solução Detalhada

### Diagnóstico Completo

```bash
# 1. Verificar Python e ambiente virtual
which python
python --version
echo $VIRTUAL_ENV

# 2. Verificar dependências instaladas
pip list | grep -E "(pydantic|dotenv|colorama|requests|psutil|python-json-logger)"

# 3. Testar importações críticas
python -c "
import pydantic
import dotenv
import colorama
import requests
import psutil
import pythonjsonlogger
print('Todas as dependências OK')
"
```

### Reinstalação Completa

Se o problema persistir:

```bash
# 1. Desativar ambiente virtual
deactivate

# 2. Remover ambiente virtual existente
rm -rf .venv

# 3. Recriar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 4. Atualizar pip
pip install --upgrade pip

# 5. Reinstalar dependências
pip install -e .

# 6. Verificar instalação
make verify-env
```

### Dependências Específicas do Linux

Para funcionalidade completa do keyring:

```bash
# Instalar dependências de sistema (já incluídas no setup_linux.sh)
sudo apt-get update
sudo apt-get install -y python3-dev libdbus-glib-1-dev pkg-config cmake build-essential libdbus-1-dev

# Instalar dependências Python opcionais
pip install secretstorage dbus-python keyrings.alt
```

## Comandos Úteis

### Verificação Rápida

```bash
# Verificar ambiente
make verify-env

# Verificar credenciais
make setup-credentials

# Verificar configuração completa
make check
```

### Troubleshooting

```bash
# Ver logs detalhados
python scripts/verify_environment.py

# Testar dependências específicas
python test_dependencies.py

# Verificar keyring (Linux)
python test_linux_keyring.py
```

## Prevenção

### Sempre Ativar o Ambiente Virtual

Adicione ao seu `.bashrc` ou `.zshrc`:

```bash
# Função para ativar automaticamente o ambiente virtual do SafeStic
cd_safestic() {
    cd /path/to/safestic
    if [ -f .venv/bin/activate ]; then
        source .venv/bin/activate
        echo "Ambiente virtual SafeStic ativado"
    fi
}

# Alias para facilitar
alias safestic='cd_safestic'
```

### Script de Inicialização

Crie um script `start_safestic.sh`:

```bash
#!/bin/bash
cd /path/to/safestic
source .venv/bin/activate
echo "SafeStic pronto para uso!"
echo "Execute 'make verify-env' para verificar o ambiente"
bash
```

## Resumo das Correções Aplicadas

1. ✅ **Adicionada dependência `python-json-logger`** ao `pyproject.toml`
2. ✅ **Criado script de verificação** `scripts/verify_environment.py`
3. ✅ **Adicionado comando `make verify-env`** ao Makefile
4. ✅ **Melhorado tratamento de dependências** no `setup_linux.sh`
5. ✅ **Documentação completa** de troubleshooting

## Suporte

Se o problema persistir:

1. Execute `make verify-env` e compartilhe a saída
2. Execute `python scripts/verify_environment.py` e compartilhe os logs
3. Verifique se está usando o ambiente virtual correto
4. Considere reinstalar o ambiente virtual do zero

---

**Nota**: Este documento resolve especificamente o erro `ModuleNotFoundError: No module named 'pythonjsonlogger'` e problemas relacionados de dependências no Linux.