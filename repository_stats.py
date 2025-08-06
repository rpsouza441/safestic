"""Display basic statistics from the configured Restic repository."""

from __future__ import annotations

import json
import subprocess
import sys

from services.restic import load_restic_env


def show_repository_stats() -> None:
    """Print repository size information."""

    try:
        repository, env, _ = load_restic_env()
    except ValueError as exc:  # pragma: no cover - configuration errors
        print(f"[FATAL] {exc}")
        sys.exit(1)

    print(f"Obtendo estatísticas gerais do repositório: {repository}\n")

    try:
        result = subprocess.run(
            [
                "restic",
                "-r",
                repository,
                "stats",
                "--mode",
                "raw-data",
                "--json",
            ],
            env=env,
            capture_output=True,
            check=True,
            text=True,
        )
        stats = json.loads(result.stdout)
        size_bytes = stats.get("total_size", 0)
        size_gib = size_bytes / (1024 ** 3)
        print(
            f"Tamanho total armazenado no repositório (dados únicos): {size_gib:.3f} GiB"
        )
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"[ERRO] Falha ao obter estatísticas: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    show_repository_stats()
