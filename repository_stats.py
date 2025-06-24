# repository_stats.py
import os
import subprocess
import json
from dotenv import load_dotenv

load_dotenv()

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
    print("[FATAL] STORAGE_PROVIDER inválido.")
    exit(1)

if not RESTIC_REPOSITORY or not RESTIC_PASSWORD:
    print("[FATAL] Variáveis obrigatórias ausentes.")
    exit(1)

env = os.environ.copy()

print(f" Obtendo estatísticas gerais do repositório: {RESTIC_REPOSITORY}\n")

try:
    result = subprocess.run(
        ["restic", "-r", RESTIC_REPOSITORY, "stats", "--mode", "raw-data", "--json"],
        env=env,
        capture_output=True,
        check=True,
        text=True
    )
    stats = json.loads(result.stdout)
    size_bytes = stats.get("total_size", 0)
    size_gib = size_bytes / (1024 ** 3)
    print(f" Tamanho total armazenado no repositório (dados únicos): {size_gib:.3f} GiB")
except subprocess.CalledProcessError as e:
    print(f"[ERRO] Falha ao obter estatísticas: {e}")
