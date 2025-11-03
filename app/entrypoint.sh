#!/bin/bash
set -e

# Replace environment variables in newrelic.ini
envsubst < /app/newrelic.ini.template > /app/newrelic.ini

# Start application with New Relic
exec newrelic-admin run-program uvicorn main:app --host 0.0.0.0 --port 3000
