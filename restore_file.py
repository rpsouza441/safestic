import os
import sys
import json
from pathlib import Path
from datetime import datetime

from services.restic import load_restic_env
from services.logger import create_log_file, log, run_cmd

try:
    RESTIC_REPOSITORY, env, _ = load_restic_env()
except ValueError as e:
    print(f"[FATAL] {e}")
    sys.exit(1)

BASE_RESTORE_TARGET = os.getenv("RESTORE_TARGET_DIR", "restore")
LOG_DIR = os.getenv("LOG_DIR", "logs")  # diretório para salvar logs

# === 3. OBTÊM SNAPSHOT_ID E INCLUDE_PATH DA LINHA DE COMANDO ===
try:
    SNAPSHOT_ID = sys.argv[1] if len(sys.argv) > 1 else "latest"  # id do snapshot
    INCLUDE_PATH = sys.argv[2] if len(sys.argv) > 2 else None       # caminho a restaurar

    if not INCLUDE_PATH:
        raise ValueError("Caminho do arquivo/diretório a restaurar não informado.")

except Exception as e:
    print(f"[FATAL] Erro nos argumentos: {e}")
    print("Uso: python restore_file.py <snapshot_id> <caminho_do_arquivo>")
    sys.exit(1)

# === 4. PREPARA ARQUIVO DE LOG ===
try:
    log_filename = create_log_file("restore_file", LOG_DIR)
except Exception as e:
    print(f"[FATAL] Falha ao preparar log: {e}")
    sys.exit(1)

# === 5. EXECUÇÃO PRINCIPAL COM LOG ===
def run_restore_file():
    """Restaura arquivo ou diretório específico do snapshot."""

    with open(log_filename, "w", encoding="utf-8") as log_file:
        log("=== Iniciando restauração de arquivo com Restic ===", log_file)
        try:
            Path(BASE_RESTORE_TARGET).mkdir(parents=True, exist_ok=True)
            log(f"Buscando informações do snapshot '{SNAPSHOT_ID}'...", log_file)
            result = run_cmd(
                ["restic", "-r", RESTIC_REPOSITORY, "snapshots", SNAPSHOT_ID, "--json"],
                log_file,
                "Metadados do snapshot obtidos.",
                "Falha ao obter metadados do snapshot.",
                env,
            )
            if result.returncode != 0:
                return
            snapshot_data = json.loads(result.stdout)[0]
            snapshot_time = datetime.fromisoformat(snapshot_data["time"].replace("Z", "+00:00"))
            timestamp_str = snapshot_time.strftime("%Y-%m-%d_%H%M%S")
            RESTORE_TARGET = os.path.join(BASE_RESTORE_TARGET, timestamp_str)
            Path(RESTORE_TARGET).mkdir(parents=True, exist_ok=True)

            log(f"Snapshot ID: {snapshot_data['short_id']}", log_file)
            log(f"Data do Snapshot: {snapshot_time.strftime('%Y-%m-%d %H:%M:%S')}", log_file)
            log(f"Arquivo/diretório a restaurar: {INCLUDE_PATH}", log_file)
            log(f"Destino da restauração: {RESTORE_TARGET}", log_file)

            # --- Execução do Restore ---
            run_cmd(
                [
                    "restic", "-r", RESTIC_REPOSITORY,
                    "restore", SNAPSHOT_ID,
                    "--target", RESTORE_TARGET,
                    "--include", INCLUDE_PATH,
                ],
                log_file,
                "✅ Arquivo ou diretório restaurado com sucesso.",
                "[ERRO] O Restic finalizou com um erro.",
                env,
            )

        except Exception as e:
            log(f"[ERRO] Uma falha inesperada ocorreu: {e}", log_file)

        finally:
            log("=== Fim do processo de restauração ===", log_file)

# === 6. PONTO DE ENTRADA DO SCRIPT ===
if __name__ == "__main__":
    run_restore_file()
