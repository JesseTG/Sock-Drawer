#!/usr/bin/env sh

set -e
# Quit in error if any of these commands fails

# # Add system-level dependencies
# apk update
# apk add --no-cache gcc g++ libffi-dev libxml2-dev libxslt-dev yaml-dev zeromq-dev

# # Add Python dependencies
# pip3 install --no-cache-dir --compile --requirement requirements/prod.txt

# # Remove unneeded packages
# apk del gcc g++ libffi-dev libxml2-dev libxslt-dev libc-utils yaml-dev
# # Intentionally not removing zeromq-dev
# # TODO: Look to see what other packages I can remove

# # Remove other cached data
# rm -rf /tmp/*


apt-get update
apt-get dist-upgrade --yes
apt-get install --no-install-recommends --yes gcc libc-dev libffi-dev libxml2-dev libxslt-dev libyaml-dev libzmq5
# Need gcc to compile some Python modules

pip3.7 install --upgrade --no-cache-dir --compile --requirement requirements/prod.txt
# Install the Python modules

apt-get purge --yes -qq binutils gcc manpages libc-dev-bin *-dev
apt-get autoremove --yes
apt-get clean --yes
apt-get autoclean --yes
# Now we don't need gcc

# rm -rf /var/log /var/backups /var/lib/apt /var/lib/dpkg
# mkdir -p /var/log /var/backups /var/lib/apt /var/lib/dpkg
# Clean the caches for good measure