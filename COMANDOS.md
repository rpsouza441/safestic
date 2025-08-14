# 📖 Guia de Comandos do Safestic

Este documento descreve todos os comandos disponiveis no sistema Safestic atraves do `make`.

## 🔧 Como Usar

Todos os comandos devem ser executados no diretorio raiz do projeto:

```bash
make <comando>
```

Para ver a lista completa de comandos:

```bash
make help
```

## 📂 Comandos de Backup

### `make backup`
Executa um backup completo dos diretorios configurados no arquivo `.env`.

**Exemplo:**
```bash
make backup
```

### `make dry-run`
Simula um backup sem executar, mostrando quais arquivos seriam incluidos.

**Exemplo:**
```bash
make dry-run
```

### `make test-backup`
Cria um backup de teste com dados temporarios para validar o funcionamento.

**Exemplo:**
```bash
make test-backup
```

## 📋 Comandos de Listagem e Consulta

### `make list`
Lista todos os snapshots disponiveis no repositorio.

**Exemplo:**
```bash
make list
```

### `make list-size`
Lista todos os snapshots com informacoes de tamanho estimado.

**Exemplo:**
```bash
make list-size
```

### `make list-files`
Lista arquivos contidos em um snapshot especifico.

**Parametros obrigatorios:**
- `ID`: ID do snapshot

**Parametros opcionais:**
- `FORMAT`: Formato de saida (`text` ou `json`)
- `OUTPUT`: Arquivo de saida

**Exemplos:**
```bash
# Listar arquivos em formato texto
make list-files ID=abc123

# Listar arquivos em formato JSON
make list-files ID=abc123 FORMAT=json

# Salvar lista em arquivo
make list-files ID=abc123 OUTPUT=arquivos.txt

# Salvar em JSON
make list-files ID=abc123 FORMAT=json OUTPUT=arquivos.json
```

### `make stats`
Mostra estatisticas detalhadas do repositorio.

**Exemplo:**
```bash
make stats
```

### `make repo-size`
Mostra o tamanho total dos dados unicos armazenados no repositorio.

**Exemplo:**
```bash
make repo-size
```

## 🔄 Comandos de Restauracao

> **💡 DICA:** Use os comandos de restauracao como alternativa ao `make mount` quando o comando mount nao estiver disponivel no restic.

### `make restore`
Restaura o snapshot mais recente para o diretorio configurado.

**Exemplo:**
```bash
make restore
```

### `make restore-id`
Restaura um snapshot especifico.

**Parametros obrigatorios:**
- `ID`: ID do snapshot

**Exemplo:**
```bash
make restore-id ID=abc123
```

### `make restore-file`
Restaura um arquivo ou diretorio especifico de um snapshot.

**Parametros obrigatorios:**
- `ID`: ID do snapshot
- `FILE`: Caminho do arquivo/diretorio (use aspas duplas para caminhos com espacos)

**Exemplos:**
```bash
# Restaurar arquivo simples
make restore-file ID=abc123 FILE="/home/user/documento.txt"

# Restaurar diretorio
make restore-file ID=abc123 FILE="/home/user/Documentos"

# Caminho com espacos (Windows)
make restore-file ID=abc123 FILE="C:/Users/Nome Usuario/Documentos/arquivo.txt"
```

### `make test-restore`
Testa a restauracao com dados temporarios.

**Exemplo:**
```bash
make test-restore
```

### Como Navegar pelos Snapshots (Alternativa ao Mount)

Quando o comando `mount` nao esta disponivel, use esta sequencia:

1. **Listar snapshots disponiveis:**
```bash
make list
```

2. **Ver conteudo de um snapshot especifico:**
```bash
# Configurar repositorio (use o mesmo do .env)
set RESTIC_REPOSITORY=C:\backup
set RESTIC_PASSWORD=sua_senha

# Listar conteudo do snapshot
restic ls SNAPSHOT_ID
# Exemplo: restic ls 2d2cb39d
```

**Alternativa usando Python:**
```bash
python -c "from services.restic_client import ResticClient; client = ResticClient(); print('\n'.join(client.list_files('SNAPSHOT_ID')))"
```

3. **Restaurar arquivos especificos:**
```bash
# Restaurar arquivo unico
make restore-file ID=abc123 FILE="/caminho/para/arquivo.txt"

# Restaurar diretorio completo
make restore-file ID=abc123 FILE="/caminho/para/diretorio"
```

4. **Restaurar snapshot completo:**
```bash
make restore-id ID=abc123
```

## 🧹 Comandos de Manutencao

### `make prune`
Aplica a politica de retencao configurada, removendo snapshots antigos.

**Exemplo:**
```bash
make prune
```

### `make manual-prune`
Executa limpeza manual de snapshots usando script Python dedicado.

**Exemplo:**
```bash
make manual-prune
```

### `make forget`
Esquece snapshots baseado na politica de retencao sem executar prune.

**Exemplo:**
```bash
make forget
```

