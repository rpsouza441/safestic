"""List all snapshots stored in the configured Restic repository."""

from __future__ import annotations

import json
import sys

from services.script import ResticScript


def list_snapshots() -> None:
    """Fetch and print all snapshots from the repository."""

    with ResticScript("list_snapshots") as ctx:
        success, result = ctx.run_cmd(
            ["restic", "-r", ctx.repository, "snapshots", "--json"],
            error_msg="Falha ao listar snapshots",
        )
        if not success or result is None:
            sys.exit(1)
        try:
            snapshots = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            ctx.log(f"Erro ao decodificar JSON: {exc}")
            sys.exit(1)

        ctx.log(f"Listando snapshots do repositório: {ctx.repository}\n")
        print("ID | Data | Hostname | Caminhos")
        for snap in snapshots:
            short_id = snap.get("short_id", "")
            time = snap.get("time", "")
            hostname = snap.get("hostname", "")
            paths = ", ".join(snap.get("paths", []))
            print(f"{short_id} | {time} | {hostname} | {paths}")


if __name__ == "__main__":
    list_snapshots()
