"""Configuracoes e fixtures para testes do projeto safestic."""

import os
import json
import pytest
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_env_vars() -> Dict[str, str]:
    """Retorna variaveis de ambiente simuladas para testes."""
    return {
        "STORAGE_PROVIDER": "aws",
        "STORAGE_BUCKET": "test-bucket",
        "RESTIC_PASSWORD": "test-password",
        "BACKUP_SOURCE_DIRS": "/test/dir1,/test/dir2",
        "RESTIC_EXCLUDES": "*.log,*.tmp",
        "RESTORE_TARGET_DIR": "./test_restore",
        "LOG_DIR": "test_logs",
        "RESTIC_TAGS": "test,unittest",
        "RETENTION_ENABLED": "true",
        "RETENTION_LAST": "5",
        "RETENTION_HOURLY": "24",
        "RETENTION_DAILY": "7",
        "RETENTION_WEEKLY": "4",
        "RETENTION_MONTHLY": "12",
        "RETENTION_YEARLY": "3",
    }


@pytest.fixture
def mock_env(mock_env_vars: Dict[str, str]) -> Generator[None, None, None]:
    """Configura variaveis de ambiente simuladas para testes."""
    original_environ = os.environ.copy()
    os.environ.update(mock_env_vars)
    yield
    os.environ.clear()
    os.environ.update(original_environ)


@pytest.fixture
def mock_successful_subprocess() -> Generator[MagicMock, None, None]:
    """Simula uma execucao bem-sucedida de subprocess."""
    with patch("subprocess.run") as mock_run:
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.stdout = json.dumps({"snapshot": {"id": "abc123"}})
        process_mock.stderr = ""
        mock_run.return_value = process_mock
        yield mock_run


@pytest.fixture
def mock_failed_subprocess() -> Generator[MagicMock, None, None]:
    """Simula uma execucao com falha de subprocess."""
    with patch("subprocess.run") as mock_run:
        process_mock = MagicMock()
        process_mock.returncode = 1
        process_mock.stdout = ""
        process_mock.stderr = "Erro simulado de execucao"
        mock_run.return_value = process_mock
        yield mock_run


@pytest.fixture
def mock_network_error_subprocess() -> Generator[MagicMock, None, None]:
    """Simula um erro de rede no subprocess."""
    with patch("subprocess.run") as mock_run:
        process_mock = MagicMock()
        process_mock.returncode = 1
        process_mock.stdout = ""
        process_mock.stderr = "unable to open config file: Timeout expired"
        mock_run.return_value = process_mock
        yield mock_run


@pytest.fixture
def mock_auth_error_subprocess() -> Generator[MagicMock, None, None]:
    """Simula um erro de autenticacao no subprocess."""
    with patch("subprocess.run") as mock_run:
        process_mock = MagicMock()
        process_mock.returncode = 1
        process_mock.stdout = ""
        process_mock.stderr = "wrong password or no key"
        mock_run.return_value = process_mock
        yield mock_run
