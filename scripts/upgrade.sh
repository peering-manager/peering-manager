#!/bin/bash

PYTHON="python3"
PIP="pip3"

# Install and update dependencies
COMMAND="${PIP} install -r requirements.txt --upgrade"
echo "Updating required Python dependencies (${COMMAND})..."
eval ${COMMAND}

# Apply database migrations
COMMAND="${PYTHON} manage.py migrate"
echo "Applying database migrations (${COMMAND})..."
eval ${COMMAND}

# Collect static files
COMMAND="${PYTHON} manage.py collectstatic --no-input --clear"
echo "Collecting static files (${COMMAND})..."
eval ${COMMAND}
