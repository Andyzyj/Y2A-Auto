#!/bin/bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")/.." && pwd)"
label="com.andyzyj.y2a-whisper"
plist_path="$HOME/Library/LaunchAgents/$label.plist"
log_dir="$HOME/Library/Logs/Y2A-Auto"
hf_home="$HOME/Library/Application Support/Y2A-Auto/huggingface"
model="mlx-community/whisper-large-v3-turbo"

cd "$project_dir"
if [[ ! -x .venv/bin/python ]]; then
  echo "Missing .venv. Run scripts/setup_macos.sh first."
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$log_dir" "$hf_home"
HF_HOME="$hf_home" .venv/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('$model')"

PROJECT_DIR="$project_dir" PLIST_PATH="$plist_path" LOG_DIR="$log_dir" HF_CACHE_HOME="$hf_home" .venv/bin/python - <<'PY'
import os
import plistlib

label = 'com.andyzyj.y2a-whisper'
payload = {
    'Label': label,
    'ProgramArguments': ['/bin/bash', os.path.join(os.environ['PROJECT_DIR'], 'scripts/run_local_whisper_macos.sh')],
    'WorkingDirectory': os.environ['PROJECT_DIR'],
    'RunAtLoad': True,
    'KeepAlive': True,
    'ThrottleInterval': 10,
    'EnvironmentVariables': {
        'HF_HOME': os.environ['HF_CACHE_HOME'],
        'WHISPER_MODEL': 'mlx-community/whisper-large-v3-turbo',
        'WHISPER_HOST': '127.0.0.1',
        'WHISPER_PORT': '5052',
    },
    'StandardOutPath': os.path.join(os.environ['LOG_DIR'], 'whisper.stdout.log'),
    'StandardErrorPath': os.path.join(os.environ['LOG_DIR'], 'whisper.stderr.log'),
}
with open(os.environ['PLIST_PATH'], 'wb') as handle:
    plistlib.dump(payload, handle, sort_keys=False)
PY

chmod +x scripts/run_local_whisper_macos.sh
launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$plist_path"
launchctl enable "gui/$(id -u)/$label"
launchctl kickstart -k "gui/$(id -u)/$label"

echo "Local Whisper installed: http://127.0.0.1:5052"
echo "Model cache: $hf_home"
