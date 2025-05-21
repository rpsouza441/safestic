import os
import subprocess
from dotenv import load_dotenv

# === 1. CARREGAR VARIÁVEIS DO .ENV ===
load_dotenv()

# === 2. VERIFICAÇÃO DE VARIÁVEIS OBRIGATÓRIAS ===
RESTIC_REPOSITORY = os.getenv("RESTIC_REPOSITORY")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")

if not RESTIC_REPOSITORY or not RESTIC_PASSWORD:
    print("[FATAL] RESTIC_REPOSITORY e RESTIC_PASSWORD precisam estar definidos no arquivo .env")
    exit(1)

# Copiar o ambiente atual (inclui variáveis do sistema + .env)
env = os.environ.copy()

# === 3. EXECUTAR COMANDO DE LISTAGEM DE SNAPSHOTS ===
print(f"📂 Listando snapshots do repositório: {RESTIC_REPOSITORY}\n")

try:
    subprocess.run(
        ["restic", "-r", RESTIC_REPOSITORY, "snapshots"],
        env=env,
        check=True
    )
except subprocess.CalledProcessError as e:
    print(f"[ERRO] Falha ao listar snapshots: {e}")
