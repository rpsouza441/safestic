import os
import subprocess
import sys
from dotenv import load_dotenv

# === 1. Carregar variáveis do .env ===
load_dotenv()

# === 2. Detectar provedor e montar RESTIC_REPOSITORY ===
PROVIDER = os.getenv("STORAGE_PROVIDER", "").lower()
BUCKET = os.getenv("STORAGE_BUCKET", "")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")

if PROVIDER == "aws":
    RESTIC_REPOSITORY = f"s3:s3.amazonaws.com/{BUCKET}"
elif PROVIDER == "azure":
    RESTIC_REPOSITORY = f"azure:{BUCKET}:restic"
elif PROVIDER == "gcp":
    RESTIC_REPOSITORY = f"gs:{BUCKET}"
else:
    print("[FATAL] STORAGE_PROVIDER inválido. Use 'aws', 'azure' ou 'gcp'")
    sys.exit(1)

# === 3. Verificar variáveis obrigatórias ===
if not RESTIC_REPOSITORY or not RESTIC_PASSWORD:
    print("[FATAL] Variáveis obrigatórias ausentes no .env")
    sys.exit(1)

# === 4. Coletar políticas de retenção do .env ou usar defaults ===
RETENTION_KEEP_DAILY = os.getenv("RETENTION_KEEP_DAILY", "7")
RETENTION_KEEP_WEEKLY = os.getenv("RETENTION_KEEP_WEEKLY", "4")
RETENTION_KEEP_MONTHLY = os.getenv("RETENTION_KEEP_MONTHLY", "6")

print("Aplicando política de retenção manual:")
print(f"  Diário:   {RETENTION_KEEP_DAILY}")
print(f"  Semanal:  {RETENTION_KEEP_WEEKLY}")
print(f"  Mensal:   {RETENTION_KEEP_MONTHLY}")
print()

# === 5. Executar comando restic forget --prune ===
env = os.environ.copy()

try:
    subprocess.run(
        [
            "restic", "-r", RESTIC_REPOSITORY, "forget",
            "--keep-daily", RETENTION_KEEP_DAILY,
            "--keep-weekly", RETENTION_KEEP_WEEKLY,
            "--keep-monthly", RETENTION_KEEP_MONTHLY,
            "--prune"
        ],
        env=env,
        check=True
    )
    print("Política de retenção aplicada com sucesso.")
except subprocess.CalledProcessError:
    print("Erro ao aplicar política de retenção.")
    sys.exit(1)
