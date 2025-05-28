# restore_file.py
import os
import subprocess
import sys
from dotenv import load_dotenv
from pathlib import Path

# === 1. CARREGAR VARIÁVEIS DO .ENV ===
load_dotenv()

# === 2. DETERMINAR PROVEDOR E MONTAR O RESTIC_REPOSITORY ===
PROVIDER = os.getenv("STORAGE_PROVIDER", "").lower()
BUCKET = os.getenv("STORAGE_BUCKET", "")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")
RESTORE_TARGET = os.getenv("RESTORE_TARGET_DIR", "restore")

# Construir a URL do repositório de acordo com o provedor
if PROVIDER == "aws":
    RESTIC_REPOSITORY = f"s3:s3.amazonaws.com/{BUCKET}"
elif PROVIDER == "azure":
    RESTIC_REPOSITORY = f"azure:{BUCKET}:restic"
elif PROVIDER == "gcp":
    RESTIC_REPOSITORY = f"gs:{BUCKET}"
else:
    print("[FATAL] STORAGE_PROVIDER inválido. Use 'aws', 'azure' ou 'gcp'")
    sys.exit(1)

# === 3. VALIDAR VARIÁVEIS OBRIGATÓRIAS ===
if not RESTIC_REPOSITORY or not RESTIC_PASSWORD:
    print("[FATAL] RESTIC_REPOSITORY e RESTIC_PASSWORD precisam estar definidos.")
    sys.exit(1)

# === 4. OBTÊM SNAPSHOT_ID E INCLUDE_PATH DA LINHA DE COMANDO ===
SNAPSHOT_ID = sys.argv[1] if len(sys.argv) > 1 else "latest"  # ID do snapshot ou 'latest'
INCLUDE_PATH = sys.argv[2] if len(sys.argv) > 2 else None     # Caminho específico a restaurar

if not INCLUDE_PATH:
    print("[FATAL] Caminho do arquivo/diretório a restaurar não informado.")
    print("Uso: python restore_file.py <snapshot_id> <caminho_do_arquivo>")
    sys.exit(1)

# === 5. GARANTE QUE DIRETÓRIO DE RESTAURAÇÃO EXISTA ===
Path(RESTORE_TARGET).mkdir(parents=True, exist_ok=True)

# === 6. EXECUTA O COMANDO RESTIC RESTORE COM --include ===
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
