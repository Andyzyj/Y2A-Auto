import unittest

from modules.task_manager import TaskProcessor


class HDRSubtitlePipelineTests(unittest.TestCase):
    def test_detects_pq_and_hlg_as_hdr(self):
        self.assertTrue(TaskProcessor._is_hdr_stream_info({'color_transfer': 'smpte2084'}))
        self.assertTrue(TaskProcessor._is_hdr_stream_info({'color_transfer': 'arib-std-b67'}))
        self.assertFalse(TaskProcessor._is_hdr_stream_info({'color_transfer': 'bt709'}))

    def test_x265_hdr_params_force_main10_and_hvc1(self):
        params = TaskProcessor._force_main10_x265_params([
            '-c:v', 'libx265', '-profile:v', 'main', '-pix_fmt', 'yuv420p',
        ])
        self.assertEqual(params[params.index('-profile:v') + 1], 'main10')
        self.assertEqual(params[params.index('-pix_fmt') + 1], 'yuv420p10le')
        self.assertEqual(params[params.index('-tag:v') + 1], 'hvc1')

    def test_apple_hdr_params_use_videotoolbox_main10(self):
        params = TaskProcessor._build_apple_hdr_params(120)
        self.assertEqual(params[params.index('-c:v') + 1], 'hevc_videotoolbox')
        self.assertEqual(params[params.index('-profile:v') + 1], 'main10')
        self.assertEqual(params[params.index('-pix_fmt') + 1], 'p010le')
        self.assertEqual(params[params.index('-tag:v') + 1], 'hvc1')

    def test_accepts_complete_main10_hdr_output(self):
        stream = {
            'codec_name': 'hevc',
            'profile': 'Main 10',
            'codec_tag_string': 'hvc1',
            'pix_fmt': 'yuv420p10le',
            'color_primaries': 'bt2020',
            'color_transfer': 'smpte2084',
            'color_space': 'bt2020nc',
        }
        self.assertEqual(TaskProcessor._hdr_output_validation_error(stream), '')

    def test_rejects_8_bit_or_missing_hdr_metadata(self):
        base = {
            'codec_name': 'hevc',
            'profile': 'Main 10',
            'codec_tag_string': 'hvc1',
            'pix_fmt': 'yuv420p10le',
            'color_primaries': 'bt2020',
            'color_transfer': 'arib-std-b67',
            'color_space': 'bt2020nc',
        }
        eight_bit = dict(base, profile='Main', pix_fmt='yuv420p')
        self.assertIn('Main 10', TaskProcessor._hdr_output_validation_error(eight_bit))
        missing_transfer = dict(base, color_transfer=None)
        self.assertIn('HLG/PQ', TaskProcessor._hdr_output_validation_error(missing_transfer))


if __name__ == '__main__':
    unittest.main()
