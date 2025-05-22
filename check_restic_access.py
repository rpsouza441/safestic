import os
import subprocess
import sys
from dotenv import load_dotenv

# === 1. Carregar variáveis do .env ===
load_dotenv()

# === 2. Montar RESTIC_REPOSITORY dinamicamente com base no provedor ===
PROVIDER = os.getenv("STORAGE_PROVIDER", "").lower()
BUCKET = os.getenv("STORAGE_BUCKET", "")
RESTIC_PASSWORD = os.getenv("RESTIC_PASSWORD")

if PROVIDER == "aws":
    RESTIC_REPOSITORY = f"s3:s3.amazonaws.com/{BUCKET}"
elif PROVIDER == "azure":
    RESTIC_REPOSITORY = f"azure:{BUCKET}"
elif PROVIDER == "gcp":
    RESTIC_REPOSITORY = f"gs:{BUCKET}"
else:
    print("[FATAL] STORAGE_PROVIDER inválido. Use 'aws', 'azure' ou 'gcp'")
    sys.exit(1)

# === 3. Verificar variáveis obrigatórias ===
print("🔍 Verificando variáveis essenciais do .env")
def print_status(name, result):
    print(f"{name.ljust(30)}: {'OK' if result else '❌ FALHA'}")

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
    print("\n[FATAL] Variáveis obrigatórias estão ausentes. Abortando.")
    sys.exit(1)

# === 4. Verificar se Restic está no PATH ===
print("\nVerificando se 'restic' está disponível no PATH...")
try:
    subprocess.run(["restic", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Restic está instalado e acessível.")
except FileNotFoundError:
    print("Restic não encontrado no PATH.")
    sys.exit(1)
except subprocess.CalledProcessError as e:
    print("Restic executou com erro:", e)
    sys.exit(1)

# === 5. Testar acesso ao repositório ===
print("\nTestando acesso ao repositório...")
try:
    subprocess.run(
        ["restic", "-r", RESTIC_REPOSITORY, "snapshots"],
        env=os.environ.copy(),
        check=True
    )
    print("Acesso ao repositório bem-sucedido.")
except subprocess.CalledProcessError as e:
    print("Não foi possível acessar o repositório.")
    print("Tentando inicializar...")

    try:
        subprocess.run(
            ["restic", "-r", RESTIC_REPOSITORY, "init"],
            env=os.environ.copy(),
            check=True
        )
        print("Repositório foi inicializado com sucesso!")
    except subprocess.CalledProcessError:
        print("Falha ao inicializar o repositório.")
        sys.exit(1)
