#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
ENV_FILE="$PROJECT_DIR/config/.env"

if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$ENV_FILE"
    set +a
fi

backend=${1:-}
if [ -z "$backend" ]; then
    echo "Uso: $0 <aws|azure|gcp>" >&2
    exit 1
fi

case "$backend" in
    aws)
        command -v aws >/dev/null 2>&1 || { echo "CLI aws faltando." >&2; exit 1; }
        : "${AWS_SECRET_ID:?AWS_SECRET_ID nao definido}"
        region_opt=""
        [ -n "${AWS_REGION:-}" ] && region_opt="--region ${AWS_REGION}"
        profile_opt=""
        if [ -n "${AWS_PROFILE:-}" ]; then
            export AWS_PROFILE
        fi
        # shellcheck disable=SC2086
        aws secretsmanager get-secret-value --secret-id "$AWS_SECRET_ID" $region_opt --query SecretString --output text
        ;;
    azure)
        command -v az >/dev/null 2>&1 || { echo "CLI az faltando." >&2; exit 1; }
        : "${AZURE_KEYVAULT_NAME:?AZURE_KEYVAULT_NAME nao definido}"
        : "${AZURE_SECRET_NAME:?AZURE_SECRET_NAME nao definido}"
        az keyvault secret show --vault-name "$AZURE_KEYVAULT_NAME" --name "$AZURE_SECRET_NAME" --query value -o tsv
        ;;
    gcp)
        command -v gcloud >/dev/null 2>&1 || { echo "CLI gcloud faltando." >&2; exit 1; }
        : "${GCP_PROJECT:?GCP_PROJECT nao definido}"
        : "${GCP_SECRET_NAME:?GCP_SECRET_NAME nao definido}"
        version=${GCP_SECRET_VERSION:-latest}
        gcloud secrets versions access "$version" --secret "$GCP_SECRET_NAME" --project "$GCP_PROJECT"
        ;;
    *)
        echo "Backend desconhecido: $backend" >&2
        exit 1
        ;;
esac
