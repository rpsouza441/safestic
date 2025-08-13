"""Gerenciador de contexto compartilhado para scripts CLI.

Este módulo expõe a classe :class:`ResticScript` que centraliza o código
boilerplate necessário para todos os utilitários de linha de comando:
carregamento da configuração do ambiente Restic, preparação de um arquivo
de log com timestamp e fornecimento de métodos auxiliares para logging
e execução de comandos externos.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, TextIO, Union, cast

from .restic import load_restic_env, load_restic_config, ResticConfig
from .logger import create_log_file, log as _log, run_cmd as _run_cmd, setup_logger, redact_secrets


class ResticScript:
    """Gerenciador de contexto usado por scripts CLI.

    Parameters
    ----------
    log_prefix: str
        Identificador usado para o nome do arquivo de log gerado.
    log_dir: str | None
        Diretório onde os arquivos de log serão armazenados. O padrão é a variável
        de ambiente ``LOG_DIR`` ou ``"logs"`` quando não definida.
    credential_source: str
        Fonte para obtenção de credenciais (env, keyring, aws_secrets, azure_keyvault, gcp_secrets, sops).
    log_level: str
        Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """

    def __init__(
        self, 
        log_prefix: str, 
        log_dir: Optional[str] = None,
        credential_source: str = "env",
        log_level: str = "INFO",
    ):
        self.log_prefix = log_prefix
        self.log_dir = log_dir or os.getenv("LOG_DIR", "logs")
        self.credential_source = credential_source
        self.log_level = log_level
        self.repository: str = ""
        self.env: Dict[str, str] = {}
        self.provider: str = ""
        self.log_filename: str = ""
        self.log_file: Optional[TextIO] = None
        self.config: Optional[ResticConfig] = None
        self.logger: Optional[logging.Logger] = None
        self.start_time = None

    def __enter__(self) -> "ResticScript":
        try:
            # Carregar configuração do Restic
            self.repository, self.env, self.provider = load_restic_env(self.credential_source)
            
            # Carregar configuração completa validada
            try:
                self.config = load_restic_config(self.credential_source)
            except Exception as exc:
                print(f"[AVISO] Falha ao carregar configuração completa: {exc}")
                print("[AVISO] Continuando com configuração básica")
        except ValueError as exc:  # pragma: no cover - environment errors
            print(f"[FATAL] {exc}")
            raise SystemExit(1)

        try:
            # Criar diretório de log se não existir
            Path(self.log_dir).mkdir(parents=True, exist_ok=True)
            
            # Criar arquivo de log
            self.log_filename = create_log_file(self.log_prefix, self.log_dir)
            self.log_file = open(self.log_filename, "w", encoding="utf-8")
            
            # Configurar logger estruturado
            self.logger = setup_logger(
                name=f"safestic.{self.log_prefix}",
                log_level=self.log_level,
                log_file=self.log_filename,
            )
            
            # Registrar início da execução
            self.log(
                f"Iniciando {self.log_prefix}", 
                level="INFO",
                extra={
                    "repository": redact_secrets(self.repository),
                    "provider": self.provider,
                    "action": "script_start"
                }
            )
        except Exception as exc:  # pragma: no cover - filesystem errors
            print(f"[FATAL] Falha ao preparar log: {exc}")
            raise SystemExit(1)

        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            # Registrar exceção não tratada
            if self.log_file is not None:
                self.log(
                    f"Erro não tratado: {exc}", 
                    level="ERROR",
                    extra={
                        "exception_type": exc_type.__name__,
                        "exception": str(exc),
                        "action": "script_error"
                    }
                )
        
        # Registrar finalização
        if self.log_file is not None:
            self.log(
                f"Finalizando {self.log_prefix}", 
                level="INFO",
                extra={"action": "script_end"}
            )
            self.log_file.close()

    # Convenience wrappers -------------------------------------------------
    def log(self, message: str, level: str = "INFO", extra: Optional[Dict[str, Any]] = None) -> None:
        """Escreve ``message`` no arquivo de log e stdout com nível e contexto.
        
        Parameters
        ----------
        message : str
            Mensagem a ser registrada
        level : str
            Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        extra : Optional[Dict[str, Any]]
            Informações adicionais para incluir no log
        """
        if self.log_file is None:  # pragma: no cover - defensive programming
            raise RuntimeError("ResticScript não inicializado")
        
        # Adicionar informações padrão ao contexto
        context = {}
        if extra:
            context.update(extra)
        
        # Registrar usando o novo sistema de logging estruturado
        _log(message, self.log_file, level=level, extra=context)

    def run_cmd(
        self,
        cmd: Sequence[str],
        *,
        timeout: Optional[int] = None,
        check: bool = False,
    ) -> int:
        """Executa ``cmd`` encaminhando a saída para o arquivo de log.
        
        Parameters
        ----------
        cmd : Sequence[str]
            Comando a ser executado
        timeout : Optional[int]
            Tempo limite em segundos
        check : bool
            Se deve lançar exceção em caso de erro
            
        Returns
        -------
        int
            Código de retorno do comando
            
        Raises
        ------
        subprocess.CalledProcessError
            Se check=True e o comando retornar código diferente de zero
        subprocess.TimeoutExpired
            Se o comando exceder o timeout
        """
        if self.log_file is None:  # pragma: no cover - defensive programming
            raise RuntimeError("ResticScript não inicializado")
        
        return _run_cmd(
            cmd,
            self.log_file,
            env=self.env,
            timeout=timeout,
            check=check,
        )
