#!/usr/bin/env python3.7

import random
import requests
from requests import Response
import os

from sockpuppet.settings import Config
from sockpuppet.utils import MIN_JSON_INT, MAX_JSON_INT
# Use an environment variable to determine whether or not to send a test request to the live API


def main():
    key = Config.SECRET_KEY
    request_host = Config.HEALTH_CHECK_HOST
    # In development/testing instances, check localhost
    # In production instances, check the Mashape proxy

    request_url = f"{request_host}/api/1/user"
    response_get = requests.get(request_url, {"ids": ["kennethreitz", "gvanrossum"]})

    response_get.raise_for_status()

    response_get_json = response_get.json()  # type: dict

    if "jsonrpc" not in response_get_json or response_get_json["jsonrpc"] != "2.0":
        raise ValueError("GET response is not valid JSON-RPC 2.0")

    if "error" in response_get_json:
        raise ValueError(f"GET response was an error: {response_get_json['error']}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        exit(1)

    exit(0)
