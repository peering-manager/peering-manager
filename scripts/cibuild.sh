#!/bin/bash

EXIT=0

info() {
  echo "$(date +'%F %T') |"
}

START=$(date +%s)
echo "$(info) starting build checks."

# Define a config file
cp peering_manager/configuration.example.py peering_manager/configuration.py

# Pass the tests suite
coverage run --source=netbox,peering,peeringdb,peering_manager,utils manage.py test
RETURN_CODE=$?
if [[ ${RETURN_CODE} != 0 ]]; then
  echo -e "\n$(info) one or more test errors detected, failing build."
  EXIT=${RETURN_CODE}
fi

END=$(date +%s)
echo "$(info) exiting with code ${EXIT} after $((${END} - ${START})) seconds."

exit $EXIT
