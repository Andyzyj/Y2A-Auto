#!/bin/bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
python_bin="${PYTHON_BIN:-/opt/homebrew/bin/python3.11}"
ffmpeg_bin="${FFMPEG_BIN:-/opt/homebrew/opt/ffmpeg@7/bin/ffmpeg}"
ffprobe_bin="${FFPROBE_BIN:-$(dirname "$ffmpeg_bin")/ffprobe}"
deno_bin="${DENO_BIN:-/opt/homebrew/bin/deno}"

if [[ ! -x "$python_bin" ]]; then
  echo "Python 3.11 not found at $python_bin"
  echo "Install it with: brew install python@3.11"
  exit 1
fi

if [[ ! -x "$ffmpeg_bin" || ! -x "$ffprobe_bin" ]]; then
  echo "FFmpeg with subtitle support not found at $ffmpeg_bin"
  echo "Install it with: brew install ffmpeg@7"
  exit 1
fi

if ! "$ffmpeg_bin" -hide_banner -filters 2>/dev/null | grep -Eq '(^|[[:space:]])subtitles([[:space:]]|$)'; then
  echo "FFmpeg at $ffmpeg_bin does not include the subtitles filter (libass)."
  echo "Install it with: brew install ffmpeg@7"
  exit 1
fi

if [[ ! -x "$deno_bin" ]]; then
  echo "Deno not found at $deno_bin"
  echo "Install it with: brew install deno"
  exit 1
fi

cd "$project_dir"
if [[ ! -d .venv ]]; then
  "$python_bin" -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-macos.txt

echo "Y2A-Auto macOS environment is ready."
echo "Set FFMPEG_LOCATION to: $ffmpeg_bin"
