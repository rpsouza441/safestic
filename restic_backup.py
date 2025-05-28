import os
import subprocess
import datetime
import sys
from pathlib import Path
from dotenv import load_dotenv

# === Carrega as variáveis do .env para o ambiente ===
load_dotenv()

# === Detecta o tipo de provedor e monta o repositório RESTIC ===
PROVIDER = os.getenv("STORAGE_PROVIDER", "").lower()
BUCKET = os.getenv("STORAGE_BUCKET", "")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")
LOG_DIR = os.getenv("LOG_DIR", "logs")  # onde os logs serão salvos

# Define a URL do repositório conforme o provedor
if PROVIDER == "aws":
    RESTIC_REPOSITORY = f"s3:s3.amazonaws.com/{BUCKET}"
elif PROVIDER == "azure":
    RESTIC_REPOSITORY = f"azure:{BUCKET}:restic"
elif PROVIDER == "gcp":
    RESTIC_REPOSITORY = f"gs:{BUCKET}"
else:
    print("[FATAL] STORAGE_PROVIDER inválido. Use 'aws', 'azure' ou 'gcp'")
    sys.exit(1)

# === Configurações de backup ===
SOURCE_DIRS = os.getenv("BACKUP_SOURCE_DIRS", "").split(",")  # múltiplos diretórios
EXCLUDES = os.getenv("RESTIC_EXCLUDES", "").split(",")        # padrões de exclusão
TAGS = os.getenv("RESTIC_TAGS", "").split(",")                # tags aplicadas ao snapshot

# === Política de retenção configurável ===
RETENTION_ENABLED = os.getenv("RETENTION_ENABLED", "true").lower() == "true"
RETENTION_KEEP_HOURLY  = os.getenv("RETENTION_KEEP_HOURLY", "0")  
RETENTION_KEEP_DAILY = os.getenv("RETENTION_KEEP_DAILY", "7")
RETENTION_KEEP_WEEKLY = os.getenv("RETENTION_KEEP_WEEKLY", "4")
RETENTION_KEEP_MONTHLY = os.getenv("RETENTION_KEEP_MONTHLY", "6")

# === Verificações mínimas obrigatórias ===
if not RESTIC_REPOSITORY or not RESTIC_PASSWORD or not any(SOURCE_DIRS):
    print("[FATAL] Variáveis obrigatórias ausentes no .env")
    sys.exit(1)

# === Cria pasta de logs (se não existir) ===
Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
now = datetime.datetime.now()
log_filename = now.strftime(f"{LOG_DIR}/backup_%Y%m%d_%H%M%S.log")

# === Função de log com timestamp ===
def log(msg, log_file):
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line)
    log_file.write(line + "\n")

# === Monta argumentos repetidos como --tag ou --exclude ===
def build_args(prefix, items):
    return [arg for i in items for arg in (prefix, i.strip()) if i.strip()]

# === Função principal que executa backup e retenção ===
def run_backup():
    with open(log_filename, "w", encoding="utf-8") as log_file:
        log("=== Iniciando backup com Restic ===", log_file)
        env = os.environ.copy()

        # === Verifica se o repositório é acessível ===
        log("🔍 Verificando acesso ao repositório...", log_file)
        try:
            subprocess.run(
                ["restic", "-r", RESTIC_REPOSITORY, "snapshots"],
                env=env, check=True, stdout=log_file, stderr=log_file
            )
            log("✅ Repositório acessível.", log_file)
        except subprocess.CalledProcessError:
            log("Não foi possível acessar o repositório. Abortando.", log_file)
            return

        # === Executa o backup propriamente dito ===
        cmd_backup = ["restic", "-r", RESTIC_REPOSITORY, "backup"]
        cmd_backup += [d.strip() for d in SOURCE_DIRS if d.strip()]
        cmd_backup += build_args("--exclude", EXCLUDES)
        cmd_backup += build_args("--tag", TAGS)

        log(f"Executando backup de: {', '.join(SOURCE_DIRS)}", log_file)
        try:
            subprocess.run(cmd_backup, env=env, check=True, stdout=log_file, stderr=log_file)
            log("Backup concluído.", log_file)
        except subprocess.CalledProcessError:
            log("Erro durante o backup.", log_file)

        # === Se ativado, aplica política de retenção ===
        if RETENTION_ENABLED:
            log("Aplicando política de retenção...", log_file)
            cmd_retention = [
                "restic", "-r", RESTIC_REPOSITORY, "forget",
                "--keep-hourly", RETENTION_KEEP_HOURLY,     
                "--keep-daily", RETENTION_KEEP_DAILY,
                "--keep-weekly", RETENTION_KEEP_WEEKLY,
                "--keep-monthly", RETENTION_KEEP_MONTHLY,
                "--prune"
            ]
            try:
                subprocess.run(cmd_retention, env=env, check=True, stdout=log_file, stderr=log_file)
                log("Política de retenção aplicada.", log_file)
            except subprocess.CalledProcessError:
                log("Erro ao aplicar retenção.", log_file)
        else:
            log("Retenção desativada via .env.", log_file)

        log("=== Fim do backup ===", log_file)

# === Execução principal ===
if __name__ == "__main__":
    try:
        run_backup()
    except Exception as e:
        print(f"[FATAL] Erro inesperado: {e}")
        sys.exit(1)
