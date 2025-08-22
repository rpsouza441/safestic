from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Sequence, Optional


@dataclass
class ResticError(Exception):
    """Excecao base para erros relacionados ao Restic."""
    message: str
    command: Sequence[str]
    returncode: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.message} (codigo: {self.returncode})"


class ResticNetworkError(ResticError):
    pass


class ResticRepositoryError(ResticError):
    pass


class ResticAuthenticationError(ResticError):
    pass


class ResticPermissionError(ResticError):
    pass


class ResticCommandError(ResticError):
    pass


def build_restic_command(*args: str) -> List[str]:
    """Constroi a lista de argumentos para chamada ao executavel restic."""
    return ["restic", *args]


def redact_secrets(text: str) -> str:
    """Redaciona senhas e chaves de acesso em strings de texto."""
    patterns = [
        (r"(RESTIC_PASSWORD=)[^\s,]+", r"\1***"),
        (r"(AWS_[^=]+=)[^\s,]+", r"\1***"),
        (r"(AZURE_[^=]+=)[^\s,]+", r"\1***"),
        (r"(GOOGLE_[^=]+=)[^\s,]+", r"\1***"),
        (r"(-p|--password) [^\s]+", r"\1 ***"),
        (r"(-p|--password-file) [^\s]+", r"\1 ***"),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    return result


def raise_for_command_error(
    cmd: Sequence[str],
    returncode: int,
    stdout: str,
    stderr: str,
) -> None:
    """Analisa a saida de um comando e levanta a excecao apropriada."""
    redacted_stdout = redact_secrets(stdout or "")
    redacted_stderr = redact_secrets(stderr or "")

    stderr_lower = redacted_stderr.lower()
    stdout_lower = redacted_stdout.lower()

    if any(msg in stderr_lower or msg in stdout_lower for msg in ["network", "connection", "timeout", "dial tcp"]):
        raise ResticNetworkError(
            message="Erro de rede ao acessar o repositorio",
            command=cmd,
            returncode=returncode,
            stdout=redacted_stdout,
            stderr=redacted_stderr,
        )
    if any(msg in stderr_lower or msg in stdout_lower for msg in ["repository not found", "invalid repository", "corrupted"]):
        raise ResticRepositoryError(
            message="Erro no repositorio Restic",
            command=cmd,
            returncode=returncode,
            stdout=redacted_stdout,
            stderr=redacted_stderr,
        )
    if any(msg in stderr_lower or msg in stdout_lower for msg in ["authentication", "access denied", "wrong password"]):
        raise ResticAuthenticationError(
            message="Erro de autenticacao",
            command=cmd,
            returncode=returncode,
            stdout=redacted_stdout,
            stderr=redacted_stderr,
        )
    if any(msg in stderr_lower or msg in stdout_lower for msg in ["permission", "access is denied", "not permitted"]):
        raise ResticPermissionError(
            message="Erro de permissao",
            command=cmd,
            returncode=returncode,
            stdout=redacted_stdout,
            stderr=redacted_stderr,
        )

    raise ResticCommandError(
        message=f"Comando Restic falhou com codigo {returncode}",
        command=cmd,
        returncode=returncode,
        stdout=redacted_stdout,
        stderr=redacted_stderr,
    )
