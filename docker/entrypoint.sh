#!/bin/bash

until PGPASSWORD=peering_manager psql -h db -U postgres -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "Postgres is up"
python3 manage.py migrate
python3 manage.py collectstatic --no-input
python3 manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', email='admin@example.com', password='password')"
exec "$@"
