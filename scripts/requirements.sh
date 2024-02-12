#!/usr/bin/env bash
poetry export --without-hashes | awk '{ print $1 }' FS=' ; ' >| requirements.txt
