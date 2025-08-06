import os
import subprocess
import sys

from services.restic import load_restic_env
from services.logger import create_log_file, log

# === Carregar configurações do Restic ===
try:
    RESTIC_REPOSITORY, env, _ = load_restic_env()
except ValueError as e:
    print(f"[FATAL] {e}")
    sys.exit(1)

# Diretório onde os logs serão salvos
LOG_DIR = os.getenv("LOG_DIR", "logs")

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
if not any(SOURCE_DIRS):
    print("[FATAL] Variáveis obrigatórias ausentes no .env")
    sys.exit(1)

# === Cria arquivo de log com timestamp ===
log_filename = create_log_file("backup", LOG_DIR)

# === Monta argumentos repetidos como --tag ou --exclude ===
def build_args(prefix, items):
    """Repete ``prefix`` para cada item não vazio.

    Parameters
    ----------
    prefix: str
        Flag a ser repetida, por exemplo ``"--tag"``.
    items: list[str]
        Itens que serão associados ao prefixo.
    """
    return [arg for i in items for arg in (prefix, i.strip()) if i.strip()]

# === Função principal que executa backup e retenção ===
def run_backup():
    with open(log_filename, "w", encoding="utf-8") as log_file:
        log("=== Iniciando backup com Restic ===", log_file)

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
