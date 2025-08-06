import os
import subprocess
import sys

from services.restic import load_restic_env

# === 1. Carregar configurações do Restic ===
try:
    RESTIC_REPOSITORY, env, _ = load_restic_env()
except ValueError as e:
    print(f"[FATAL] {e}")
    sys.exit(1)

# === 2. Obter o snapshot ID da linha de comando (ou usar 'latest') ===
SNAPSHOT_ID = sys.argv[1] if len(sys.argv) > 1 else "latest"

# === 3. Executar o comando restic ls para listar os arquivos do snapshot ===

print(f"📂 Listando arquivos do snapshot '{SNAPSHOT_ID}'...")

try:
    subprocess.run(
        ["restic", "-r", RESTIC_REPOSITORY, "ls", SNAPSHOT_ID],
        env=env,
        check=True
    )
except subprocess.CalledProcessError as e:
    print(f"[ERRO] Falha ao listar arquivos do snapshot: {e}")
