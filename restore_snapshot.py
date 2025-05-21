import os
import subprocess
import sys
from dotenv import load_dotenv
from pathlib import Path

# === 1. CARREGAR VARIÁVEIS DO .ENV ===
load_dotenv()

RESTIC_REPOSITORY = os.getenv("RESTIC_REPOSITORY")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")
RESTORE_TARGET = os.getenv("RESTORE_TARGET_DIR", "restore")

# === 2. VALIDAR VARIÁVEIS OBRIGATÓRIAS ===
if not RESTIC_REPOSITORY or not RESTIC_PASSWORD:
    print("[FATAL] RESTIC_REPOSITORY e RESTIC_PASSWORD precisam estar definidos no .env")
    sys.exit(1)

# === 3. DEFINIR SNAPSHOT_ID A PARTIR DA LINHA DE COMANDO OU DEFAULT ===
SNAPSHOT_ID = sys.argv[1] if len(sys.argv) > 1 else "latest"

# === 4. CRIAR DIRETÓRIO DE DESTINO SE NÃO EXISTIR ===
Path(RESTORE_TARGET).mkdir(parents=True, exist_ok=True)

# === 5. EXECUTAR RESTORE COM RESTIC ===
env = os.environ.copy()

print(f"♻️ Restaurando snapshot '{SNAPSHOT_ID}' para o diretório: '{RESTORE_TARGET}'\n")

try:
    subprocess.run(
        ["restic", "-r", RESTIC_REPOSITORY, "restore", SNAPSHOT_ID, "--target", RESTORE_TARGET],
        env=env, check=True
    )
    print("✅ Restauração concluída com sucesso.")
except subprocess.CalledProcessError as e:
    print(f"[ERRO] Falha na restauração: {e}")
