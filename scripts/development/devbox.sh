#!/bin/bash

# check docker requirements
[[ -x "$(which docker)" ]]         || (echo "docker is required" && exit 1)
[[ -x "$(which docker-compose)" ]] || (echo "docker-compose is required" && exit 2)

# bring the dev stack up (postgresql and adminer)
$(which docker-compose) -f dev-stack.yml up ${@}

exit 0
