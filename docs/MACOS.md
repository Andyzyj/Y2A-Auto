# macOS local deployment

This setup runs Y2A-Auto natively on Apple Silicon and keeps the Web service
on the local machine by default.

## Requirements

```bash
brew install python@3.11 ffmpeg@7 deno
```

Y2A requires FFmpeg's `subtitles` filter (libass) to burn captions into video.
The setup script checks for that filter and defaults to the versioned Homebrew
binary at `/opt/homebrew/opt/ffmpeg@7/bin/ffmpeg`. In Y2A settings, set
`FFMPEG_LOCATION` to that path. A different FFmpeg build can be used by passing
`FFMPEG_BIN` and `FFPROBE_BIN` when running the setup script, provided it
includes the `subtitles` filter.

## Install

```bash
scripts/setup_macos.sh
```

## Run

```bash
scripts/run_macos.sh
```

Open <http://127.0.0.1:5051>. Port 5051 avoids the AirPlay receiver that can
occupy port 5000 on macOS. Set `HOST=0.0.0.0` only when LAN access is
intended and login protection has been configured.

Runtime configuration, cookies, the database, logs, downloads, and the Python
virtual environment are excluded by `.gitignore` and should remain local.

## Local Whisper large-v3-turbo

Apple Silicon Macs can use MLX to expose a local OpenAI-compatible Whisper
Audio API. The installer downloads the approximately 1.61 GB
`mlx-community/whisper-large-v3-turbo` model and registers the
`com.andyzyj.y2a-whisper` LaunchAgent:

```bash
scripts/install_local_whisper_macos.sh
curl http://127.0.0.1:5052/health
```

Configure Y2A speech recognition with these values:

- Provider: `Whisper (OpenAI compatible)`
- Base URL: `http://127.0.0.1:5052/v1`
- Model: `large-v3-turbo`
- API key: any non-empty local marker, such as `local-whisper`
- Maximum workers: `1`, so local unified memory is not contested by concurrent inference

Source audio, window clips, and a transcription manifest are kept in the
task download directory under `whisper/`. Manual and scheduled download
cleanup, per-task deletion, and post-upload deletion therefore remove them
with the downloaded video. The model cache lives at
`~/Library/Application Support/Y2A-Auto/huggingface` and is not affected by
task cleanup.
