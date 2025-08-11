"""List all snapshots stored in the configured Restic repository."""

from __future__ import annotations

import sys

from services.script import ResticScript


def list_snapshots() -> None:
    """Fetch and print all snapshots from the repository."""

    with ResticScript("list_snapshots") as ctx:
        ctx.log(f"Listando snapshots do repositório: {ctx.repository}\n")

        success, _ = ctx.run_cmd(
            ["restic", "-r", ctx.repository, "snapshots"],
            error_msg="Falha ao listar snapshots",
        )
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    list_snapshots()
