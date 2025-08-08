"""List snapshots and their approximate restore size from a Restic repository."""

from __future__ import annotations

import json
import os
import sys

from services.restic import load_restic_env
from services.logger import create_log_file, log, run_cmd


def list_snapshots_with_size() -> None:
    """Print snapshot information including estimated restore size."""

    try:
        repository, env, _ = load_restic_env()
    except ValueError as exc:  # pragma: no cover - configuration errors
        print(f"[FATAL] {exc}")
        sys.exit(1)

    log_dir = os.getenv("LOG_DIR", "logs")
    log_filename = create_log_file("list_snapshots_with_size", log_dir)

    with open(log_filename, "w", encoding="utf-8") as log_file:
        success, result = run_cmd(
            ["restic", "-r", repository, "snapshots", "--json"],
            log_file,
            env=env,
            error_msg="Falha ao buscar snapshots",
        )
        if not success or result is None:
            sys.exit(1)
        try:
            snapshots = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            log(f"Erro ao decodificar JSON: {exc}", log_file)
            sys.exit(1)

        log(f"Listando snapshots do repositório: {repository}\n", log_file)

        for snap in snapshots:
            short_id = snap["short_id"]
            time = snap["time"]
            hostname = snap["hostname"]
            paths = ", ".join(snap["paths"])

            success, stats_res = run_cmd(
                [
                    "restic",
                    "-r",
                    repository,
                    "stats",
                    short_id,
                    "--mode",
                    "restore-size",
                    "--json",
                ],
                log_file,
                env=env,
                error_msg="Erro ao calcular tamanho",
            )

            if success and stats_res is not None:
                try:
                    stats = json.loads(stats_res.stdout)
                    total_bytes = stats.get("total_size", 0)
                    total_gib = total_bytes / (1024 ** 3)
                    print(
                        f"{short_id} | {time} | {hostname} | {paths} | {total_gib:.3f} GiB"
                    )
                except json.JSONDecodeError:
                    print(
                        f"{short_id} | {time} | {hostname} | {paths} | (erro ao calcular tamanho)"
                    )
            else:
                print(
                    f"{short_id} | {time} | {hostname} | {paths} | (erro ao calcular tamanho)"
                )


if __name__ == "__main__":
    list_snapshots_with_size()

