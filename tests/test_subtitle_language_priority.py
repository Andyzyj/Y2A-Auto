import ast
import os
import pathlib
import unittest


def _load_functions(*names):
    module_path = pathlib.Path(__file__).resolve().parents[1] / "modules" / "task_manager.py"
    source = module_path.read_text(encoding="utf-8")
    module_ast = ast.parse(source, filename=str(module_path))
    selected = [
        node for node in module_ast.body
        if isinstance(node, ast.FunctionDef) and node.name in names
    ]
    namespace = {"os": os}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(module_path), "exec"), namespace)
    return [namespace[name] for name in names]


class SubtitleLanguagePriorityTests(unittest.TestCase):
    def test_preserves_full_chinese_language_tags(self):
        language_tag, _ = _load_functions(
            "_subtitle_language_tag", "_subtitle_candidate_priority"
        )

        self.assertEqual(language_tag("video.zh-Hans.srt"), "zh-hans")
        self.assertEqual(language_tag("video.zh-Hant.srt"), "zh-hant")
        self.assertEqual(language_tag("video.en-orig.vtt"), "en-orig")

    def test_prefers_simplified_then_original_english_before_traditional(self):
        _, priority = _load_functions(
            "_subtitle_language_tag", "_subtitle_candidate_priority"
        )
        candidates = [
            "video.zh-Hant.srt",
            "video.en.srt",
            "video.en-orig.vtt",
            "video.zh-Hans.vtt",
        ]

        self.assertEqual(
            sorted(candidates, key=priority),
            [
                "video.zh-Hans.vtt",
                "video.en-orig.vtt",
                "video.en.srt",
                "video.zh-Hant.srt",
            ],
        )


if __name__ == "__main__":
    unittest.main()
