#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import requests


def setup_cli():
    parser = argparse.ArgumentParser(
        description="Import JSON data using Peering Manager's API"
    )
    parser.add_argument("url", help="URL of the API (endpoint included)")
    parser.add_argument("token", help="token to be used for API authentication")
    parser.add_argument("json_file", help="file containing JSON data")

    return parser.parse_args()


def read_json(filename):
    with Path(filename).open() as json_file:
        return json.load(json_file)


def call_api(url, token, data):
    headers = {"accept": "application/json", "authorization": f"Token {token}"}
    r = requests.post(url, headers=headers, json=data)
    r.raise_for_status()


if __name__ == "__main__":
    args = setup_cli()
    data = read_json(args.json_file)
    call_api(args.url, args.token, data)
