import os
import subprocess
import sys
from dotenv import load_dotenv

# === 1. Carregar variáveis do .env ===
load_dotenv()

# === 2. Determinar provedor e montar o RESTIC_REPOSITORY ===
PROVIDER = os.getenv("STORAGE_PROVIDER", "").lower()
BUCKET = os.getenv("STORAGE_BUCKET", "")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")

if PROVIDER == "aws":
    RESTIC_REPOSITORY = f"s3:s3.amazonaws.com/{BUCKET}"
elif PROVIDER == "azure":
    RESTIC_REPOSITORY = f"azure:{BUCKET}"
elif PROVIDER == "gcp":
    RESTIC_REPOSITORY = f"gs:{BUCKET}"
else:
    print("[FATAL] STORAGE_PROVIDER inválido ou não definido. Use 'aws', 'azure' ou 'gcp'")
    sys.exit(1)

# === 3. Validar variáveis obrigatórias ===
if not RESTIC_REPOSITORY or not RESTIC_PASSWORD:
    print("[FATAL] RESTIC_REPOSITORY e RESTIC_PASSWORD precisam estar definidos corretamente.")
    sys.exit(1)

# === 4. Obter o snapshot ID da linha de comando (ou usar 'latest') ===
SNAPSHOT_ID = sys.argv[1] if len(sys.argv) > 1 else "latest"

# === 5. Executar o comando restic ls para listar os arquivos do snapshot ===
env = os.environ.copy()

print(f"📂 Listando arquivos do snapshot '{SNAPSHOT_ID}'...")

try:
    subprocess.run(
        ["restic", "-r", RESTIC_REPOSITORY, "ls", SNAPSHOT_ID],
        env=env,
        check=True
    )
except subprocess.CalledProcessError as e:
    print(f"[ERRO] Falha ao listar arquivos do snapshot: {e}")
