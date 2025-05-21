import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

RESTIC_REPOSITORY = os.getenv("RESTIC_REPOSITORY")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

def print_status(name, result):
    print(f"{name.ljust(30)}: {'✅ OK' if result else '❌ FALHA'}")

# === Verificações básicas ===
print("🔍 Verificando variáveis essenciais do .env")
print_status("RESTIC_REPOSITORY", bool(RESTIC_REPOSITORY))
print_status("RESTIC_PASSWORD", bool(RESTIC_PASSWORD))
print_status("AWS_ACCESS_KEY_ID", bool(AWS_ACCESS_KEY_ID))
print_status("AWS_SECRET_ACCESS_KEY", bool(AWS_SECRET_ACCESS_KEY))

if not all([RESTIC_REPOSITORY, RESTIC_PASSWORD, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]):
    print("\n[FATAL] Algumas variáveis obrigatórias estão ausentes no .env. Abortando.")
    sys.exit(1)

# === Verificar se Restic está no PATH ===
print("\n🔍 Verificando se 'restic' está disponível no PATH...")
try:
    subprocess.run(["restic", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("✅ Restic está instalado e acessível.")
except FileNotFoundError:
    print("❌ Restic não encontrado no PATH.")
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print("❌ Restic executou com erro:", e)
    sys.exit(1)

# === Testar acesso ao repositório ===
print("\n🔍 Testando acesso ao repositório...")
try:
    subprocess.run(
        ["restic", "-r", RESTIC_REPOSITORY, "snapshots"],
        env=os.environ.copy(),
        check=True
    )
    print("✅ Acesso ao repositório bem-sucedido.")
except subprocess.CalledProcessError as e:
    print("⚠️ Não foi possível acessar o repositório.")
    print("ℹ️ Tentando inicializar...")

    # Tentativa de init
    try:
        subprocess.run(
            ["restic", "-r", RESTIC_REPOSITORY, "init"],
            env=os.environ.copy(),
            check=True
        )
        print("✅ Repositório foi inicializado com sucesso!")
    except subprocess.CalledProcessError:
        print("❌ Falha ao inicializar o repositório.")
        sys.exit(1)
