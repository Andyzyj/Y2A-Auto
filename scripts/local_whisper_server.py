#!/usr/bin/env python3
"""Local MLX Whisper service with the OpenAI audio API surface used by Y2A."""

from __future__ import annotations

import json
import logging
import math
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List

from flask import Flask, Response, jsonify, request


DEFAULT_MODEL = 'mlx-community/whisper-large-v3-turbo'
MODEL_ALIASES = {'large-v3-turbo', 'whisper-large-v3-turbo', DEFAULT_MODEL}
_INFERENCE_LOCK = threading.Lock()


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else 0.0
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, 'item'):
        return _json_safe(value.item())
    return str(value)


def _timestamp(seconds: float, separator: str = ',') -> str:
    millis = max(0, int(round(_finite_float(seconds) * 1000)))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f'{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}'


def _render_srt(segments: Iterable[Dict[str, Any]]) -> str:
    blocks: List[str] = []
    for index, segment in enumerate(segments, start=1):
        text = str(segment.get('text') or '').strip()
        if not text:
            continue
        blocks.append(
            f"{index}\n{_timestamp(segment.get('start', 0.0))} --> "
            f"{_timestamp(segment.get('end', 0.0))}\n{text}"
        )
    return '\n\n'.join(blocks) + ('\n' if blocks else '')


def _render_vtt(segments: Iterable[Dict[str, Any]]) -> str:
    blocks = ['WEBVTT']
    for segment in segments:
        text = str(segment.get('text') or '').strip()
        if text:
            blocks.append(
                f"{_timestamp(segment.get('start', 0.0), '.')} --> "
                f"{_timestamp(segment.get('end', 0.0), '.')}\n{text}"
            )
    return '\n\n'.join(blocks) + '\n'


def _normalize_result(raw: Dict[str, Any], task: str) -> Dict[str, Any]:
    result = _json_safe(raw if isinstance(raw, dict) else {})
    segments = result.get('segments') or []
    words: List[Dict[str, Any]] = []
    for segment_index, segment in enumerate(segments):
        segment.setdefault('id', segment_index)
        segment.setdefault('start', 0.0)
        segment.setdefault('end', segment.get('start', 0.0))
        for word in segment.get('words') or []:
            words.append(word)
    duration = result.get('duration')
    if duration is None:
        duration = max((_finite_float(item.get('end')) for item in segments), default=0.0)
    return {
        'task': task,
        'language': result.get('language') or '',
        'duration': _finite_float(duration),
        'text': str(result.get('text') or '').strip(),
        'segments': segments,
        'words': result.get('words') or words,
    }


def _default_transcriber(audio_path: str, **options: Any) -> Dict[str, Any]:
    import mlx_whisper

    return mlx_whisper.transcribe(audio_path, **options)


def create_app(transcriber: Callable[..., Dict[str, Any]] | None = None) -> Flask:
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('WHISPER_MAX_UPLOAD_BYTES', 4 * 1024**3))
    run_transcription = transcriber or _default_transcriber
    configured_model = os.environ.get('WHISPER_MODEL', DEFAULT_MODEL).strip() or DEFAULT_MODEL

    @app.get('/health')
    def health():
        return jsonify({'status': 'ok', 'engine': 'mlx-whisper', 'model': configured_model})

    @app.get('/v1/models')
    def models():
        return jsonify({'object': 'list', 'data': [{'id': 'large-v3-turbo', 'object': 'model'}]})

    def transcribe(task: str):
        upload = request.files.get('file')
        if upload is None or not upload.filename:
            return jsonify({'error': {'message': 'A non-empty audio file is required.', 'type': 'invalid_request_error'}}), 400

        requested_model = str(request.form.get('model') or 'large-v3-turbo').strip()
        if requested_model not in MODEL_ALIASES:
            return jsonify({'error': {'message': f'Unsupported model: {requested_model}', 'type': 'invalid_request_error'}}), 400

        granularities = request.form.getlist('timestamp_granularities[]')
        granularities += request.form.getlist('timestamp_granularities')
        if not granularities:
            raw_granularities = str(request.form.get('timestamp_granularities') or '')
            granularities = [item.strip() for item in raw_granularities.split(',') if item.strip()]
        word_timestamps = 'word' in granularities
        response_format = str(request.form.get('response_format') or 'json').lower()
        suffix = Path(upload.filename).suffix or '.audio'

        temp_path = ''
        try:
            with tempfile.NamedTemporaryFile(prefix='y2a_whisper_', suffix=suffix, delete=False) as handle:
                temp_path = handle.name
                upload.save(handle)

            options: Dict[str, Any] = {
                'path_or_hf_repo': configured_model,
                'task': task,
                'word_timestamps': word_timestamps,
                'verbose': False,
                'condition_on_previous_text': str(request.form.get('condition_on_previous_text', 'false')).lower() in {'1', 'true', 'yes', 'on'},
            }
            language = str(request.form.get('language') or '').strip()
            prompt = str(request.form.get('prompt') or '').strip()
            if language and task != 'translate':
                options['language'] = language
            if prompt:
                options['initial_prompt'] = prompt
            if request.form.get('temperature') not in (None, ''):
                options['temperature'] = _finite_float(request.form.get('temperature'))
            if request.form.get('no_speech_threshold') not in (None, ''):
                options['no_speech_threshold'] = _finite_float(request.form.get('no_speech_threshold'), 0.6)

            with _INFERENCE_LOCK:
                payload = _normalize_result(run_transcription(temp_path, **options), task)

            if response_format == 'verbose_json':
                return jsonify(payload)
            if response_format == 'json':
                return jsonify({'text': payload['text'], 'language': payload['language']})
            if response_format == 'srt':
                return Response(_render_srt(payload['segments']), mimetype='text/plain')
            if response_format == 'vtt':
                return Response(_render_vtt(payload['segments']), mimetype='text/vtt')
            if response_format == 'text':
                return Response(payload['text'] + '\n', mimetype='text/plain')
            return jsonify({'error': {'message': f'Unsupported response_format: {response_format}', 'type': 'invalid_request_error'}}), 400
        except Exception as exc:
            app.logger.exception('Local Whisper transcription failed')
            return jsonify({'error': {'message': str(exc), 'type': 'server_error'}}), 500
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    app.add_url_rule('/v1/audio/transcriptions', 'audio_transcriptions', lambda: transcribe('transcribe'), methods=['POST'])
    app.add_url_rule('/v1/audio/translations', 'audio_translations', lambda: transcribe('translate'), methods=['POST'])
    return app


def main() -> None:
    logging.basicConfig(level=os.environ.get('WHISPER_LOG_LEVEL', 'INFO'))
    host = os.environ.get('WHISPER_HOST', '127.0.0.1')
    port = int(os.environ.get('WHISPER_PORT', '5052'))
    create_app().run(host=host, port=port, threaded=True, use_reloader=False)


if __name__ == '__main__':
    main()
