#!/usr/bin/env bash
uv export --no-hashes --no-annotate --no-header --no-dev --no-group docs --format requirements-txt >| requirements.txt
