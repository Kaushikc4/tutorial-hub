#!/usr/bin/env bash
# Run the Django server using PostgreSQL. Edit PGPASSWORD below, then:
#   chmod +x run_with_postgres.sh
#   ./run_with_postgres.sh

cd "$(dirname "$0")"
export PGDATABASE=tutorials
export PGUSER=tutorials_user
export PGPASSWORD=password   # <-- set this
export PGHOST=localhost
export PGPORT=5432
exec python manage.py runserver "$@"
