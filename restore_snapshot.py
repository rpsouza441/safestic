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
RESTORE_TARGET = os.getenv("RESTORE_TARGET_DIR", "restore")  # destino da restauração

# Montagem dinâmica do repositório com base no provedor
if PROVIDER == "aws":
    RESTIC_REPOSITORY = f"s3:s3.amazonaws.com/{BUCKET}"
elif PROVIDER == "azure":
    RESTIC_REPOSITORY = f"azure:{BUCKET}:restic"
elif PROVIDER == "gcp":
    RESTIC_REPOSITORY = f"gs:{BUCKET}"
else:
    print("[FATAL] STORAGE_PROVIDER inválido ou não definido. Use 'aws', 'azure' ou 'gcp'")
    sys.exit(1)

# === 3. VALIDAR VARIÁVEIS OBRIGATÓRIAS ===
if not RESTIC_REPOSITORY or not RESTIC_PASSWORD:
    print("[FATAL] RESTIC_REPOSITORY e RESTIC_PASSWORD precisam estar definidos corretamente.")
    sys.exit(1)

# === 4. DEFINIR SNAPSHOT_ID A PARTIR DA LINHA DE COMANDO OU DEFAULT ===
SNAPSHOT_ID = sys.argv[1] if len(sys.argv) > 1 else "latest"

# === 5. CRIAR DIRETÓRIO DE DESTINO SE NÃO EXISTIR ===
Path(RESTORE_TARGET).mkdir(parents=True, exist_ok=True)

# === 6. EXECUTAR O COMANDO RESTIC RESTORE ===
env = os.environ.copy()

print(f"Restaurando snapshot '{SNAPSHOT_ID}' para o diretório: '{RESTORE_TARGET}'\n")

try:
    subprocess.run(
        ["restic", "-r", RESTIC_REPOSITORY, "restore", SNAPSHOT_ID, "--target", RESTORE_TARGET],
        env=env, check=True
    )
    print("Restauração concluída com sucesso.")
except subprocess.CalledProcessError as e:
    print(f"[ERRO] Falha na restauração: {e}")
