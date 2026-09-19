#!/bin/bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$project_dir"

if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv. Run scripts/setup_macos.sh first."
  exit 1
fi

export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONUNBUFFERED=1
export PYTHONIOENCODING=utf-8
export HF_HOME="${HF_HOME:-$HOME/Library/Application Support/Y2A-Auto/huggingface}"
export WHISPER_MODEL="${WHISPER_MODEL:-mlx-community/whisper-large-v3-turbo}"
export WHISPER_HOST="${WHISPER_HOST:-127.0.0.1}"
export WHISPER_PORT="${WHISPER_PORT:-5052}"

exec .venv/bin/python scripts/local_whisper_server.py
