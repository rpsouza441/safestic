"""Testes para o módulo services.logger."""

import json
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from services.logger import create_log_file, log, run_cmd


class TestCreateLogFile:
    """Testes para a função create_log_file."""

    def test_create_log_file(self) -> None:
        """Testa criação de arquivo de log."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = create_log_file("test", temp_dir)
            assert log_file.startswith(temp_dir)
            assert "test_" in log_file
            assert log_file.endswith(".log")
            assert Path(log_file).parent.exists()

    def test_create_log_file_creates_directory(self) -> None:
        """Testa criação de diretório de log quando não existe."""
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_dir = os.path.join(temp_dir, "logs")
            log_file = create_log_file("test", non_existent_dir)
            assert Path(non_existent_dir).exists()
            assert Path(log_file).parent.exists()


class TestLog:
    """Testes para a função log."""

    def test_log_writes_to_file(self) -> None:
        """Testa escrita de log em arquivo."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            log_path = temp_file.name

        try:
            with open(log_path, "w+") as log_file:
                with patch("builtins.print") as mock_print:
                    log("Test message", log_file)
                    mock_print.assert_called_once()

            with open(log_path, "r") as log_file:
                content = log_file.read()
                assert "Test message" in content
        finally:
            if os.path.exists(log_path):
                os.unlink(log_path)


class TestRunCmd:
    """Testes para a função run_cmd."""

    def test_run_cmd_success(self) -> None:
        """Testa execução de comando com sucesso."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            log_path = temp_file.name

        try:
            with open(log_path, "w+") as log_file:
                with patch("subprocess.run") as mock_run:
                    process_mock = MagicMock()
                    process_mock.returncode = 0
                    process_mock.stdout = "Command output"
                    process_mock.stderr = ""
                    mock_run.return_value = process_mock

                    result = run_cmd(["test", "command"], log_file)
                    assert result == 0

            with open(log_path, "r") as log_file:
                content = log_file.read()
                assert "Command output" in content
        finally:
            if os.path.exists(log_path):
                os.unlink(log_path)

    def test_run_cmd_failure(self) -> None:
        """Testa execução de comando com falha."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
            log_path = temp_file.name

        try:
            with open(log_path, "w+") as log_file:
                with patch("subprocess.run") as mock_run:
                    process_mock = MagicMock()
                    process_mock.returncode = 1
                    process_mock.stdout = ""
                    process_mock.stderr = "Command error"
                    mock_run.return_value = process_mock

                    result = run_cmd(["test", "command"], log_file)
                    assert result == 1

            with open(log_path, "r") as log_file:
                content = log_file.read()
                assert "Command error" in content
                assert "ERRO" in content
        finally:
            if os.path.exists(log_path):
                os.unlink(log_path)