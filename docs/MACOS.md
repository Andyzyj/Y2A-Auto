# macOS local deployment

This setup runs Y2A-Auto natively on Apple Silicon and keeps the Web service
on the local machine by default.

## Requirements

```bash
brew install python@3.11 ffmpeg deno
```

## Install

```bash
scripts/setup_macos.sh
```

## Run

```bash
scripts/run_macos.sh
```

Open <http://127.0.0.1:5000>. Set `HOST=0.0.0.0` only when LAN access is
intended and login protection has been configured.

Runtime configuration, cookies, the database, logs, downloads, and the Python
virtual environment are excluded by `.gitignore` and should remain local.
