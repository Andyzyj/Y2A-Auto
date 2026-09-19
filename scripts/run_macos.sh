#!/bin/bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv. Run scripts/setup_macos.sh first."
  exit 1
fi

export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export HOST="${HOST:-127.0.0.1}"
export PORT="${PORT:-5051}"
export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=utf-8

exec .venv/bin/python app.py