### `make check`
Verifica se o Restic esta instalado, variaveis estao corretas e repositorio esta acessivel.

**Exemplo:**
```bash
make check
```

### `make rebuild-index`
Reconstroi o indice do repositorio (util para reparar corrupcoes menores).

**Exemplo:**
```bash
make rebuild-index
```

### `make repair`
Repara o repositorio (operacao destrutiva - use com cuidado).

**Exemplo:**
```bash
make repair
```

### `make clean`
Limpa arquivos temporarios e logs antigos (mais de 30 dias).

**Exemplo:**
```bash
make clean
```

## ⚙️ Comandos de Configuracao

### `make setup`
Instala dependencias do sistema e configura o ambiente.

**Exemplo:**
```bash
make setup
```

### `make bootstrap`
Executa bootstrap completo (apenas Windows).

**Exemplo:**
```bash
make bootstrap
```

### `make first-run`
Executa a primeira configuracao do projeto.

**Exemplo:**
```bash
make first-run
```

### `make init`
Inicializa um novo repositorio Restic (apenas se nao existir).

**Exemplo:**
```bash
make init
```

### `make validate`
Valida a configuracao e dependencias do sistema.

**Exemplo:**
```bash
make validate
```

### `make validate-setup`
Valida o setup completo do sistema.

**Exemplo:**
```bash
make validate-setup
```

### `make health`
Verifica a saude completa do sistema de backup.

**Exemplo:**
```bash
make health
```

## 📅 Comandos de Agendamento

### `make schedule-install`
Instala o agendamento automatico de backups.

**Exemplo:**
```bash
make schedule-install
```

### `make schedule-remove`
Remove o agendamento automatico de backups.

**Exemplo:**
```bash
make schedule-remove
```

### `make schedule-status`
Mostra o status do agendamento automatico.

**Exemplo:**
```bash
make schedule-status
```

## 🔧 Comandos Avancados

### `make mount`
Monta o repositorio como sistema de arquivos (requer WinFsp no Windows).

**⚠️ LIMITAcaO ATUAL:**
A versao do restic instalada nao inclui suporte ao comando `mount`. Este e um problema conhecido com algumas distribuicoes do restic.

**Verificar suporte:**
```bash
make check-mount-support
```

**Solucoes:**
1. **Instalar versao completa do restic:**
   - Download: https://github.com/restic/restic/releases
   - Ou compile: `go install github.com/restic/restic/cmd/restic@latest`

2. **Alternativa recomendada - usar restore:**
```bash
# Listar snapshots disponiveis
make list

# Restaurar snapshot especifico
make restore SNAPSHOT_ID=latest
```

**Exemplo (se mount estiver disponivel):**
```bash
make mount
# Acesse: ./mount/snapshots/
```

### `make unmount`
Desmonta o repositorio do sistema de arquivos.

**Exemplo:**
```bash
make unmount
```

## 📚 Comando de Ajuda

### `make help`
Mostra a lista completa de comandos disponiveis com descricoes breves.

**Exemplo:**
```bash
make help
```

## 🔍 Exemplos de Uso Comum

### Backup Completo e Verificacao
```bash
# Executar backup
make backup

# Verificar se funcionou
make list

# Ver estatisticas
make stats
```

### Restauracao de Arquivo Especifico
```bash
# Listar snapshots
make list

# Listar arquivos de um snapshot
make list-files ID=abc123

# Restaurar arquivo especifico
make restore-file ID=abc123 FILE="/caminho/para/arquivo.txt"
```

### Manutencao Regular
```bash
# Verificar saude do sistema
make check

# Limpar snapshots antigos
make manual-prune

# Limpar arquivos temporarios
make clean
```

### Configuracao Inicial
```bash
# Primeira configuracao
make first-run

# Validar configuracao
make validate

# Teste de backup
make test-backup

# Instalar agendamento
make schedule-install
```

## ⚠️ Notas Importantes

1. **Caminhos com Espacos**: Sempre use aspas duplas ao especificar caminhos que contenham espacos.

2. **Comandos Destrutivos**: Os comandos `repair` e `forget` podem ser destrutivos. Use com cuidado.

3. **Privilegios**: Alguns comandos (como `schedule-install`) podem requerer privilegios de administrador.

4. **Compatibilidade**: Os comandos sao compativeis com Windows e Linux, com adaptacoes automaticas.

5. **Logs**: Todos os comandos geram logs detalhados no diretorio `logs/`.

## 🆘 Solucao de Problemas

### Erro "Make nao encontrado"
```bash
# Windows - instalar atraves do Chocolatey
choco install make

# Ou usar mingw32-make se disponivel
```

### Erro "Python nao encontrado"
```bash
# Verificar se Python esta no PATH
python --version

# Ativar ambiente virtual se necessario
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux
```

### Erro "Restic nao encontrado"
```bash
# Verificar instalacao
restic version

# Executar setup se necessario
make setup
```

Para mais informacoes, consulte o arquivo `README.md` ou execute `make help`.
