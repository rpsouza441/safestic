"""List all snapshots stored in the configured Restic repository."""

from __future__ import annotations

import os
import sys

from services.restic import load_restic_env
from services.logger import create_log_file, log, run_cmd


def list_snapshots() -> None:
    """Fetch and print all snapshots from the repository."""

    try:
        repository, env, _ = load_restic_env()
    except ValueError as exc:  # pragma: no cover - configuration errors
        print(f"[FATAL] {exc}")
        sys.exit(1)

    log_dir = os.getenv("LOG_DIR", "logs")
    log_filename = create_log_file("list_snapshots", log_dir)

    with open(log_filename, "w", encoding="utf-8") as log_file:
        log(f"Listando snapshots do repositório: {repository}\n", log_file)

        success, _ = run_cmd(
            ["restic", "-r", repository, "snapshots"],
            log_file,
            env=env,
            error_msg="Falha ao listar snapshots",
        )
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    list_snapshots()
