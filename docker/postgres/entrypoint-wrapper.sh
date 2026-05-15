#!/bin/bash
# Wrapper: start postgres, then always sync password from env
set -e

# Start postgres in background
/usr/local/bin/docker-entrypoint.sh postgres "$@" &
PG_PID=$!

# Wait until postgres is ready
until pg_isready -U "${POSTGRES_USER:-postgres}" -q; do
  sleep 1
done

# Always sync password with POSTGRES_PASSWORD env var (survives volume restarts)
psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-postgres}" \
  -c "ALTER USER ${POSTGRES_USER:-postgres} WITH PASSWORD '${POSTGRES_PASSWORD:-postgres}';" \
  > /dev/null 2>&1 && echo "✓ PostgreSQL password synced"

# Wait for postgres process to finish
wait $PG_PID
