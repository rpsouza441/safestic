"""List snapshots and their approximate restore size from a Restic repository."""

from __future__ import annotations

import json
import subprocess
import sys

from services.restic import load_restic_env


def list_snapshots_with_size() -> None:
    """Print snapshot information including estimated restore size."""

    try:
        repository, env, _ = load_restic_env()
    except ValueError as exc:  # pragma: no cover - configuration errors
        print(f"[FATAL] {exc}")
        sys.exit(1)

    try:
        result = subprocess.run(
            ["restic", "-r", repository, "snapshots", "--json"],
            env=env,
            capture_output=True,
            check=True,
            text=True,
        )
        snapshots = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"[FATAL] Falha ao buscar snapshots: {exc}")
        sys.exit(1)

    print(f"Listando snapshots do repositório: {repository}\n")

    for snap in snapshots:
        short_id = snap["short_id"]
        time = snap["time"]
        hostname = snap["hostname"]
        paths = ", ".join(snap["paths"])

        try:
            stats_result = subprocess.run(
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
                env=env,
                capture_output=True,
                check=True,
                text=True,
            )
            stats = json.loads(stats_result.stdout)
            total_bytes = stats.get("total_size", 0)
            total_gib = total_bytes / (1024 ** 3)
            print(f"{short_id} | {time} | {hostname} | {paths} | {total_gib:.3f} GiB")
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            print(
                f"{short_id} | {time} | {hostname} | {paths} | (erro ao calcular tamanho)"
            )


if __name__ == "__main__":
    list_snapshots_with_size()
