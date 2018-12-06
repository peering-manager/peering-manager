#!/bin/bash

PYTHON="python3"

[[ -f db.sqlite3 ]] || (echo "Unable to find SQLite database" && exit 1)
[[ -f manage.py ]]  || (echo "Unable to find Django manage.py" && exit 2)

# dump data as json file
COMMAND="${PYTHON} manage.py dumpdata >| datadump.json"
echo "Dumping data as JSON (${COMMAND})..."
eval ${COMMAND}

# check if the dump is here before continuing
[[ -f datadump.json ]] || (echo "No data dump file found" && exit 3)

# wait for user to change the configuration file
echo "Please upgrade and change your configuration.py file to use PostgreSQL"
read -p "Press enter when you are ready"

# create the database's tablez in postgresql
COMMAND="${PYTHON} manage.py migrate --run-syncdb"
echo "Migrating database (${COMMAND})..."
eval ${COMMAND}

# cleaning django contenttype data
cat << EOF >| contenttype.py
from django.contrib.contenttypes.models import ContentType
ContentType.objects.all().delete()
quit()
EOF
[[ -f contenttype.py ]] || (echo "No database cleanup file found" && exit 4)

COMMAND="${PYTHON} manage.py shell < contenttype.py"
echo "Importing data from JSON (${COMMAND})..."
eval ${COMMAND}
rm contenttype.py

# import json data from file
COMMAND="${PYTHON} manage.py loaddata datadump.json"
echo "Importing data from JSON (${COMMAND})..."
eval ${COMMAND}
rm datadump.json

exit 0
