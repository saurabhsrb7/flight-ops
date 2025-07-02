#!/bin/sh
set -e

python init_db.py
exec uvicorn app:app --host 0.0.0.0 --port 8001