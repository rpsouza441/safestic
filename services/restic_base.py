from __future__ import annotations

"""Utilidades compartilhadas para clientes Restic."""

import asyncio
import logging
import random
import shutil
import time
from functools import wraps
from typing import Any, Callable, Sequence, Tuple, TypeVar

from .restic_common import (
    ResticError,
    ResticNetworkError,
    ResticRepositoryError,
    build_restic_command,
    redact_secrets,
)

T = TypeVar("T")
AsyncCallable = Callable[..., Any]


__all__ = [
    "build_restic_command",
    "redact_secrets",
    "check_restic_installed",
    "ensure_restic_installed",
    "with_retry",
    "with_async_retry",
]


def check_restic_installed() -> bool:
    """Verifica se o executável do Restic está disponível."""
    return shutil.which("restic") is not None


def ensure_restic_installed() -> None:
    """Garante que o Restic esteja instalado, levantando erro caso contrário."""
    if not check_restic_installed():
        raise ResticError(
            message="Restic nao esta instalado ou nao esta no PATH",
            command=["restic"],
        )


def with_retry(
    max_attempts: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: float = 0.1,
    retriable_errors: Sequence[type[Exception]] | Tuple[type[Exception], ...] = (
        ResticNetworkError,
        ResticRepositoryError,
    ),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorador para adicionar retry com backoff exponencial a funções."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            attempt = 1
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except tuple(retriable_errors) as exc:  # type: ignore[misc]
                    last_exception = exc
                    if attempt == max_attempts:
                        break
                    backoff = min(
                        max_backoff,
                        initial_backoff * (backoff_factor ** (attempt - 1)),
                    )
                    backoff *= 1 + random.uniform(-jitter, jitter)
                    logging.warning(
                        "Tentativa %d/%d falhou: %s. Tentando novamente em %.2f segundos.",
                        attempt,
                        max_attempts,
                        exc,
                        backoff,
                    )
                    time.sleep(backoff)
                    attempt += 1
                except Exception:
                    raise
            assert last_exception is not None
            raise last_exception

        return wrapper

    return decorator


def with_async_retry(
    max_attempts: int = 3,
    retry_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retriable_errors: Tuple[type[Exception], ...] = (
        ResticNetworkError,
        ResticRepositoryError,
    ),
) -> Callable[[AsyncCallable], AsyncCallable]:
    """Decorador para funções assíncronas com retry automático."""

    def decorator(func: AsyncCallable) -> AsyncCallable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = retry_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retriable_errors as exc:
                    if attempt == max_attempts:
                        logging.error(
                            "Todas as %d tentativas falharam. ultimo erro: %s",
                            max_attempts,
                            exc,
                        )
                        raise
                    logging.warning(
                        "Tentativa %d/%d falhou: %s. Tentando novamente em %.1fs.",
                        attempt,
                        max_attempts,
                        exc,
                        current_delay,
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
                except Exception:
                    raise

        return wrapper

    return decorator
