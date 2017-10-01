#!/bin/bash

# Prefer python3 and pip3 but fallback to python and pip if needed
PYTHON="python3"
PIP="pip3"
type ${PYTHON} >/dev/null 2>&1 && type ${PIP} >/dev/null 2>&1 || PYTHON="python" PIP="pip"
while getopts ":23" opt; do
  case $opt in
    2)
      PYTHON="python"
      PIP="pip"
      echo "Forcing python/pip version 2"
      ;;
    3)
      PYTHON="python3"
      PIP="pip3"
      echo "Forcing python/pip version 3"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Delete old Python bytecode
COMMAND="find . -name \"*.pyc\" -delete"
echo "Cleaning up old Python bytecode (${COMMAND})..."
eval ${COMMAND}

# Install and update dependencies
COMMAND="${PIP} install -r requirements.txt --upgrade"
echo "Updating required Python dependencies (${COMMAND})..."
eval ${COMMAND}

# Apply database migrations
COMMAND="${PYTHON} manage.py migrate"
echo "Applying database migrations (${COMMAND})..."
eval ${COMMAND}

# Collect static files
COMMAND="${PYTHON} manage.py collectstatic --no-input"
echo "Collecting static files (${COMMAND})..."
eval ${COMMAND}
