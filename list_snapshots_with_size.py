"""List snapshots and their approximate restore size from a Restic repository."""

from __future__ import annotations

import json
import sys

from services.script import ResticScript


def list_snapshots_with_size() -> None:
    """Print snapshot information including estimated restore size."""

    with ResticScript("list_snapshots_with_size") as ctx:
        success, result = ctx.run_cmd(
            ["restic", "-r", ctx.repository, "snapshots", "--json"],
            error_msg="Falha ao buscar snapshots",
        )
        if not success or result is None:
            sys.exit(1)
        try:
            snapshots = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            ctx.log(f"Erro ao decodificar JSON: {exc}")
            sys.exit(1)

        ctx.log(f"Listando snapshots do repositório: {ctx.repository}\n")

        for snap in snapshots:
            short_id = snap["short_id"]
            time = snap["time"]
            hostname = snap["hostname"]
            paths = ", ".join(snap["paths"])

            success, stats_res = ctx.run_cmd(
                [
                    "restic",
                    "-r",
                    ctx.repository,
                    "stats",
                    short_id,
                    "--mode",
                    "restore-size",
                    "--json",
                ],
                error_msg="Erro ao calcular tamanho",
            )

            if success and stats_res is not None:
                try:
                    stats = json.loads(stats_res.stdout)
                    total_bytes = stats.get("total_size", 0)
                    total_gib = total_bytes / (1024 ** 3)
                    print(
                        f"{short_id} | {time} | {hostname} | {paths} | {total_gib:.3f} GiB",
                    )
                except json.JSONDecodeError:
                    print(
                        f"{short_id} | {time} | {hostname} | {paths} | (erro ao calcular tamanho)",
                    )
            else:
                print(
                    f"{short_id} | {time} | {hostname} | {paths} | (erro ao calcular tamanho)",
                )


if __name__ == "__main__":
    list_snapshots_with_size()
