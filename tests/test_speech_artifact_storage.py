import json
import logging
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from modules.speech_recognition import SpeechRecognitionConfig, SpeechRecognizer


class SpeechArtifactStorageTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.task_dir = os.path.join(self.root, 'downloads', 'task-id')
        os.makedirs(self.task_dir)
        self.output_path = os.path.join(self.task_dir, 'asr_task-id.srt')
        self.video_path = os.path.join(self.task_dir, 'video.mp4')
        open(self.video_path, 'wb').close()
        logging.disable(logging.CRITICAL)
        self.recognizer = SpeechRecognizer(SpeechRecognitionConfig(api_key='key'), task_id='artifact-test')

    def tearDown(self):
        self.recognizer._cleanup_temp_files()
        logging.disable(logging.NOTSET)
        shutil.rmtree(self.root, ignore_errors=True)

    def test_whisper_artifacts_live_under_task_download_directory(self):
        self.recognizer._prepare_artifact_dir(self.output_path)
        whisper_dir = os.path.join(self.task_dir, 'whisper')
        self.assertEqual(self.recognizer._artifact_dir, whisper_dir)
        self.assertTrue(os.path.isdir(os.path.join(whisper_dir, 'chunks')))

        source = os.path.join(whisper_dir, 'source_audio.wav')
        with open(source, 'wb') as handle:
            handle.write(b'audio')
        with open(self.output_path, 'w', encoding='utf-8') as handle:
            handle.write('1\n00:00:00,000 --> 00:00:01,000\nhello\n')

        self.recognizer._resolve_quality_state(self.output_path)
        self.recognizer._write_artifact_manifest(self.video_path, self.output_path)

        manifest_path = os.path.join(whisper_dir, 'manifest.json')
        with open(manifest_path, encoding='utf-8') as handle:
            manifest = json.load(handle)
        self.assertEqual(manifest['cleanup_scope'], 'task_download_directory')
        self.assertEqual(manifest['model'], 'whisper-1')
        self.assertIn('whisper/source_audio.wav', [item['path'] for item in manifest['artifacts']])

    def test_cleanup_keeps_persisted_artifact_directory(self):
        self.recognizer._prepare_artifact_dir(self.output_path)
        marker = os.path.join(self.recognizer._artifact_dir, 'source_audio.wav')
        with open(marker, 'wb') as handle:
            handle.write(b'audio')

        self.recognizer._cleanup_temp_files()

        self.assertTrue(os.path.exists(marker))


if __name__ == '__main__':
    unittest.main()
