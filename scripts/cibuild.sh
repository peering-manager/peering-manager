#!/bin/bash

EXIT=0

info() {
  echo "$(date +'%F %T') |"
}

START=$(date +%s)
echo "$(info) starting build checks."

# Check for syntax issues
SYNTAX=$(find peering peering_manager utils -name "*.py" -type f -exec python -m py_compile {} \; 2>&1)
if [[ ! -z ${SYNTAX} ]]; then
  echo -e "${SYNTAX}"
  echo -e "\n$(info) detected one or more syntax errors, failing build."
  EXIT=1
fi

# Check for PEP8 compliance
# Ignore:
#   - E501: line greater than 80 characters in length
pep8 --ignore=E501 peering peering_manager utils
RETURN_CODE=$?
if [[ ${RETURN_CODE} != 0 ]]; then
  echo -e "\n$(info) one or more PEP 8 errors detected, failing build."
  EXIT=${RETURN_CODE}
fi

END=$(date +%s)
echo "$(info) exiting with code ${EXIT} after $((${END} - ${START})) seconds."

exit $EXIT
