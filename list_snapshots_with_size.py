import os
import subprocess
import json
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

# === 4. Buscar todos os snapshots em JSON ===
try:
    result = subprocess.run(
        ["restic", "-r", RESTIC_REPOSITORY, "snapshots", "--json"],
        env=env,
        capture_output=True,
        check=True,
        text=True
    )
    snapshots = json.loads(result.stdout)
except subprocess.CalledProcessError as e:
    print("[FATAL] Falha ao buscar snapshots:", e)
    exit(1)

# === 5. EXECUTAR O COMANDO RESTIC PARA LISTAR SNAPSHOTS ===
print(f" Listando snapshots do repositório: {RESTIC_REPOSITORY}\n")

for snap in snapshots:
    short_id = snap["short_id"]
    time = snap["time"]
    hostname = snap["hostname"]
    paths = ", ".join(snap["paths"])

    try:
        stats_result = subprocess.run(
            ["restic", "-r", RESTIC_REPOSITORY, "stats", short_id, "--mode", "restore-size", "--json"],
            env=env,
            capture_output=True,
            check=True,
            text=True
        )
        stats = json.loads(stats_result.stdout)
        total_bytes = stats.get("total_size", 0)
        total_gib = total_bytes / (1024 ** 3)
        print(f"{short_id} | {time} | {hostname} | {paths} | {total_gib:.3f} GiB")
    except subprocess.CalledProcessError:
        print(f"{short_id} | {time} | {hostname} | {paths} | (erro ao calcular tamanho)")
