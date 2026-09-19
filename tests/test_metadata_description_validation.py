import unittest

from modules.ai_enhancer import _is_natural_description, _validate_output


class MetadataDescriptionValidationTests(unittest.TestCase):
    def test_short_natural_chinese_closing_paragraph_is_accepted(self):
        description = (
            "无敌。最终雨水根本无法触及飞机。\n\n"
            "感觉就像这段视频里看到的一样，但想象一下你第一次开快车时胃里的那种感觉。"
            "燃料以每秒两加仑的速度冲过管线，加力燃烧室点燃后，声音变成风噪对着座舱盖的呼啸。\n\n"
            "生活美好。"
        )

        self.assertTrue(_is_natural_description(description, max_blocks=None))
        valid, reasons = _validate_output(
            "English source description",
            description,
            content_type="description",
            description_max_blocks=None,
        )
        self.assertTrue(valid)
        self.assertNotIn("description_not_natural", reasons)

    def test_trivial_fragment_is_still_rejected(self):
        self.assertFalse(_is_natural_description("正文内容完整。\n\n好。", max_blocks=None))

    def test_list_format_is_still_rejected(self):
        self.assertFalse(_is_natural_description("- 第一项内容\n- 第二项内容", max_blocks=None))


if __name__ == "__main__":
    unittest.main()
