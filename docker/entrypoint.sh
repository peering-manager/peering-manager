#!/bin/sh

## Attempt connection to Postgres DB
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $DATABASE_HOST -U $POSTGRES_USER -c '\q'; do
  >&2 echo "Waiting for Postgres..."
  sleep 1
done
>&2 echo "Postgres online."

## Create initial user on first run
if [ ! -f "/opt/peering-manager/has_run" ]; then
    python3 manage.py migrate
    python3 manage.py collectstatic --no-input
    python3 manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', email='admin@example.com', password='password')"
    touch /opt/peering-manager/has_run
fi

exec "$@"