"""Sistema de logging estruturado para o projeto safestic.

Este modulo fornece funcionalidades para logging estruturado em formato JSON,
com suporte a niveis de log, contexto adicional e redacao automatica de segredos.
Tambem inclui funcoes para execucao de comandos com logging detalhado.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import platform
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, TextIO, Union, cast

from pythonjsonlogger import jsonlogger

from .credentials import get_credential

# Padroes para redacao de segredos
SECRET_PATTERNS = [
    # Senhas
    r'(RESTIC_PASSWORD=)[^\s]+',
    r'(password=)[^\s]+',
    r'(senha=)[^\s]+',
    # AWS
    r'(AWS_ACCESS_KEY_ID=)[^\s]+',
    r'(AWS_SECRET_ACCESS_KEY=)[^\s]+',
    # Azure
    r'(AZURE_ACCOUNT_NAME=)[^\s]+',
    r'(AZURE_ACCOUNT_KEY=)[^\s]+',
    # GCP
    r'(GOOGLE_APPLICATION_CREDENTIALS=)[^\s]+',
    # Tokens
    r'(token=)[^\s]+',
    r'(api_key=)[^\s]+',
]


def redact_secrets(text: str) -> str:
    """Redige segredos em texto.
    
    Parameters
    ----------
    text : str
        Texto a ser processado
        
    Returns
    -------
    str
        Texto com segredos redigidos
    """
    for pattern in SECRET_PATTERNS:
        text = re.sub(pattern, r'\1REDACTED', text)
    return text


class SafesticJsonFormatter(jsonlogger.JsonFormatter):
    """Formatador JSON personalizado com campos adicionais e redacao de segredos."""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.hostname = socket.gethostname()
        self.platform = platform.system()
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Adiciona campos padrao e redige segredos."""
        super().add_fields(log_record, record, message_dict)
        
        # Adicionar campos padrao
        log_record["timestamp"] = datetime.datetime.now().isoformat()
        log_record["hostname"] = self.hostname
        log_record["platform"] = self.platform
        
        # Redigir segredos em todos os campos de texto
        for key, value in log_record.items():
            if isinstance(value, str):
                log_record[key] = redact_secrets(value)


