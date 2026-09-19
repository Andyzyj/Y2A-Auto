#!/bin/bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
python_bin="${PYTHON_BIN:-/opt/homebrew/bin/python3.11}"

if [[ ! -x "$python_bin" ]]; then
  echo "Python 3.11 not found at $python_bin"
  echo "Install it with: brew install python@3.11"
  exit 1
fi

for tool in ffmpeg ffprobe deno; do
  if [[ ! -x "/opt/homebrew/bin/$tool" ]]; then
    echo "$tool not found in /opt/homebrew/bin"
    echo "Install the missing tools with: brew install ffmpeg deno"
    exit 1
  fi
done

cd "$project_dir"
if [[ ! -d .venv ]]; then
  "$python_bin" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-macos.txt

echo "Y2A-Auto macOS environment is ready."
