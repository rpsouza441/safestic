from __future__ import annotations

"""Funcoes e classes utilitarias compartilhadas entre clientes Restic."""

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence


@dataclass
class ResticError(Exception):
    """Excecao base para erros relacionados ao Restic."""

    message: str
    command: Sequence[str]
    returncode: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None

    def __str__(self) -> str:  # pragma: no cover - simples representacao
        return f"{self.message} (codigo: {self.returncode})"


class ResticNetworkError(ResticError):
    """Erro de rede ao acessar o repositorio Restic."""

    pass


class ResticRepositoryError(ResticError):
    """Erro relacionado ao repositorio Restic."""

    pass


class ResticAuthenticationError(ResticError):
    """Erro de autenticacao (senha incorreta, credenciais invalidas, etc.)."""

    pass


class ResticPermissionError(ResticError):
    """Erro de permissao ao acessar arquivos ou o repositorio."""

    pass


class ResticCommandError(ResticError):
    """Erro generico na execucao de um comando Restic."""

    pass


def redact_secrets(text: str) -> str:
    """Redaciona senhas e chaves de acesso em strings de texto."""

    patterns = [
        (r"(RESTIC_PASSWORD=)[^\s,]+", r"\1REDACTED"),
        (r"(AWS_[^=]+=)[^\s,]+", r"\1REDACTED"),
        (r"(AZURE_[^=]+=)[^\s,]+", r"\1REDACTED"),
        (r"(GOOGLE_[^=]+=)[^\s,]+", r"\1REDACTED"),
        (r"(-p|--password) [^\s]+", r"\1 REDACTED"),
        (r"(-p|--password-file) [^\s]+", r"\1 REDACTED"),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)
    return result


def build_restic_command(*args: str, repository: Optional[str] = None) -> List[str]:
    """Constroi a lista de comando base do Restic."""

    cmd: List[str] = ["restic"]
    if repository:
        cmd.extend(["-r", repository])
    cmd.extend(list(args))
    return cmd


def analyze_command_error(
    cmd: Sequence[str],
    returncode: int,
    stdout: str,
    stderr: str,
) -> None:
    """Analisa a saida de erro de um comando Restic e levanta excecao apropriada."""

    combined = f"{stdout}\n{stderr}".lower()
    if any(msg in combined for msg in ["network", "connection", "timeout", "dial tcp"]):
        raise ResticNetworkError(
            message="Erro de rede ao acessar o repositorio",
            command=list(cmd),
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )
    if any(msg in combined for msg in ["repository not found", "invalid repository", "corrupted"]):
        raise ResticRepositoryError(
            message="Erro no repositorio Restic",
            command=list(cmd),
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )
    if any(msg in combined for msg in ["authentication", "access denied", "wrong password"]):
        raise ResticAuthenticationError(
            message="Erro de autenticacao",
            command=list(cmd),
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )
    if any(msg in combined for msg in ["permission", "access is denied", "not permitted"]):
        raise ResticPermissionError(
            message="Erro de permissao",
            command=list(cmd),
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )
    raise ResticCommandError(
        message=f"Comando Restic falhou com codigo {returncode}",
        command=list(cmd),
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )
