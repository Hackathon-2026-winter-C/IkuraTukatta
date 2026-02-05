#!/usr/bin/env bash
set -e

echo "Run migrations"
python manage.py makemigrations
python manage.py migrate --fake-initial || true

echo "Start server"
exec python manage.py runserver 0.0.0.0:8000
