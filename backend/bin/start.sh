#!/bin/sh
# Production entrypoint: schema, reference data, admin user, then the web server.
set -e
python manage.py migrate --noinput
python manage.py seed_reference
python manage.py ensure_superuser
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --access-logfile -
