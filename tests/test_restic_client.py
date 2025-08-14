"""Testes para o modulo services.restic_client."""

import json
import pytest
from unittest.mock import patch, MagicMock

from services.restic_client import (
    ResticClient,
    ResticError,
    ResticNetworkError,
    ResticAuthenticationError,
    ResticRepositoryError,
    redact_secrets,
    with_retry
)


class TestRedactSecrets:
    """Testes para a funcao redact_secrets."""

    def test_redact_password(self) -> None:
        """Testa redacao de senha em texto."""
        text = "RESTIC_PASSWORD=senha123 e mais texto"
        redacted = redact_secrets(text)
        assert "senha123" not in redacted
        assert "REDACTED" in redacted

    def test_redact_aws_keys(self) -> None:
        """Testa redacao de chaves AWS em texto."""
        text = "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        redacted = redact_secrets(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in redacted
        assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in redacted
        assert "REDACTED" in redacted

    def test_redact_azure_keys(self) -> None:
        """Testa redacao de chaves Azure em texto."""
        text = "AZURE_ACCOUNT_NAME=myaccount AZURE_ACCOUNT_KEY=YWNjZXNzLWtleS1oZXJl"
        redacted = redact_secrets(text)
        assert "myaccount" not in redacted
        assert "YWNjZXNzLWtleS1oZXJl" not in redacted
        assert "REDACTED" in redacted


class TestWithRetry:
    """Testes para o decorador with_retry."""

    def test_with_retry_success_first_attempt(self) -> None:
        """Testa funcao que tem sucesso na primeira tentativa."""
        mock_func = MagicMock(return_value="success")
        decorated = with_retry(max_attempts=3)(mock_func)

        result = decorated("arg1", kwarg1="value1")

        assert result == "success"
        mock_func.assert_called_once_with("arg1", kwarg1="value1")

    def test_with_retry_success_after_retries(self) -> None:
        """Testa funcao que tem sucesso apos algumas tentativas."""
        mock_func = MagicMock(side_effect=[ResticNetworkError("Erro de rede", ["restic"]), "success"])
        decorated = with_retry(max_attempts=3)(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 2

    def test_with_retry_max_attempts_exceeded(self) -> None:
        """Testa funcao que falha em todas as tentativas."""
        error = ResticNetworkError("Erro de rede persistente", ["restic"])
        mock_func = MagicMock(side_effect=error)
        decorated = with_retry(max_attempts=3)(mock_func)

        with pytest.raises(ResticNetworkError, match="Erro de rede persistente"):
            decorated()

        assert mock_func.call_count == 3

    def test_with_retry_non_retriable_error(self) -> None:
        """Testa funcao que falha com erro nao-retentavel."""
        error = ResticAuthenticationError("Erro de autenticacao", ["restic"])
        mock_func = MagicMock(side_effect=error)
        decorated = with_retry(max_attempts=3, retriable_errors=[ResticNetworkError])(mock_func)

        with pytest.raises(ResticAuthenticationError, match="Erro de autenticacao"):
            decorated()

        # Nao deve tentar novamente para erros nao retentaveis
        assert mock_func.call_count == 1


class TestResticClient:
    """Testes para a classe ResticClient."""

    def test_init(self) -> None:
        """Testa inicializacao do cliente."""
        client = ResticClient(max_attempts=5)
        assert client.max_attempts == 5

    def test_check_restic_installed_success(self, mock_successful_subprocess) -> None:
        """Testa verificacao de instalacao do Restic com sucesso."""
        client = ResticClient()
        result = client.check_restic_installed()
        assert result is True
        mock_successful_subprocess.assert_called_once()

    def test_check_restic_installed_failure(self, mock_failed_subprocess) -> None:
        """Testa verificacao de instalacao do Restic com falha."""
        client = ResticClient()
        result = client.check_restic_installed()
        assert result is False
        mock_failed_subprocess.assert_called_once()

    def test_check_repository_access_success(self, mock_successful_subprocess) -> None:
        """Testa verificacao de acesso ao repositorio com sucesso."""
        client = ResticClient()
        result = client.check_repository_access()
        assert result is True
        mock_successful_subprocess.assert_called_once()

    def test_check_repository_access_network_error(self, mock_network_error_subprocess) -> None:
        """Testa verificacao de acesso ao repositorio com erro de rede."""
        client = ResticClient()
        with pytest.raises(ResticNetworkError):
            client.check_repository_access()

    def test_check_repository_access_auth_error(self, mock_auth_error_subprocess) -> None:
        """Testa verificacao de acesso ao repositorio com erro de autenticacao."""
        client = ResticClient()
        with pytest.raises(ResticAuthenticationError):
            client.check_repository_access()

    def test_backup_success(self, mock_successful_subprocess) -> None:
        """Testa execucao de backup com sucesso."""
        client = ResticClient()
        result = client.backup(source_dirs=["/test/dir"], tags=["test"])
        assert "abc123" in result
        mock_successful_subprocess.assert_called_once()

    def test_backup_failure(self, mock_failed_subprocess) -> None:
        """Testa execucao de backup com falha."""
        client = ResticClient()
        with pytest.raises(ResticError):
            client.backup(source_dirs=["/test/dir"], tags=["test"])

    def test_apply_retention_policy_success(self, mock_successful_subprocess) -> None:
        """Testa aplicacao de politica de retencao com sucesso."""
        client = ResticClient()
        client.apply_retention_policy(last=5, hourly=24, daily=7, weekly=4, monthly=12, yearly=3)
        mock_successful_subprocess.assert_called_once()

    def test_list_snapshots_success(self, mock_successful_subprocess) -> None:
        """Testa listagem de snapshots com sucesso."""
        mock_successful_subprocess.return_value.stdout = json.dumps([{"id": "abc123", "time": "2023-01-01T12:00:00Z"}])
        client = ResticClient()
        snapshots = client.list_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0]["id"] == "abc123"

    def test_restore_snapshot_success(self, mock_successful_subprocess) -> None:
        """Testa restauracao de snapshot com sucesso."""
        client = ResticClient()
        client.restore_snapshot(snapshot_id="abc123", target_dir="/restore/path")
        mock_successful_subprocess.assert_called_once()

    def test_get_repository_stats_success(self, mock_successful_subprocess) -> None:
        """Testa obtencao de estatisticas do repositorio com sucesso."""
        mock_successful_subprocess.return_value.stdout = json.dumps({"total_size": 1024, "total_file_count": 100})
        client = ResticClient()
        stats = client.get_repository_stats()
        assert stats["total_size"] == 1024
        assert stats["total_file_count"] == 100
