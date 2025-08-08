import os
import sys

from services.restic import load_restic_env
from services.logger import create_log_file, log, run_cmd

# === 1. Carregar configurações do Restic ===
try:
    RESTIC_REPOSITORY, env, _ = load_restic_env()
except ValueError as e:
    print(f"[FATAL] {e}")
    sys.exit(1)

LOG_DIR = os.getenv("LOG_DIR", "logs")
log_filename = create_log_file("manual_prune", LOG_DIR)

# === 2. Coletar políticas de retenção do .env ou usar defaults ===
RETENTION_KEEP_DAILY = os.getenv("RETENTION_KEEP_DAILY", "7")
RETENTION_KEEP_WEEKLY = os.getenv("RETENTION_KEEP_WEEKLY", "4")
RETENTION_KEEP_MONTHLY = os.getenv("RETENTION_KEEP_MONTHLY", "6")


def main() -> None:
    with open(log_filename, "w", encoding="utf-8") as log_file:
        log("Aplicando política de retenção manual:", log_file)
        log(f"  Diário:   {RETENTION_KEEP_DAILY}", log_file)
        log(f"  Semanal:  {RETENTION_KEEP_WEEKLY}", log_file)
        log(f"  Mensal:   {RETENTION_KEEP_MONTHLY}", log_file)

        cmd = [
            "restic",
            "-r",
            RESTIC_REPOSITORY,
            "forget",
            "--keep-daily",
            RETENTION_KEEP_DAILY,
            "--keep-weekly",
            RETENTION_KEEP_WEEKLY,
            "--keep-monthly",
            RETENTION_KEEP_MONTHLY,
            "--prune",
        ]

        success, _ = run_cmd(
            cmd,
            log_file,
            env=env,
            success_msg="Política de retenção aplicada com sucesso.",
            error_msg="Erro ao aplicar política de retenção.",
        )

        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
