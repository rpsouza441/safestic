# restore_file.py
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
    BASE_RESTORE_TARGET  = os.getenv("RESTORE_TARGET_DIR", "restore")

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
    print(f"[DEBUG] INCLUDE_PATH corrigido: {INCLUDE_PATH}")

except Exception as e:
    print(f"[FATAL] Erro nos argumentos: {e}")
    print("Uso: python restore_file.py <snapshot_id> <caminho_do_arquivo>")
    sys.exit(1)

# === 4. GARANTE QUE DIRETÓRIO DE RESTAURAÇÃO EXISTA ===
try:
    Path(BASE_RESTORE_TARGET).mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"[FATAL] Falha ao criar diretório de restauração: {e}")
    sys.exit(1)
    

# === 5. BUSCA DATA DO SNAPSHOT COM restic snapshots --json ===
print("🔎 Buscando data do snapshot...")

try:
    result = subprocess.run(
        ["restic", "-r", RESTIC_REPOSITORY, "snapshots", "--json"],
        check=True,
        capture_output=True,
        env=os.environ.copy()
    )
    snapshots = json.loads(result.stdout)
    snapshot = next((s for s in snapshots if s["short_id"] == SNAPSHOT_ID or s["id"].startswith(SNAPSHOT_ID)), None)

    if not snapshot:
        raise ValueError(f"Snapshot com ID '{SNAPSHOT_ID}' não encontrado.")

    # Converte data ISO para YYYY-MM-DD_HHMMSS
    snapshot_time = datetime.fromisoformat(snapshot["time"].replace("Z", "+00:00"))
    timestamp_str = snapshot_time.strftime("%Y-%m-%d_%H%M%S")
except Exception as e:
    print(f"[FATAL] Erro ao obter data do snapshot: {e}")
    sys.exit(1)

# === 6. CRIA DESTINO FINAL: BASE + TIMESTAMP ===
RESTORE_TARGET = os.path.join(BASE_RESTORE_TARGET, timestamp_str)
Path(RESTORE_TARGET).mkdir(parents=True, exist_ok=True)

# === 5. EXECUTA O COMANDO RESTIC RESTORE COM --include ===
print(f"🔍 Restaurando '{INCLUDE_PATH}' do snapshot '{SNAPSHOT_ID}' para: {RESTORE_TARGET}\n")

env = os.environ.copy()

try:
    subprocess.run(
        [
            "restic", "-r", RESTIC_REPOSITORY,
            "restore", SNAPSHOT_ID,
            "--target", RESTORE_TARGET,
            "--include", INCLUDE_PATH
        ],
        env=env, check=True
    )
    print("✅ Arquivo ou diretório restaurado com sucesso.")
except subprocess.CalledProcessError as e:
    print(f"[ERRO] Falha na restauração: {e}")
