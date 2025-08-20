# 🚀 Guia de Bootstrap do SafeStic

Este guia explica como configurar o SafeStic do zero usando o sistema de bootstrap automatizado para **Windows** e **Linux**.

## 📋 Pré-requisitos

### Windows
- **Windows 10/11** com PowerShell 5.1+
- **Permissões de Administrador** (necessário para instalar dependências)
- **Conexão com a Internet** (para download das dependências)

### Linux
- **Distribuição Linux suportada** (Ubuntu/Debian, Fedora/RHEL, Arch, openSUSE)
- **Acesso sudo** (necessário para instalar dependências)
- **Conexão com a Internet** (para download das dependências)

## 🔧 Instalação Automática

### Opção 1: Git Clone + Bootstrap (Recomendado)

**Windows:**
```powershell
# 1. Clone o repositório
git clone https://github.com/seu-usuario/safestic.git
cd safestic

# 2. Execute o bootstrap (como Administrador)
make bootstrap
```

**Linux:**
```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/safestic.git
cd safestic

# 2. Execute o bootstrap (com sudo)
make bootstrap
```

### Opção 2: Bootstrap Automático (Sem Interação)

**Para automação ou CI/CD:**
```bash
# Windows (PowerShell) ou Linux (Bash)
make bootstrap-auto
```

### Opção 3: Download Manual + Bootstrap

**Windows:**
```powershell
# 1. Baixe e extraia o projeto
# 2. Abra PowerShell como Administrador
# 3. Navegue até o diretório do projeto
cd C:\caminho\para\safestic

# 4. Execute o bootstrap
make bootstrap
```

**Linux:**
```bash
# 1. Baixe e extraia o projeto
# 2. Abra terminal
# 3. Navegue até o diretório do projeto
cd /caminho/para/safestic

# 4. Execute o bootstrap
make bootstrap
```

## 🎯 O que o Bootstrap Faz

O comando `make bootstrap` executa automaticamente:

### 1. **Instalação de Dependências do Sistema**

**Windows:**
- ✅ **Git for Windows** - Controle de versão
- ✅ **GNU Make** - Sistema de build
- ✅ **Python 3.12+** - Linguagem de programação
- ✅ **Restic** - Ferramenta de backup
- ✅ **WinFsp** - Sistema de arquivos para comando `mount`

**Linux:**
- ✅ **Git** - Controle de versão
- ✅ **GNU Make** - Sistema de build
- ✅ **Python 3** - Linguagem de programação
- ✅ **pip** - Gerenciador de pacotes Python
- ✅ **python3-venv** - Módulo para ambientes virtuais
- ✅ **Restic** - Ferramenta de backup

### 2. **Configuração do Ambiente Python**
- ✅ Criação do ambiente virtual (`.venv`)
- ✅ Ativação automática do ambiente virtual
- ✅ Atualização do `pip` para a versão mais recente
- ✅ Instalacao de todas as dependencias Python

### 3. **Configuracao do PATH**
- ✅ Adiciona GNU Make ao PATH do sistema
- ✅ Configura Restic no PATH (se necessario)
- ✅ Atualiza variaveis de ambiente permanentemente

## 📊 Verificacao da Instalacao

Apos o bootstrap, execute:

```powershell
# Verificar se tudo esta funcionando
make validate-setup

# Verificar saude do sistema
make health

# Verificar suporte ao comando mount (WinFsp)
make check-mount-support

# Ver todos os comandos disponiveis
make help
```

## 🔧 Configuracao Inicial

### 1. Configurar Arquivo .env

```powershell
# Copiar exemplo de configuracao
cp .env.example .env

# Editar configuracoes (use seu editor preferido)
notepad .env
```

### 2. Inicializar Repositorio

```powershell
# Inicializar repositorio de backup
make init
```

### 3. Primeiro Backup

```powershell
# Executar primeiro backup
make backup
```

## 🐛 Solucao de Problemas

### Problema: "Comando nao encontrado"

**Solucao:** Reinicie o PowerShell apos o bootstrap

```powershell
# Feche e reabra o PowerShell como Administrador
# Navegue novamente para o diretorio do projeto
cd C:\caminho\para\safestic
```

### Problema: "WinFsp nao instalado"

**Solucao:** Instale manualmente o WinFsp

1. Baixe de: https://winfsp.dev/rel/
2. Execute o instalador como Administrador
3. Reinicie o sistema

### Problema: "Ambiente virtual nao funciona"

**Solucao:** Recriar ambiente virtual

```powershell
# Remover ambiente virtual existente
Remove-Item .venv -Recurse -Force

# Executar bootstrap novamente
make bootstrap
```

### Problema: "Permissoes negadas"

**Solucao:** Execute como Administrador

1. Clique com botao direito no PowerShell
2. Selecione "Executar como Administrador"
3. Execute o bootstrap novamente

### Problema: "Comando 'restic mount' nao disponivel"

**Causa:** Algumas versoes do restic nao incluem suporte ao mount

**Verificacao:** Execute `make check-mount-support`

**Solucoes:**
- Baixe versao completa: https://github.com/restic/restic/releases
- Ou compile: `go install github.com/restic/restic/cmd/restic@latest`

**Alternativa:** Use `make restore` ao inves de `make mount`

## 🧪 Teste do Bootstrap

Para testar se o bootstrap funciona corretamente:

```powershell
# Executar teste automatizado
.\test_bootstrap.ps1 -TestDir "C:\temp\safestic-test" -CleanFirst
```

## 📁 Estrutura Apos Bootstrap

```
safestic/
├── .venv/                     # Ambiente virtual Python
│   ├── Scripts/
│   │   ├── python.exe        # Python do ambiente virtual
│   │   ├── pip.exe           # Pip do ambiente virtual
│   │   └── Activate.ps1      # Script de ativacao
│   └── Lib/                  # Bibliotecas instaladas
├── scripts/                   # Scripts de automacao
├── services/                  # Servicos Python
├── .env                      # Suas configuracoes (criar)
├── .env.example              # Exemplo de configuracao
├── Makefile                  # Comandos make
└── requirements.txt          # Dependencias Python
```

## 🎯 Comandos Principais

Apos o bootstrap, voce pode usar:

```powershell
# Backup e Restauracao
make backup                   # Executar backup
make list                     # Listar snapshots
make restore                  # Restaurar ultimo snapshot

# Manutencao
make check                    # Verificar integridade
make prune                    # Limpar snapshots antigos
make mount                    # Montar repositorio (requer WinFsp)

# Configuracao
make validate-setup           # Validar configuracao completa
make health                   # Verificar saude do sistema
make check-mount-support      # Verificar suporte ao mount
make help                     # Ver todos os comandos
```

## 🔄 Atualizacoes

Para atualizar o SafeStic:

```powershell
# Atualizar codigo
git pull origin main

# Atualizar dependencias
pip install -r requirements.txt --upgrade

# Verificar se tudo esta funcionando
make validate-setup
```

## 💡 Dicas Importantes

1. **Sempre execute como Administrador** na primeira vez
2. **Reinicie o terminal** apos o bootstrap
3. **Configure o .env** antes de usar
4. **Use `make help`** para ver todos os comandos
5. **O comando `mount` requer WinFsp** instalado
6. **Mantenha o ambiente virtual ativo** ao usar os scripts

## 🆘 Suporte

Se encontrar problemas:

1. Execute `make validate-setup` para diagnostico
2. Execute `make health` para verificar o sistema
3. Verifique os logs em `logs/`
4. Consulte a documentacao completa no `README.md`

---

**✅ Pronto!** Seu SafeStic esta configurado e pronto para uso!
