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
LOG_FILE = create_log_file("list_snapshot_files", LOG_DIR)

# === 2. Obter o snapshot ID da linha de comando (ou usar 'latest') ===
SNAPSHOT_ID = sys.argv[1] if len(sys.argv) > 1 else "latest"


def main() -> None:
    with open(LOG_FILE, "w", encoding="utf-8") as log_file:
        log(f"📂 Listando arquivos do snapshot '{SNAPSHOT_ID}'...", log_file)
        success, _ = run_cmd(
            ["restic", "-r", RESTIC_REPOSITORY, "ls", SNAPSHOT_ID],
            log_file,
            env=env,
            error_msg="Falha ao listar arquivos do snapshot",
        )
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
