#!/usr/bin/env bash
set -e
export PYTHONUNBUFFERED=1
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

