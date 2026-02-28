#!/usr/bin/env bash
set -e


echo "Run migrations"
python manage.py makemigrations web --noinput
python manage.py migrate --noinput
python manage.py shell -c "from web.seed_dummy import seed; seed()"

echo "Start server"
python manage.py collectstatic --noinput
exec python manage.py runserver 0.0.0.0:8000

# 本番用
# exec gunicorn config.wsgi:application \
#   --bind 0.0.0.0:8000 \
#   --workers 3 \
#   --threads 2 \
#   --timeout 60
