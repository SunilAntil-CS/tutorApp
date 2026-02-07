#!/usr/bin/env bash
# Install greenlet (if needed) and run seed_content against DB from .env (e.g. remote).
set -e
cd "$(dirname "$0")/.."
if [ -d .venv ]; then
  .venv/bin/pip install -q greenlet
  .venv/bin/python -m scripts.seed_content
else
  echo "No .venv found. Create one with: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi
