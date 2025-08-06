"""Helper functions for loading Restic configuration."""

from __future__ import annotations

import os
from dotenv import load_dotenv


def load_restic_env() -> tuple[str, dict[str, str], str]:
    """Load environment variables and build the Restic repository string.

    Returns
    -------
    tuple[str, dict[str, str], str]
        A tuple containing the repository URL, a copy of the environment
        variables and the provider name.

    Raises
    ------
    ValueError
        If required variables are missing or the provider is invalid.
    """

    load_dotenv()

    provider = os.getenv("STORAGE_PROVIDER", "").lower()
    bucket = os.getenv("STORAGE_BUCKET", "")
    password = os.getenv("RESTIC_PASSWORD")

    if provider == "aws":
        repository = f"s3:s3.amazonaws.com/{bucket}"
    elif provider == "azure":
        repository = f"azure:{bucket}:restic"
    elif provider == "gcp":
        repository = f"gs:{bucket}"
    else:
        raise ValueError("STORAGE_PROVIDER inválido. Use 'aws', 'azure' ou 'gcp'")

    if not repository or not password:
        raise ValueError(
            "RESTIC_REPOSITORY e RESTIC_PASSWORD precisam estar definidos no .env"
        )

    env = os.environ.copy()
    return repository, env, provider

