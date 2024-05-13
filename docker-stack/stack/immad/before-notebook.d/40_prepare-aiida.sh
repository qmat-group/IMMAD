#!/bin/bash

# This script is executed whenever the docker container is (re)started.

# Debugging.
set -x

# Environment.
export SHELL=/bin/bash

CONFIG=/var/immad/config.yaml

# Check if user requested to set up AiiDA profile (and if it exists already)
if [ -f $CONFIG ] && ! verdi profile show ${AIIDA_PROFILE_NAME} &> /dev/null; then
    NEED_SETUP_PROFILE=true;
else
    NEED_SETUP_PROFILE=false;
fi

# Setup AiiDA profile if needed.
if [[ ${NEED_SETUP_PROFILE} == true ]]; then
    # Create AiiDA profile.
    verdi setup --non-interactive --config $CONFIG
fi

# Show the default profile
verdi profile show || echo "The default profile is not set."

# Make sure that the daemon is not running, otherwise the migration will abort.
verdi daemon stop

# Migration will run for the default profile.
verdi storage migrate --force

# Daemon will start only if the database exists and is migrated to the latest version.
verdi daemon start || echo "AiiDA daemon is not running."

# Suppress warning of RabbitMQ issue
verdi config set warnings.rabbitmq_version False || echo "AiiDA RabbitMQ warning suppression not set"
