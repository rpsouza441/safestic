import os
import sys
import datetime
import json
from pathlib import Path

from services.restic import load_restic_env
from services.logger import create_log_file, log, run_cmd

try:
    RESTIC_REPOSITORY, env, _ = load_restic_env()
except ValueError as e:
    print(f"[FATAL] {e}")
    sys.exit(1)

RESTORE_TARGET = os.getenv("RESTORE_TARGET_DIR", "restore")  # destino da restauração
LOG_DIR = os.getenv("LOG_DIR", "logs")  # diretório para logs

# === 3. ARGUMENTOS DA LINHA DE COMANDO ===
SNAPSHOT_ID = sys.argv[1] if len(sys.argv) > 1 else "latest"  # id do snapshot

# === 4. PREPARA ARQUIVO DE LOG ===
try:
    log_filename = create_log_file("restore_snapshot", LOG_DIR)
except Exception as e:
    print(f"[FATAL] Falha ao preparar log: {e}")
    sys.exit(1)

# === 5. FUNÇÃO PRINCIPAL DE RESTAURAÇÃO ===
def run_restore_snapshot():
    """Restaura um snapshot inteiro para o diretório alvo."""

    with open(log_filename, "w", encoding="utf-8") as log_file:
        log("=== Iniciando restauração de snapshot com Restic ===", log_file)
        
        try:
            # Garante que o diretório de restauração exista
            Path(RESTORE_TARGET).mkdir(parents=True, exist_ok=True)

            # --- Informações do processo sendo logadas ---
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

            snapshot_time = datetime.datetime.fromisoformat(snapshot_data["time"].replace("Z", "+00:00"))

            log(f"Snapshot ID: {snapshot_data['short_id']}", log_file)
            log(f"Data do Snapshot: {snapshot_time.strftime('%Y-%m-%d %H:%M:%S')}", log_file)
            log(f"Destino da restauração: {RESTORE_TARGET}", log_file)
            print("\nIniciando processo de restauração... O progresso será exibido abaixo.")

            # --- Execução do Restore ---
            run_cmd(
                [
                    "restic", "-r", RESTIC_REPOSITORY,
                    "restore", SNAPSHOT_ID,
                    "--target", RESTORE_TARGET,
                ],
                log_file,
                "✅ Restauração de snapshot concluída com sucesso.",
                "[ERRO] O Restic finalizou com um erro.",
                env,
            )

        except Exception as e:
            log(f"[ERRO] Uma falha inesperada ocorreu: {e}", log_file)

        finally:
            log("=== Fim do processo de restauração ===", log_file)

# === 6. PONTO DE ENTRADA DO SCRIPT ===
if __name__ == "__main__":
    run_restore_snapshot()
