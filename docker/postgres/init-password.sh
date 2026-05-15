#!/bin/bash
# Ensure postgres password matches POSTGRES_PASSWORD env var on every startup
set -e

# This script runs after PostgreSQL starts (via pg_isready)
# It resets the password to ensure consistency with docker-compose config
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    ALTER USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';
EOSQL

echo "✓ PostgreSQL password synced with POSTGRES_PASSWORD env var"
