#!/usr/bin/env bash
set -e


python manage.py makemigrations web --noinput
python manage.py migrate --noinput
python manage.py shell -c "from web.seed_dummy import seed; seed()"

exec python manage.py runserver 0.0.0.0:8000
