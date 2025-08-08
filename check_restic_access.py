import os
import sys

from services.restic import load_restic_env
from services.logger import create_log_file, log, run_cmd

# === 1. Carregar configurações do Restic ===
try:
    RESTIC_REPOSITORY, env, PROVIDER = load_restic_env()
except ValueError as e:
    print(f"[FATAL] {e}")
    sys.exit(1)

RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")

# === 3. Verificar variáveis obrigatórias ===
LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_FILE = create_log_file("check_restic_access", LOG_DIR)

print("🔍 Verificando variáveis essenciais do .env")
with open(LOG_FILE, "w", encoding="utf-8") as log_file:
    def print_status(name, result):
        line = f"{name.ljust(30)}: {'OK' if result else '❌ FALHA'}"
        print(line)
        log(line, log_file)

    print_status("RESTIC_REPOSITORY", bool(RESTIC_REPOSITORY))
    print_status("RESTIC_PASSWORD", bool(RESTIC_PASSWORD))

    if PROVIDER == "aws":
        print_status("AWS_ACCESS_KEY_ID", bool(os.getenv("AWS_ACCESS_KEY_ID")))
        print_status("AWS_SECRET_ACCESS_KEY", bool(os.getenv("AWS_SECRET_ACCESS_KEY")))
    elif PROVIDER == "azure":
        print_status("AZURE_ACCOUNT_NAME", bool(os.getenv("AZURE_ACCOUNT_NAME")))
        print_status("AZURE_ACCOUNT_KEY", bool(os.getenv("AZURE_ACCOUNT_KEY")))
    elif PROVIDER == "gcp":
        print_status("GOOGLE_PROJECT_ID", bool(os.getenv("GOOGLE_PROJECT_ID")))
        print_status("GOOGLE_APPLICATION_CREDENTIALS", bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")))

    if not RESTIC_REPOSITORY or not RESTIC_PASSWORD:
        log("[FATAL] Variáveis obrigatórias estão ausentes. Abortando.", log_file)
        print("\n[FATAL] Variáveis obrigatórias estão ausentes. Abortando.")
        sys.exit(1)

    # === 4. Verificar se Restic está no PATH ===
    log("\nVerificando se 'restic' está disponível no PATH...", log_file)
    success, _ = run_cmd(
        ["restic", "version"],
        log_file,
        error_msg="Restic não encontrado ou com erro",
    )
    if not success:
        sys.exit(1)
    log("Restic está instalado e acessível.", log_file)
    print("Restic está instalado e acessível.")

    # === 5. Testar acesso ao repositório ===
    log("\nTestando acesso ao repositório...", log_file)
    success, _ = run_cmd(
        ["restic", "-r", RESTIC_REPOSITORY, "snapshots"],
        log_file,
        env=env,
        error_msg="Não foi possível acessar o repositório",
    )
    if success:
        log("Acesso ao repositório bem-sucedido.", log_file)
        print("Acesso ao repositório bem-sucedido.")
    else:
        print("Não foi possível acessar o repositório.")
        log("Tentando inicializar...", log_file)

        success, _ = run_cmd(
            ["restic", "-r", RESTIC_REPOSITORY, "init"],
            log_file,
            env=env,
            error_msg="Falha ao inicializar o repositório",
            success_msg="Repositório foi inicializado com sucesso!",
        )
        if not success:
            sys.exit(1)
