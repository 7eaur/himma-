#!/usr/bin/env bash
set -euo pipefail

cd /app/services/api

printf '%s\n' '[himma-release] applying Alembic migrations...'
python -m alembic upgrade head

printf '%s\n' '[himma-release] publishing canonical approved runtime content...'
python seed_all.py

printf '%s\n' '[himma-release] ensuring researcher account seed exists...'
python -m db.seed

printf '%s\n' '[himma-release] pre-deploy preparation complete.'
