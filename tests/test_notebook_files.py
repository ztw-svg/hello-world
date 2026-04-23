import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
OFFLINE = ROOT / "离线版-男女对话记事本.html"


class NotebookFilesTest(unittest.TestCase):
    def test_core_files_exist(self):
        self.assertTrue(INDEX.exists(), "index.html should exist")
        self.assertTrue(OFFLINE.exists(), "offline html should exist")

    def test_offline_file_matches_index(self):
        self.assertEqual(INDEX.read_text(encoding="utf-8"), OFFLINE.read_text(encoding="utf-8"))

    def test_required_ui_controls_present(self):
        html = INDEX.read_text(encoding="utf-8")
        for control_id in [
            "speaker",
            "title",
            "content",
            "addBtn",
            "saveBtn",
            "exportBtn",
            "toggleImportBtn",
            "runImportBtn",
        ]:
            self.assertIn(f'id="{control_id}"', html)

    def test_required_behaviors_present(self):
        html = INDEX.read_text(encoding="utf-8")
        for fn_name in [
            "addEntry",
            "saveLocal",
            "loadLocal",
            "exportTxt",
            "importDialogue",
            "parseLine",
        ]:
            self.assertRegex(html, rf"function\s+{fn_name}\s*\(")
        self.assertIn("localStorage.setItem", html)
        self.assertIn("localStorage.getItem", html)


if __name__ == "__main__":
    unittest.main()
