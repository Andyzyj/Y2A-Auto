import io
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.local_whisper_server import create_app


class LocalWhisperServerTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

        def fake_transcriber(path, **options):
            self.calls.append((path, options))
            return {
                'language': 'zh',
                'text': '你好，世界',
                'segments': [{
                    'start': 0.0,
                    'end': 1.25,
                    'text': '你好，世界',
                    'words': [
                        {'word': '你好', 'start': 0.0, 'end': 0.55, 'probability': 0.99},
                        {'word': '世界', 'start': 0.6, 'end': 1.25, 'probability': 0.98},
                    ],
                }],
            }

        app = create_app(fake_transcriber)
        app.config['TESTING'] = True
        self.client = app.test_client()

    def _audio(self, **fields):
        data = {'file': (io.BytesIO(b'RIFF-test'), 'sample.wav'), 'model': 'large-v3-turbo'}
        data.update(fields)
        return data

    def test_health_exposes_local_model(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['engine'], 'mlx-whisper')

    def test_verbose_json_preserves_word_timestamps(self):
        response = self.client.post(
            '/v1/audio/transcriptions',
            data=self._audio(response_format='verbose_json', **{'timestamp_granularities[]': 'word'}),
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['words'][0]['word'], '你好')
        self.assertTrue(self.calls[0][1]['word_timestamps'])
        self.assertFalse(os.path.exists(self.calls[0][0]))

    def test_srt_response_is_openai_compatible(self):
        response = self.client.post(
            '/v1/audio/transcriptions',
            data=self._audio(response_format='srt'),
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('00:00:00,000 --> 00:00:01,250', response.get_data(as_text=True))

    def test_unknown_model_is_rejected(self):
        response = self.client.post(
            '/v1/audio/transcriptions',
            data={'file': (io.BytesIO(b'audio'), 'a.wav'), 'model': 'other'},
            content_type='multipart/form-data',
        )
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
