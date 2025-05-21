import os
import subprocess
import datetime
import sys
from pathlib import Path
from dotenv import load_dotenv

# === 1. Carregar variáveis do .env ===
load_dotenv()

RESTIC_REPOSITORY = os.getenv("RESTIC_REPOSITORY")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# Diretórios a serem backupeados (separados por vírgula)
SOURCE_DIRS = os.getenv("BACKUP_SOURCE_DIRS", "").split(",")

# Exclusões (separadas por vírgula)
EXCLUDES = os.getenv("RESTIC_EXCLUDES", "").split(",")

# Tags (separadas por vírgula)
TAGS = os.getenv("RESTIC_TAGS", "").split(",")

# Controle de retenção
RETENTION_ENABLED = os.getenv("RETENTION_ENABLED", "true").lower() == "true"
RETENTION_KEEP_DAILY = os.getenv("RETENTION_KEEP_DAILY", "7")
RETENTION_KEEP_WEEKLY = os.getenv("RETENTION_KEEP_WEEKLY", "4")
RETENTION_KEEP_MONTHLY = os.getenv("RETENTION_KEEP_MONTHLY", "6")

# Validar variáveis obrigatórias
if not RESTIC_REPOSITORY or not RESTIC_PASSWORD or not any(SOURCE_DIRS):
    print("[FATAL] RESTIC_REPOSITORY, RESTIC_PASSWORD e BACKUP_SOURCE_DIRS devem estar definidos no .env")
    sys.exit(1)

# Criar diretório de logs, se necessário
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
now = datetime.datetime.now()
log_filename = now.strftime(f"{LOG_DIR}/backup_%Y%m%d_%H%M%S.log")

def log(msg, log_file):
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line)
    log_file.write(line + "\n")

def build_args(prefix, items):
    args = []
    for item in items:
        item = item.strip()
        if item:
            args.extend([prefix, item])
    return args

def run_backup():
    with open(log_filename, "w", encoding="utf-8") as log_file:
        log("=== Iniciando backup com Restic ===", log_file)

        env = os.environ.copy()

        # Verificar repositório
        log("🔍 Verificando acesso ao repositório...", log_file)
        try:
            subprocess.run(
                ["restic", "-r", RESTIC_REPOSITORY, "snapshots"],
                env=env, check=True, stdout=log_file, stderr=log_file
            )
            log("✅ Repositório acessível.", log_file)
        except subprocess.CalledProcessError:
            log("❌ Não foi possível acessar o repositório. Abortando.", log_file)
            return

        # Construir comando de backup com diretórios, exclusões e tags
        cmd_backup = ["restic", "-r", RESTIC_REPOSITORY, "backup"]
        cmd_backup += [d.strip() for d in SOURCE_DIRS if d.strip()]
        cmd_backup += build_args("--exclude", EXCLUDES)
        cmd_backup += build_args("--tag", TAGS)

        log(f"💾 Executando backup dos diretórios: {', '.join(SOURCE_DIRS)}", log_file)
        try:
            subprocess.run(cmd_backup, env=env, check=True, stdout=log_file, stderr=log_file)
            log("✅ Backup finalizado com sucesso.", log_file)
        except subprocess.CalledProcessError:
            log("❌ Erro durante o backup. Verifique o log para detalhes.", log_file)

        # Aplicar retenção, se habilitada
        if RETENTION_ENABLED:
            log("🧹 Aplicando política de retenção...", log_file)
            cmd_retention = [
                "restic", "-r", RESTIC_REPOSITORY,
                "forget",
                "--keep-daily", RETENTION_KEEP_DAILY,
                "--keep-weekly", RETENTION_KEEP_WEEKLY,
                "--keep-monthly", RETENTION_KEEP_MONTHLY,
                "--prune"
            ]
            try:
                subprocess.run(cmd_retention, env=env, check=True, stdout=log_file, stderr=log_file)
                log("✅ Política de retenção aplicada.", log_file)
            except subprocess.CalledProcessError:
                log("❌ Erro ao aplicar política de retenção.", log_file)
        else:
            log("ℹ️ Retenção desativada via .env. Nenhum snapshot foi removido.", log_file)

        log("=== Fim do processo de backup ===", log_file)

if __name__ == "__main__":
    try:
        run_backup()
    except Exception as e:
        print(f"[FATAL] Erro inesperado: {e}")
        sys.exit(1)
