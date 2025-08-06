"""Exibe estatísticas do repositório Restic."""

import os
import subprocess
import json

from services.restic import load_restic_env

try:
    RESTIC_REPOSITORY, env, _ = load_restic_env()
except ValueError as e:
    print(f"[FATAL] {e}")
    exit(1)

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
