#!/usr/bin/env sh

# Add system-level dependencies
apk update
apk add --no-cache gcc g++ libffi-dev libxml2-dev libxslt-dev
# TODO: Install libzmq

# Add Python dependencies
pip3 install -v --no-cache-dir --compile --requirement requirements/prod.txt

# Remove unneeded packages
apk del gcc g++ libffi-dev libxml2-dev libxslt-dev libc-utils
# TODO: Look to see what other packages I can remove

# Remove other cached data
rm -rf /var/cache /tmp/*
mkdir -p /var/cache
