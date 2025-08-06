import os
import subprocess
import sys
import datetime
import json
from pathlib import Path

from services.restic import load_restic_env

try:
    RESTIC_REPOSITORY, env, _ = load_restic_env()
except ValueError as e:
    print(f"[FATAL] {e}")
    sys.exit(1)

RESTORE_TARGET = os.getenv("RESTORE_TARGET_DIR", "restore")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# === 3. ARGUMENTOS DA LINHA DE COMANDO ===
SNAPSHOT_ID = sys.argv[1] if len(sys.argv) > 1 else "latest"

# === 4. PREPARA AMBIENTE DE LOG ===
try:
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    log_filename = now.strftime(f"{LOG_DIR}/restore_snapshot_%Y%m%d_%H%M%S.log")
except Exception as e:
    print(f"[FATAL] Falha ao criar diretório de log: {e}")
    sys.exit(1)

# Função para registrar mensagens no console e no arquivo
def log(msg, log_file):
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line)
    log_file.write(line + "\n")

# === 5. FUNÇÃO PRINCIPAL DE RESTAURAÇÃO ===
def run_restore_snapshot():
    with open(log_filename, "w", encoding="utf-8") as log_file:
        log("=== Iniciando restauração de snapshot com Restic ===", log_file)
        
        try:
            # Garante que o diretório de restauração exista
            Path(RESTORE_TARGET).mkdir(parents=True, exist_ok=True)
            
            # --- Informações do processo sendo logadas ---
            log(f"Buscando informações do snapshot '{SNAPSHOT_ID}'...", log_file)
            
            result = subprocess.run(
                ["restic", "-r", RESTIC_REPOSITORY, "snapshots", SNAPSHOT_ID, "--json"],
                check=True, capture_output=True, text=True, env=env
            )
            snapshot_data = json.loads(result.stdout)[0]
            
            snapshot_time = datetime.datetime.fromisoformat(snapshot_data["time"].replace("Z", "+00:00"))

            log(f"Snapshot ID: {snapshot_data['short_id']}", log_file)
            log(f"Data do Snapshot: {snapshot_time.strftime('%Y-%m-%d %H:%M:%S')}", log_file)
            log(f"Destino da restauração: {RESTORE_TARGET}", log_file)
            print("\nIniciando processo de restauração... O progresso será exibido abaixo.")
            
            # --- Execução do Restore ---
            # Removido "stderr=log_file" para que o progresso apareça no console
            subprocess.run(
                [
                    "restic", "-r", RESTIC_REPOSITORY,
                    "restore", SNAPSHOT_ID,
                    "--target", RESTORE_TARGET
                ],
                env=env,
                check=True
            )
            
            log("✅ Restauração de snapshot concluída com sucesso.", log_file)

        except subprocess.CalledProcessError as e:
            log(f"[ERRO] O Restic finalizou com um erro.", log_file)
            print(f"Comando com falha: {' '.join(e.cmd)}")
            
        except Exception as e:
            log(f"[ERRO] Uma falha inesperada ocorreu: {e}", log_file)
        
        finally:
            log("=== Fim do processo de restauração ===", log_file)

# === 6. PONTO DE ENTRADA DO SCRIPT ===
if __name__ == "__main__":
    run_restore_snapshot()
