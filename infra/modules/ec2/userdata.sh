#!/bin/bash
set -euxo pipefail

APP_DIR=/app
COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"
ENV_FILE="$APP_DIR/.env"
NGINX_DIR="$APP_DIR/nginx"
ECR_REGISTRY="$(echo "${ecr_repository_url}" | cut -d'/' -f1)"
IMAGE_REF="${ecr_repository_url}:${image_tag}"

retry() {
  local max_retry="$1"
  shift
  local try=1

  until "$@"; do
    if [ "$try" -ge "$max_retry" ]; then
      echo "Command failed after $max_retry attempts: $*" >&2
      return 1
    fi

    sleep $((try * 5))
    try=$((try + 1))
  done
}

# Prefer instance profile credentials for bootstrap commands.
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN || true

mkdir -p "$NGINX_DIR"
cd "$APP_DIR"

systemctl enable --now docker
retry 12 systemctl is-active --quiet docker

retry 6 aws s3 cp "s3://${aws_s3_bucket}/deploy/docker-compose.prod.yml" "$COMPOSE_FILE"
retry 6 aws s3 cp "s3://${aws_s3_bucket}/deploy/default.conf" "$NGINX_DIR/default.conf"

ecr_login() {
  aws ecr get-login-password --region "${region}" \
    | docker login --username AWS --password-stdin "$ECR_REGISTRY"
}
retry 6 ecr_login
retry 6 docker pull "$IMAGE_REF"

cat > "$ENV_FILE" <<EOF
DB_HOST=${db_host}
DB_PORT=3306
DB_NAME=${db_name}
DB_USER=${db_user}
DB_PASSWORD=${db_password}
ALLOWED_HOSTS=${alb_dns_name},localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://${alb_dns_name}
AWS_S3_REGION_NAME=${region}
AWS_STORAGE_BUCKET_NAME=${aws_s3_bucket}
AWS_ACCESS_KEY_ID=${aws_access_key}
AWS_SECRET_ACCESS_KEY=${aws_secret_key}
ECR_REPOSITORY_URL=${ecr_repository_url}
IMAGE_TAG=${image_tag}
EOF

chmod 600 "$ENV_FILE"
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d
