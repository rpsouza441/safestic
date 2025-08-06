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

# === 2. Coletar políticas de retenção do .env ou usar defaults ===
RETENTION_KEEP_DAILY = os.getenv("RETENTION_KEEP_DAILY", "7")
RETENTION_KEEP_WEEKLY = os.getenv("RETENTION_KEEP_WEEKLY", "4")
RETENTION_KEEP_MONTHLY = os.getenv("RETENTION_KEEP_MONTHLY", "6")

print("Aplicando política de retenção manual:")
print(f"  Diário:   {RETENTION_KEEP_DAILY}")
print(f"  Semanal:  {RETENTION_KEEP_WEEKLY}")
print(f"  Mensal:   {RETENTION_KEEP_MONTHLY}")
print()

# === 3. Executar comando restic forget --prune ===

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
