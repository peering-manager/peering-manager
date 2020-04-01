#!/bin/sh

## Set Timezone
cp "/usr/share/zoneinfo/$TZ" /etc/localtime
>&2 echo $TZ > /etc/timezone

## Attempt connection to Postgres DB
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $DATABASE_HOST -U $POSTGRES_USER -c '\q'; do
    >&2 echo "Waiting for Postgres..."
    sleep 1
done
>&2 echo "Postgres online."

## Create initial user on first run
if [ ! -f "/opt/peering-manager/config/has_run" ]; then
    >&2 echo "Executing First-Run..."
    python3 manage.py migrate
    python3 manage.py collectstatic --no-input
    python3 manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('$DB_ADMIN_USER', email='', password='$DB_ADMIN_PASS')"
    touch /opt/peering-manager/config/has_run
    >&2 echo "First-Run complete."
fi

## Initial pull of PeeringDB information
>&2 echo "Syncing with PeeringDB..."
python3 manage.py peeringdb_sync
>&2 echo "PeeringDB Sync complete."

exec "$@"