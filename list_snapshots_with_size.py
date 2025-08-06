import os
import subprocess
import json

from services.restic import load_restic_env

# === 1. Carregar configurações do Restic ===
try:
    RESTIC_REPOSITORY, env, _ = load_restic_env()
except ValueError as e:
    print(f"[FATAL] {e}")
    exit(1)

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
