# Guia Rápido de Troubleshooting - SafeStic

Este guia fornece comandos rápidos para diagnosticar e resolver problemas comuns no SafeStic.

## 🚨 Problemas Comuns e Soluções Rápidas

### Problema: "Repositório existe mas não consegue acessar" (Linux)

**Diagnóstico Rápido:**
```bash
make diagnose-azure-linux
```

**Soluções Mais Comuns:**
```bash
# 1. Reconfigurar credenciais para usar .env
export CREDENTIAL_SOURCE=env
make setup-credentials-env

# 2. Verificar conectividade
ping -c 3 azure.microsoft.com

# 3. Testar restic diretamente
source .env
restic -r "$RESTIC_REPOSITORY" snapshots
```

### Problema: Diferenças entre Windows e Linux

**Gerar Relatórios de Configuração:**
```bash
# No Windows
make generate-config-report

# No Linux
make generate-config-report

# Comparar (copie um arquivo para o outro sistema)
python scripts/compare_configs.py --compare config_report_windows_*.json config_report_linux_*.json
```

### Problema: Credenciais não funcionam

**Diagnóstico:**
```bash
make diagnose
```

**Soluções:**
```bash
# Reconfigurar completamente
rm .env
make setup-credentials

# Ou usar apenas arquivo .env (mais compatível)
make setup-credentials-env
```

### Problema: Keyring não funciona (Linux)

**Solução:**
```bash
# Instalar dependências
sudo apt-get install -y python3-secretstorage python3-keyring

# Ou usar .env em vez de keyring
export CREDENTIAL_SOURCE=env
make setup-credentials-env
```

### Problema: Erro de SSL/TLS

**Solução:**
```bash
# Atualizar certificados
sudo apt-get update
sudo apt-get install -y ca-certificates

# Verificar data/hora
date
```

### Problema: Container Docker sem conectividade

**Diagnóstico:**
```bash
# Dentro do container
curl -I https://azure.microsoft.com
ping -c 3 8.8.8.8
```

**Solução:**
```bash
# Executar container com rede do host
docker run --network host ...
```

## 🔧 Comandos de Diagnóstico Disponíveis

| Comando | Descrição | Quando Usar |
|---------|-----------|-------------|
| `make diagnose` | Diagnóstico completo | Problemas gerais |
| `make diagnose-azure-linux` | Diagnóstico Azure Linux | Problemas específicos Azure no Linux |
| `make generate-config-report` | Gera relatório do sistema | Comparar configurações |
| `make compare-configs` | Instruções de comparação | Diferenças entre sistemas |
| `make validate` | Valida configuração | Verificar se tudo está OK |
| `make check` | Verifica acesso ao repositório | Problemas de conectividade |

## 📋 Checklist de Troubleshooting

### Antes de Pedir Ajuda

- [ ] Executei `make diagnose` ou `make diagnose-azure-linux`
- [ ] Verifiquei conectividade de rede (`ping azure.microsoft.com`)
- [ ] Testei credenciais (`make validate`)
- [ ] Comparei configurações entre sistemas (se aplicável)
- [ ] Verifiquei logs de erro completos

### Informações para Coleta

```bash
# 1. Relatório de diagnóstico
make diagnose-azure-linux > diagnostico.txt 2>&1

# 2. Informações do sistema
uname -a > sistema.txt
python3 --version >> sistema.txt
restic version >> sistema.txt

# 3. Configuração (sem credenciais)
grep -v "KEY\|PASSWORD" .env > config_anonima.txt

# 4. Logs de erro
make check > erro_completo.txt 2>&1
```

## 🎯 Soluções por Ambiente

### Windows
- Geralmente funciona sem problemas
- Use keyring do Windows para credenciais
- Verifique antivírus se houver problemas

### Linux (Nativo)
- Use `CREDENTIAL_SOURCE=env` para evitar problemas de keyring
- Instale dependências: `sudo apt-get install -y python3-secretstorage`
- Configure encoding: `export LANG=C.UTF-8`

### Linux (Container Docker)
- **SEMPRE** use `CREDENTIAL_SOURCE=env`
- Use `--network host` se houver problemas de conectividade
- Monte volume para persistir `.env`
- Verifique se o container tem acesso à internet

## 🚀 Configuração Recomendada por Ambiente

### Windows (Recomendado)
```bash
make setup-credentials  # Usa keyring automaticamente
```

### Linux Nativo
```bash
export CREDENTIAL_SOURCE=env
export LANG=C.UTF-8
make setup-credentials-env
```

### Docker/Container
```bash
# No Dockerfile ou docker-compose.yml
ENV CREDENTIAL_SOURCE=env
ENV LANG=C.UTF-8

# Depois
make setup-credentials-env
```

## 📞 Quando Pedir Ajuda

Se após seguir este guia o problema persistir, colete:

1. **Saída do diagnóstico**: `make diagnose-azure-linux`
2. **Informações do sistema**: `uname -a`, `python3 --version`, `restic version`
3. **Configuração anonimizada**: `grep -v "KEY\|PASSWORD" .env`
4. **Logs de erro completos**: `make check > erro.txt 2>&1`
5. **Relatório de configuração**: `make generate-config-report`

E descreva:
- O que estava tentando fazer
- O que esperava que acontecesse
- O que realmente aconteceu
- Qual ambiente (Windows/Linux/Docker)
- Se funcionava antes e parou de funcionar