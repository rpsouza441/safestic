"""Testes para o modulo services.restic."""

import os
import pytest
from unittest.mock import patch

from services.restic import load_restic_env


class TestLoadResticEnv:
    """Testes para a funcao load_restic_env."""

    def test_load_restic_env_aws(self, mock_env) -> None:
        """Testa carregamento de variaveis para AWS."""
        os.environ["STORAGE_PROVIDER"] = "aws"
        os.environ["STORAGE_BUCKET"] = "test-bucket"
        os.environ["RESTIC_PASSWORD"] = "test-password"

        repository, env, provider = load_restic_env()

        assert repository == "s3:s3.amazonaws.com/test-bucket"
        assert env["RESTIC_PASSWORD"] == "test-password"
        assert provider == "aws"

    def test_load_restic_env_azure(self, mock_env) -> None:
        """Testa carregamento de variaveis para Azure."""
        os.environ["STORAGE_PROVIDER"] = "azure"
        os.environ["STORAGE_BUCKET"] = "test-bucket"
        os.environ["RESTIC_PASSWORD"] = "test-password"

        repository, env, provider = load_restic_env()

        assert repository == "azure:test-bucket:restic"
        assert env["RESTIC_PASSWORD"] == "test-password"
        assert provider == "azure"

    def test_load_restic_env_gcp(self, mock_env) -> None:
        """Testa carregamento de variaveis para GCP."""
        os.environ["STORAGE_PROVIDER"] = "gcp"
        os.environ["STORAGE_BUCKET"] = "test-bucket"
        os.environ["RESTIC_PASSWORD"] = "test-password"

        repository, env, provider = load_restic_env()

        assert repository == "gs:test-bucket"
        assert env["RESTIC_PASSWORD"] == "test-password"
        assert provider == "gcp"

    def test_load_restic_env_invalid_provider(self, mock_env) -> None:
        """Testa erro com provedor invalido."""
        os.environ["STORAGE_PROVIDER"] = "invalid"
        os.environ["STORAGE_BUCKET"] = "test-bucket"
        os.environ["RESTIC_PASSWORD"] = "test-password"

        with pytest.raises(ValueError, match="STORAGE_PROVIDER invalido"):
            load_restic_env()

    def test_load_restic_env_missing_password(self, mock_env) -> None:
        """Testa erro com senha ausente."""
        os.environ["STORAGE_PROVIDER"] = "aws"
        os.environ["STORAGE_BUCKET"] = "test-bucket"
        if "RESTIC_PASSWORD" in os.environ:
            del os.environ["RESTIC_PASSWORD"]

        with pytest.raises(ValueError, match="RESTIC_REPOSITORY e RESTIC_PASSWORD"):
            load_restic_env()
