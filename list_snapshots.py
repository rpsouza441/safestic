import os
import subprocess
from dotenv import load_dotenv

# === 1. CARREGAR VARIÁVEIS DO .ENV ===
load_dotenv()

# === 2. DETERMINAR PROVEDOR E MONTAR O RESTIC_REPOSITORY ===
PROVIDER = os.getenv("STORAGE_PROVIDER", "").lower()
BUCKET = os.getenv("STORAGE_BUCKET", "")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")

# Montagem do repositório com base no provedor de nuvem
if PROVIDER == "aws":
    RESTIC_REPOSITORY = f"s3:s3.amazonaws.com/{BUCKET}"
elif PROVIDER == "azure":
    RESTIC_REPOSITORY = f"azure:{BUCKET}:restic"
elif PROVIDER == "gcp":
    RESTIC_REPOSITORY = f"gs:{BUCKET}"
else:
    print("[FATAL] STORAGE_PROVIDER inválido. Use 'aws', 'azure' ou 'gcp'")
    exit(1)

# === 3. VERIFICAÇÃO DE VARIÁVEIS OBRIGATÓRIAS ===
if not RESTIC_REPOSITORY or not RESTIC_PASSWORD:
    print("[FATAL] RESTIC_REPOSITORY e RESTIC_PASSWORD precisam estar definidos no .env")
    exit(1)

# Copia o ambiente (incluindo variáveis carregadas)
env = os.environ.copy()

# === 4. EXECUTAR O COMANDO RESTIC PARA LISTAR SNAPSHOTS ===
print(f"istando snapshots do repositório: {RESTIC_REPOSITORY}\n")

try:
    subprocess.run(
        ["restic", "-r", RESTIC_REPOSITORY, "snapshots"],
        env=env,
        check=True
    )
except subprocess.CalledProcessError as e:
    print(f"[ERRO] Falha ao listar snapshots: {e}")
