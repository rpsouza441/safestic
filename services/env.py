"""Utility functions for environment configuration."""

from __future__ import annotations

import os
from dotenv import load_dotenv


def get_credential_source() -> str:
    """Load ``.env`` and return configured ``CREDENTIAL_SOURCE``.

    Returns
    -------
    str
        Value of ``CREDENTIAL_SOURCE`` from environment (default ``"env"``).
    """
    load_dotenv()
    return os.getenv("CREDENTIAL_SOURCE", "env")

