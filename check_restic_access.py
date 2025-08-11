import os
import sys

from services.script import ResticScript


def main() -> None:
    with ResticScript("check_restic_access") as ctx:
        restic_password = os.getenv("RESTIC_PASSWORD")

        print("🔍 Verificando variáveis essenciais do .env")

        def print_status(name: str, result: bool) -> None:
            line = f"{name.ljust(30)}: {'OK' if result else '❌ FALHA'}"
            print(line)
            ctx.log(line)

        print_status("RESTIC_REPOSITORY", bool(ctx.repository))
        print_status("RESTIC_PASSWORD", bool(restic_password))

        if ctx.provider == "aws":
            print_status("AWS_ACCESS_KEY_ID", bool(os.getenv("AWS_ACCESS_KEY_ID")))
            print_status(
                "AWS_SECRET_ACCESS_KEY",
                bool(os.getenv("AWS_SECRET_ACCESS_KEY")),
            )
        elif ctx.provider == "azure":
            print_status("AZURE_ACCOUNT_NAME", bool(os.getenv("AZURE_ACCOUNT_NAME")))
            print_status("AZURE_ACCOUNT_KEY", bool(os.getenv("AZURE_ACCOUNT_KEY")))
        elif ctx.provider == "gcp":
            print_status("GOOGLE_PROJECT_ID", bool(os.getenv("GOOGLE_PROJECT_ID")))
            print_status(
                "GOOGLE_APPLICATION_CREDENTIALS",
                bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS")),
            )

        if not ctx.repository or not restic_password:
            ctx.log("[FATAL] Variáveis obrigatórias estão ausentes. Abortando.")
            print("\n[FATAL] Variáveis obrigatórias estão ausentes. Abortando.")
            sys.exit(1)

        ctx.log("\nVerificando se 'restic' está disponível no PATH...")
        success, _ = ctx.run_cmd(
            ["restic", "version"],
            error_msg="Restic não encontrado ou com erro",
        )
        if not success:
            sys.exit(1)
        ctx.log("Restic está instalado e acessível.")
        print("Restic está instalado e acessível.")

        ctx.log("\nTestando acesso ao repositório...")
        success, _ = ctx.run_cmd(
            ["restic", "-r", ctx.repository, "snapshots"],
            error_msg="Não foi possível acessar o repositório",
        )
        if success:
            ctx.log("Acesso ao repositório bem-sucedido.")
            print("Acesso ao repositório bem-sucedido.")
        else:
            print("Não foi possível acessar o repositório.")
            ctx.log("Tentando inicializar...")
            success, _ = ctx.run_cmd(
                ["restic", "-r", ctx.repository, "init"],
                error_msg="Falha ao inicializar o repositório",
                success_msg="Repositório foi inicializado com sucesso!",
            )
            if not success:
                sys.exit(1)


if __name__ == "__main__":
    main()
