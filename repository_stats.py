"""Show overall size information about the Restic repository."""

from __future__ import annotations

import json
import sys

from services.script import ResticScript


def show_repository_stats() -> None:
    """Print repository size information."""

    with ResticScript("repository_stats") as ctx:
        ctx.log(f"Obtendo estatísticas gerais do repositório: {ctx.repository}\n")

        success, result = ctx.run_cmd(
            [
                "restic",
                "-r",
                ctx.repository,
                "stats",
                "--mode",
                "raw-data",
                "--json",
            ],
            error_msg="Falha ao obter estatísticas",
        )
        if not success or result is None:
            sys.exit(1)

        try:
            stats = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            ctx.log(f"Erro ao decodificar JSON: {exc}")
            sys.exit(1)

        size_bytes = stats.get("total_size", 0)
        size_gib = size_bytes / (1024 ** 3)
        print(
            f"Tamanho total armazenado no repositório (dados únicos): {size_gib:.3f} GiB",
        )


if __name__ == "__main__":
    show_repository_stats()

