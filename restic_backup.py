import os
import sys

from services.restic import load_restic_env
from services.logger import create_log_file, log, run_cmd

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
        result = run_cmd(
            ["restic", "-r", RESTIC_REPOSITORY, "snapshots"],
            log_file,
            "✅ Repositório acessível.",
            "Não foi possível acessar o repositório. Abortando.",
            env,
        )
        if result.returncode != 0:
            return

        # === Executa o backup propriamente dito ===
        cmd_backup = ["restic", "-r", RESTIC_REPOSITORY, "backup"]
        cmd_backup += [d.strip() for d in SOURCE_DIRS if d.strip()]
        cmd_backup += build_args("--exclude", EXCLUDES)
        cmd_backup += build_args("--tag", TAGS)

        log(f"Executando backup de: {', '.join(SOURCE_DIRS)}", log_file)
        run_cmd(cmd_backup, log_file, "Backup concluído.", "Erro durante o backup.", env)

        # === Se ativado, aplica política de retenção ===
        if RETENTION_ENABLED:
            log("Aplicando política de retenção...", log_file)
            cmd_retention = [
                "restic",
                "-r",
                RESTIC_REPOSITORY,
                "forget",
                "--keep-hourly",
                RETENTION_KEEP_HOURLY,
                "--keep-daily",
                RETENTION_KEEP_DAILY,
                "--keep-weekly",
                RETENTION_KEEP_WEEKLY,
                "--keep-monthly",
                RETENTION_KEEP_MONTHLY,
                "--prune",
            ]
            run_cmd(
                cmd_retention,
                log_file,
                "Política de retenção aplicada.",
                "Erro ao aplicar retenção.",
                env,
            )
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
