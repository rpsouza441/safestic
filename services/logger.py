"""Utility helpers for timestamped logging in scripts."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import TextIO


def create_log_file(prefix: str, log_dir: str) -> str:
    """Return a new log file path inside ``log_dir`` using ``prefix``.

    Parameters
    ----------
    prefix: str
        Short identifier used in the log file name, e.g. ``"backup"``.
    log_dir: str
        Directory where the log file will be created.

    Returns
    -------
    str
        Full path to the newly created log file. The directory is created
        automatically if it does not exist.
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    return now.strftime(f"{log_dir}/{prefix}_%Y%m%d_%H%M%S.log")


def log(msg: str, log_file: TextIO) -> None:
    """Print ``msg`` and append it to ``log_file`` with a timestamp."""
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line)
    log_file.write(line + "\n")
