#!/bin/bash

echo "▶️  $0 $*"

set -e

if [ "${1}" == "--help" ] || [ "${1}" == "-h" ]; then
  echo ""
  echo "Usage: ${0}"
  echo ""
  echo "You can use the following ENV variables to customize the behavior:"
  echo "  DRY_RUN     Prints all commands instead of running them."
  echo "              Default: undefined"
  echo ""
  exit 0
fi

cd $(dirname $(dirname $(realpath $0)))
VIRTUALENV="$(pwd -P)/venv"

# Enabling dry-run mode
if [ -z "${DRY_RUN}" ]; then
  DRY=""
else
  echo "⚠️  DRY_RUN MODE ON ⚠️"
  DRY="echo"
fi

# Check for a venv and remove it if it exists
if [ -d "$VIRTUALENV" ]; then
  echo "📦 Removing old virtual environment..."
  $DRY rm -rf $VIRTUALENV
else
  WARN_MISSING_VENV=1
fi

# Create a new venv
echo "📦 Creating a new virtual environment at ${VIRTUALENV}"
$DRY /usr/bin/python3 -m venv $VIRTUALENV || {
  echo "--------------------------------------------------------------------"
  echo "🚨 Failed to create the virtual environment."
  echo "Check that you have the required system packages installed and the"
  echo "following path is writable:"
  echo "  ${VIRTUALENV}"
  echo "--------------------------------------------------------------------"
  exit 1
}

# Activate the virtual environment
echo "🐍 Activating new virtual environment"
$DRY source "${VIRTUALENV}/bin/activate"

# Install necessary system packages
echo "🐍 Installing Python system packages"
$DRY pip install -U pip wheel || exit 1

# Install required Python packages
echo "🐍 Installing dependencies"
$DRY pip install -r requirements.txt || exit 1

# Apply any database migrations
echo "🔄 Applying database migrations"
$DRY python manage.py migrate || exit 1

# Collect static files
echo "🔄 Collecting static files"
$DRY python manage.py collectstatic --no-input || exit 1

# Delete any stale content types
echo "🔄 Removing stale content types"
$DRY python manage.py remove_stale_contenttypes --no-input || exit 1

# Delete any expired user sessions
echo "🔄 Removing expired user sessions"
$DRY python manage.py clearsessions || exit 1

# Clear all cached data
echo "🔄 Clearing cache data"
$DRY python manage.py invalidate all || exit 1

if [ -n "${WARN_MISSING_VENV}" ]; then
  echo "--------------------------------------------------------------------"
  echo "⚠️   No existing virtual environment was detected. A new one has"
  echo "been created. Update your systemd service files to reflect the new"
  echo "Python and gunicorn executables."
  echo ""
  echo "peering-manager.service ExecStart:"
  echo "  ${VIRTUALENV}/bin/gunicorn"
  echo ""
  echo "peering-manager-rqworker.service ExecStart:"
  echo "  ${VIRTUALENV}/bin/python"
  echo ""
  echo "After modifying these files, reload the systemctl daemon:"
  echo "  > systemctl daemon-reload"
  echo "--------------------------------------------------------------------"
fi

echo "✅ Upgrade complete! Don't forget to restart the Peering Manager services:"
echo "  > sudo systemctl restart peering-manager peering-manager-rqworker"
