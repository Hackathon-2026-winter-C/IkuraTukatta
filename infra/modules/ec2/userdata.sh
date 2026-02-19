#!/bin/bash
set -euxo pipefail

APP_DIR=/app
mkdir -p "$APP_DIR/nginx"
cd "$APP_DIR"

systemctl enable --now docker

aws s3 cp "s3://${aws_s3_bucket}/deploy/docker-compose.prod.yml" "$APP_DIR/docker-compose.prod.yml"
aws s3 cp "s3://${aws_s3_bucket}/deploy/default.conf" "$APP_DIR/nginx/default.conf"

ECR_REGISTRY="$(echo "${ecr_repository_url}" | cut -d'/' -f1)"
aws ecr get-login-password --region "${region}" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

cat > "$APP_DIR/.env" <<EOF
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

chmod 600 "$APP_DIR/.env"
docker compose --env-file "$APP_DIR/.env" -f "$APP_DIR/docker-compose.prod.yml" up -d
