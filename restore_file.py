import os
import subprocess
import sys
import json
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# === 1. CARREGAR VARIÁVEIS DO .ENV ===
try:
    load_dotenv()
except Exception as e:
    print(f"[FATAL] Erro ao carregar variáveis do .env: {e}")
    sys.exit(1)

# === 2. DETERMINAR PROVEDOR E MONTAR O RESTIC_REPOSITORY ===
try:
    PROVIDER = os.getenv("STORAGE_PROVIDER", "").lower()
    BUCKET = os.getenv("STORAGE_BUCKET", "")
    RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")
    BASE_RESTORE_TARGET = os.getenv("RESTORE_TARGET_DIR", "restore")
    LOG_DIR = os.getenv("LOG_DIR", "logs")

    if PROVIDER == "aws":
        RESTIC_REPOSITORY = f"s3:s3.amazonaws.com/{BUCKET}"
    elif PROVIDER == "azure":
        RESTIC_REPOSITORY = f"azure:{BUCKET}:restic"
    elif PROVIDER == "gcp":
        RESTIC_REPOSITORY = f"gs:{BUCKET}"
    else:
        raise ValueError("STORAGE_PROVIDER inválido. Use 'aws', 'azure' ou 'gcp'")

    if not RESTIC_REPOSITORY or not RESTIC_PASSWORD:
        raise ValueError("RESTIC_REPOSITORY e RESTIC_PASSWORD precisam estar definidos.")

except Exception as e:
    print(f"[FATAL] Erro na configuração do repositório: {e}")
    sys.exit(1)

# === 3. OBTÊM SNAPSHOT_ID E INCLUDE_PATH DA LINHA DE COMANDO ===
try:
    SNAPSHOT_ID = sys.argv[1] if len(sys.argv) > 1 else "latest"
    INCLUDE_PATH = sys.argv[2] if len(sys.argv) > 2 else None

    if not INCLUDE_PATH:
        raise ValueError("Caminho do arquivo/diretório a restaurar não informado.")

except Exception as e:
    print(f"[FATAL] Erro nos argumentos: {e}")
    print("Uso: python restore_file.py <snapshot_id> <caminho_do_arquivo>")
    sys.exit(1)

# === 4. PREPARA AMBIENTE DE LOG ===
try:
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    log_filename = now.strftime(f"{LOG_DIR}/restore_file_%Y%m%d_%H%M%S.log")
except Exception as e:
    print(f"[FATAL] Falha ao criar diretório de log: {e}")
    sys.exit(1)

# Função para registrar mensagens no console e no arquivo
def log(msg, log_file):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line)
    log_file.write(line + "\n")

# === 5. EXECUÇÃO PRINCIPAL COM LOG ===
def run_restore_file():
    with open(log_filename, "w", encoding="utf-8") as log_file:
        log("=== Iniciando restauração de arquivo com Restic ===", log_file)
        try:
            Path(BASE_RESTORE_TARGET).mkdir(parents=True, exist_ok=True)
            log(f"Buscando informações do snapshot '{SNAPSHOT_ID}'...", log_file)
            result = subprocess.run(
                ["restic", "-r", RESTIC_REPOSITORY, "snapshots", SNAPSHOT_ID, "--json"],
                check=True, capture_output=True, text=True, env=os.environ.copy()
            )
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
            # Removido "stderr=log_file" para que o progresso apareça no console
            subprocess.run(
                [
                    "restic", "-r", RESTIC_REPOSITORY,
                    "restore", SNAPSHOT_ID,
                    "--target", RESTORE_TARGET,
                    "--include", INCLUDE_PATH
                ],
                env=os.environ.copy(),
                check=True
            )
            
            log("✅ Arquivo ou diretório restaurado com sucesso.", log_file)

        except subprocess.CalledProcessError as e:
            # Este bloco agora pegará o erro, mas a saída do Restic terá aparecido no console
            log(f"[ERRO] O Restic finalizou com um erro.", log_file)
            print(f"Comando com falha: {' '.join(e.cmd)}")
            
        except Exception as e:
            log(f"[ERRO] Uma falha inesperada ocorreu: {e}", log_file)
        
        finally:
            log("=== Fim do processo de restauração ===", log_file)

# === 6. PONTO DE ENTRADA DO SCRIPT ===
if __name__ == "__main__":
    run_restore_file()