def setup_logger(name: str, log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Configura um logger estruturado.
    
    Parameters
    ----------
    name : str
        Nome do logger
    log_level : str
        Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_file : Optional[str]
        Caminho para arquivo de log
        
    Returns
    -------
    logging.Logger
        Logger configurado
    """
    logger = logging.getLogger(name)
    
    # Converter nivel de log para constante do logging
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Remover handlers existentes
    for handler in logger.handlers[:]:  
        logger.removeHandler(handler)
    
    # Criar formatador JSON
    formatter = SafesticJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        rename_fields={'levelname': 'level', 'module': 'source'}
    )
    
    # Adicionar handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Adicionar handler para arquivo se especificado
    if log_file:
        # Garantir que o diretorio exista
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def create_log_file(prefix: str, log_dir: str) -> str:
    """Cria um arquivo de log com timestamp.
    
    Parameters
    ----------
    prefix: str
        Identificador curto usado no nome do arquivo, ex: "backup".
    log_dir: str
        Diretorio onde o arquivo de log sera criado.

    Returns
    -------
    str
        Caminho completo para o arquivo de log. O diretorio e criado
        automaticamente se nao existir.
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now()
    return now.strftime(f"{log_dir}/{prefix}_%Y%m%d_%H%M%S.log")


def log(msg: str, log_file: TextIO, level: str = "INFO", extra: Optional[Dict[str, Any]] = None) -> None:
    """Registra uma mensagem no console e no arquivo de log com timestamp.
    
    Parameters
    ----------
    msg : str
        Mensagem a ser registrada
    log_file : TextIO
        Arquivo de log aberto para escrita
    level : str
        Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    extra : Optional[Dict[str, Any]]
        Informacoes adicionais para incluir no log
    """
    timestamp = datetime.datetime.now().isoformat()
    
    # Redigir segredos na mensagem
    msg = redact_secrets(msg)
    
    # Criar entrada de log estruturada
    log_entry = {
        "timestamp": timestamp,
        "level": level,
        "message": msg,
        "hostname": socket.gethostname(),
    }
    
    # Adicionar informacoes extras se fornecidas
    if extra:
        for key, value in extra.items():
            if isinstance(value, str):
                log_entry[key] = redact_secrets(value)
            else:
                log_entry[key] = value
    
    # Converter para JSON
    log_json = json.dumps(log_entry)
    
    # Imprimir no console
    print(log_json)
    
    # Escrever no arquivo de log
    log_file.write(log_json + "\n")
    log_file.flush()


def run_cmd(
    cmd: Sequence[str],
    log_file: TextIO,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    check: bool = False,
) -> int:
    """Executa um comando e registra saida e erros.
    
    Parameters
    ----------
    cmd : Sequence[str]
        Comando a ser executado como lista de strings
    log_file : TextIO
        Arquivo de log aberto para escrita
    env : Optional[Dict[str, str]]
        Variaveis de ambiente para o comando
    timeout : Optional[int]
        Tempo limite em segundos
    check : bool
        Se deve lancar excecao em caso de erro
        
    Returns
    -------
    int
        Codigo de retorno do comando
        
    Raises
    ------
    subprocess.CalledProcessError
        Se check=True e o comando retornar codigo diferente de zero
    subprocess.TimeoutExpired
        Se o comando exceder o timeout
    """
    # Redigir segredos no comando para logging
    safe_cmd = [redact_secrets(str(arg)) for arg in cmd]
    
    # Registrar inicio da execucao
    start_time = time.time()
    log(
        f"Executando: {' '.join(safe_cmd)}", 
        log_file, 
        level="INFO",
        extra={"command": safe_cmd, "action": "command_start"}
    )
    
    try:
        # Executar comando
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )
        
        # Calcular tempo de execucao
        execution_time = time.time() - start_time
        
        # Redigir segredos na saida
        safe_stdout = redact_secrets(result.stdout)
        safe_stderr = redact_secrets(result.stderr)
        
        # Registrar resultado
        if result.returncode == 0:
            log(
                f"Comando concluido com sucesso em {execution_time:.2f}s", 
                log_file, 
                level="INFO",
                extra={
                    "command": safe_cmd,
                    "returncode": result.returncode,
                    "execution_time": execution_time,
                    "action": "command_success"
                }
            )
            if safe_stdout:
                log(f"Saida: {safe_stdout}", log_file, level="DEBUG", extra={"stdout": safe_stdout})
        else:
            log(
                f"Comando falhou com codigo {result.returncode} em {execution_time:.2f}s", 
                log_file, 
                level="ERROR",
                extra={
                    "command": safe_cmd,
                    "returncode": result.returncode,
                    "execution_time": execution_time,
                    "action": "command_error"
                }
            )
            if safe_stderr:
                log(f"ERRO: {safe_stderr}", log_file, level="ERROR", extra={"stderr": safe_stderr})
            if safe_stdout:
                log(f"Saida: {safe_stdout}", log_file, level="DEBUG", extra={"stdout": safe_stdout})
        
        return result.returncode
    
    except subprocess.TimeoutExpired as e:
        # Calcular tempo de execucao
        execution_time = time.time() - start_time
        
        # Registrar timeout
        log(
            f"Comando excedeu o timeout de {timeout}s apos {execution_time:.2f}s", 
            log_file, 
            level="ERROR",
            extra={
                "command": safe_cmd,
                "timeout": timeout,
                "execution_time": execution_time,
                "action": "command_timeout"
            }
        )
        
        # Re-lancar excecao
        raise
    
    except Exception as e:
        # Calcular tempo de execucao
        execution_time = time.time() - start_time
        
        # Registrar erro
        log(
            f"Erro ao executar comando: {str(e)}", 
            log_file, 
            level="ERROR",
            extra={
                "command": safe_cmd,
                "error": str(e),
                "execution_time": execution_time,
                "action": "command_exception"
            }
        )
        
        # Re-lancar excecao
        raise


