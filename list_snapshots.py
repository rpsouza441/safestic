import os
import subprocess

from services.restic import load_restic_env

# === 1. Carregar configurações do Restic ===
try:
    RESTIC_REPOSITORY, env, _ = load_restic_env()
except ValueError as e:
    print(f"[FATAL] {e}")
    exit(1)

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
