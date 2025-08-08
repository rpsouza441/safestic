"""Show overall size information about the Restic repository."""

from __future__ import annotations

import json
import os
import sys

from services.restic import load_restic_env
from services.logger import create_log_file, log, run_cmd


def show_repository_stats() -> None:
    """Print repository size information."""

    try:
        repository, env, _ = load_restic_env()
    except ValueError as exc:  # pragma: no cover - configuration errors
        print(f"[FATAL] {exc}")
        sys.exit(1)

    log_dir = os.getenv("LOG_DIR", "logs")
    log_filename = create_log_file("repository_stats", log_dir)

    with open(log_filename, "w", encoding="utf-8") as log_file:
        log(f"Obtendo estatísticas gerais do repositório: {repository}\n", log_file)

        success, result = run_cmd(
            [
                "restic",
                "-r",
                repository,
                "stats",
                "--mode",
                "raw-data",
                "--json",
            ],
            log_file,
            env=env,
            error_msg="Falha ao obter estatísticas",
        )
        if not success or result is None:
            sys.exit(1)

        try:
            stats = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            log(f"Erro ao decodificar JSON: {exc}", log_file)
            sys.exit(1)

        size_bytes = stats.get("total_size", 0)
        size_gib = size_bytes / (1024 ** 3)
        print(
            f"Tamanho total armazenado no repositório (dados únicos): {size_gib:.3f} GiB",
        )


if __name__ == "__main__":
    show_repository_stats()

