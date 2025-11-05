
#!/usr/bin/env python3
"""Interactive credentials helper for Safestic."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from getpass import getpass
from pathlib import Path
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT_DIR / "config"
ENV_EXAMPLE = CONFIG_DIR / ".env.example"
ENV_FILE = CONFIG_DIR / ".env"
DEFAULT_PASSWORD_FILE = CONFIG_DIR / "restic_password.txt"

ENV_KEYS: List[str] = [
    "SECRET_MODE",
    "RESTIC_REPOSITORY",
    "RESTIC_PASSWORD_FILE",
    "RESTIC_SECRET_BACKEND",
    "AWS_REGION",
    "AWS_PROFILE",
    "AWS_SECRET_ID",
    "AZURE_KEYVAULT_NAME",
    "AZURE_SECRET_NAME",
    "GCP_PROJECT",
    "GCP_SECRET_NAME",
    "GCP_SECRET_VERSION",
    "INCLUDE_DIRS",
    "EXCLUDE_FILE",
    "EXCLUDE_PATTERNS",
    "TAG",
    "RESTIC_CACHE_DIR",
    "KEEP_DAILY",
    "KEEP_WEEKLY",
    "KEEP_MONTHLY",
    "KEEP_YEARLY",
    "SCHEDULE_CRON",
    "SCHEDULE_WIN_TIME",
    "SCHEDULE_WIN_DAYS",
]


def parse_env(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def render_env(template_lines: List[str], values: Dict[str, str]) -> str:
    output: List[str] = []
    seen: set[str] = set()
    for raw_line in template_lines:
        stripped = raw_line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in values:
                output.append(f"{key}={values[key]}\n")
                seen.add(key)
                continue
        if raw_line.endswith("\n"):
            output.append(raw_line)
        else:
            output.append(raw_line + "\n")
    for key in ENV_KEYS:
        if key in values and key not in seen:
            output.append(f"{key}={values[key]}\n")
    return "".join(output)

def prompt(message: str, default: str | None = None, required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            value = input(f"{message}{suffix}: ").strip()
        except EOFError:
            print()
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nInterrompido pelo usuario.")
            sys.exit(1)
        if not value and default is not None:
            return default
        if not value and required:
            print("Valor obrigatorio. Tente novamente.")
            continue
        return value


def prompt_secret(message: str) -> str:
    try:
        value = getpass(message + ": ")
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario.")
        sys.exit(1)
    if not value:
        print("Senha nao pode ser vazia.")
        return prompt_secret(message)
    return value


def ensure_cli(binary: str) -> None:
    if shutil.which(binary) is None:
        print(f"Erro: CLI '{binary}' nao encontrada no PATH.")
        sys.exit(1)


def write_password_file(path_value: str, password: str) -> str:
    candidate = Path(path_value).expanduser()
    if not candidate.is_absolute():
        candidate = ROOT_DIR / candidate
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(password + "\n")
    try:
        os.chmod(candidate, 0o600)
    except PermissionError:
        pass
    try:
        relative = candidate.relative_to(ROOT_DIR)
        return str(relative)
    except ValueError:
        return str(candidate)


def store_aws_secret(secret_id: str, password: str, region: str, profile: str) -> None:
    ensure_cli("aws")
    env = os.environ.copy()
    if region:
        env["AWS_REGION"] = region
    if profile:
        env["AWS_PROFILE"] = profile
    describe = subprocess.run(
        ["aws", "secretsmanager", "describe-secret", "--secret-id", secret_id],
        env=env,
        capture_output=True,
        text=True,
    )
    if describe.returncode == 0:
        command = [
            "aws",
            "secretsmanager",
            "put-secret-value",
            "--secret-id",
            secret_id,
            "--secret-string",
            password,
        ]
    else:
        command = [
            "aws",
            "secretsmanager",
            "create-secret",
            "--name",
            secret_id,
            "--secret-string",
            password,
        ]
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("Falha ao gravar segredo no AWS Secrets Manager.")


def store_azure_secret(vault: str, name: str, password: str) -> None:
    ensure_cli("az")
    command = [
        "az",
        "keyvault",
        "secret",
        "set",
        "--vault-name",
        vault,
        "--name",
        name,
        "--value",
        password,
        "--only-show-errors",
        "--output",
        "none",
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("Falha ao gravar segredo no Azure Key Vault.")


def store_gcp_secret(project: str, name: str, password: str) -> None:
    ensure_cli("gcloud")
    describe = subprocess.run(
        ["gcloud", "secrets", "describe", name, "--project", project],
        capture_output=True,
        text=True,
    )
    if describe.returncode != 0:
        create = subprocess.run(
            [
                "gcloud",
                "secrets",
                "create",
                name,
                "--project",
                project,
                "--replication-policy",
                "automatic",
            ],
            capture_output=True,
            text=True,
        )
        if create.returncode != 0:
            raise RuntimeError("Falha ao criar segredo no GCP Secret Manager.")
    add = subprocess.run(
        [
            "gcloud",
            "secrets",
            "versions",
            "add",
            name,
            "--project",
            project,
            "--data-file=-",
        ],
        input=password,
        text=True,
        capture_output=True,
    )
    if add.returncode != 0:
        raise RuntimeError("Falha ao atualizar segredo no GCP Secret Manager.")


def main() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not ENV_EXAMPLE.exists():
        print("Arquivo config/.env.example nao encontrado.")
        sys.exit(1)
    if not ENV_FILE.exists():
        ENV_FILE.write_text(ENV_EXAMPLE.read_text())

    example_lines = ENV_EXAMPLE.read_text().splitlines(keepends=True)
    values = parse_env(ENV_EXAMPLE)
    values.update(parse_env(ENV_FILE))

    print("=== Configurador de credenciais Safestic ===")

    secret_mode = prompt("Modo de segredo (file/manager)", values.get("SECRET_MODE", "file"), required=True)
    while secret_mode not in {"file", "manager"}:
        print("Valor invalido. Use 'file' ou 'manager'.")
        secret_mode = prompt("Modo de segredo (file/manager)", values.get("SECRET_MODE", "file"), required=True)
    values["SECRET_MODE"] = secret_mode

    repo_default = values.get("RESTIC_REPOSITORY", "")
    values["RESTIC_REPOSITORY"] = prompt("RESTIC_REPOSITORY", repo_default, required=True)

    if secret_mode == "file":
        password_path = prompt(
            "Caminho do RESTIC_PASSWORD_FILE",
            values.get("RESTIC_PASSWORD_FILE", str(DEFAULT_PASSWORD_FILE.relative_to(ROOT_DIR))),
            required=True,
        )
        password = prompt_secret("Informe a senha do repositorio")
        stored_path = write_password_file(password_path, password)
        values["RESTIC_PASSWORD_FILE"] = stored_path
        print(f"Senha armazenada em {stored_path} (permissoes 600).")
    else:
        backend = prompt("Backend de segredo (aws/azure/gcp)", values.get("RESTIC_SECRET_BACKEND", "aws"), required=True)
        while backend not in {"aws", "azure", "gcp"}:
            print("Backend invalido. Escolha entre aws, azure ou gcp.")
            backend = prompt("Backend de segredo (aws/azure/gcp)", values.get("RESTIC_SECRET_BACKEND", "aws"), required=True)
        values["RESTIC_SECRET_BACKEND"] = backend
        password = prompt_secret("Informe a senha do repositorio")
        try:
            if backend == "aws":
                region = prompt("AWS_REGION", values.get("AWS_REGION", "us-east-1"), required=True)
                profile = prompt("AWS_PROFILE (opcional)", values.get("AWS_PROFILE", ""))
                secret_id = prompt("AWS_SECRET_ID", values.get("AWS_SECRET_ID", "safestic/restic-password"), required=True)
                store_aws_secret(secret_id, password, region, profile)
                values.update({
                    "AWS_REGION": region,
                    "AWS_PROFILE": profile,
                    "AWS_SECRET_ID": secret_id,
                })
            elif backend == "azure":
                vault = prompt("AZURE_KEYVAULT_NAME", values.get("AZURE_KEYVAULT_NAME", ""), required=True)
                name = prompt("AZURE_SECRET_NAME", values.get("AZURE_SECRET_NAME", ""), required=True)
                store_azure_secret(vault, name, password)
                values.update({
                    "AZURE_KEYVAULT_NAME": vault,
                    "AZURE_SECRET_NAME": name,
                })
            else:
                project = prompt("GCP_PROJECT", values.get("GCP_PROJECT", ""), required=True)
                secret_name = prompt("GCP_SECRET_NAME", values.get("GCP_SECRET_NAME", ""), required=True)
                version = prompt("GCP_SECRET_VERSION", values.get("GCP_SECRET_VERSION", "latest"), required=True)
                store_gcp_secret(project, secret_name, password)
                values.update({
                    "GCP_PROJECT": project,
                    "GCP_SECRET_NAME": secret_name,
                    "GCP_SECRET_VERSION": version or "latest",
                })
        except RuntimeError as error:
            print(str(error))
            sys.exit(1)

    values["INCLUDE_DIRS"] = prompt("INCLUDE_DIRS (separar por espaco)", values.get("INCLUDE_DIRS", "/etc /home"), required=True)
    values["EXCLUDE_FILE"] = prompt("EXCLUDE_FILE", values.get("EXCLUDE_FILE", ""))
    values["EXCLUDE_PATTERNS"] = prompt("EXCLUDE_PATTERNS", values.get("EXCLUDE_PATTERNS", ""))
    values["TAG"] = prompt("TAG", values.get("TAG", "safestic"))
    values["RESTIC_CACHE_DIR"] = prompt("RESTIC_CACHE_DIR", values.get("RESTIC_CACHE_DIR", ".cache/restic"))

    values["KEEP_DAILY"] = prompt("KEEP_DAILY", values.get("KEEP_DAILY", "7"))
    values["KEEP_WEEKLY"] = prompt("KEEP_WEEKLY", values.get("KEEP_WEEKLY", "4"))
    values["KEEP_MONTHLY"] = prompt("KEEP_MONTHLY", values.get("KEEP_MONTHLY", "12"))
    values["KEEP_YEARLY"] = prompt("KEEP_YEARLY", values.get("KEEP_YEARLY", "3"))

    values["SCHEDULE_CRON"] = prompt("SCHEDULE_CRON", values.get("SCHEDULE_CRON", "0 2 * * *"))
    values["SCHEDULE_WIN_TIME"] = prompt("SCHEDULE_WIN_TIME", values.get("SCHEDULE_WIN_TIME", "02:00"))
    values["SCHEDULE_WIN_DAYS"] = prompt("SCHEDULE_WIN_DAYS", values.get("SCHEDULE_WIN_DAYS", "MON,TUE,WED,THU,FRI"))

    rendered = render_env(example_lines, values)
    ENV_FILE.write_text(rendered)
    print(f"Arquivo de configuracao atualizado em {ENV_FILE.relative_to(ROOT_DIR)}.")
    if secret_mode == "file":
        print("Modo file configurado. RESTIC_PASSWORD_FILE mantem a senha local com permissao 600.")
    else:
        backend = values["RESTIC_SECRET_BACKEND"]
        print(f"Modo manager configurado usando backend {backend}.")


if __name__ == "__main__":
    main()
