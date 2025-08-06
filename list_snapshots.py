"""List all snapshots stored in the configured Restic repository."""

from __future__ import annotations

import subprocess
import sys

from services.restic import load_restic_env


def list_snapshots() -> None:
    """Fetch and print all snapshots from the repository."""

    try:
        repository, env, _ = load_restic_env()
    except ValueError as exc:  # pragma: no cover - configuration errors
        print(f"[FATAL] {exc}")
        sys.exit(1)

    print(f"Listando snapshots do repositório: {repository}\n")
    try:
        subprocess.run(
            ["restic", "-r", repository, "snapshots"], env=env, check=True
        )
    except subprocess.CalledProcessError as exc:
        print(f"[ERRO] Falha ao listar snapshots: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    list_snapshots()
