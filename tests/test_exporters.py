from pathlib import Path

from transcriber_tool.exporters import export_markdown, export_txt
from transcriber_tool.models import TranscriptSegment


def test_export_text_files(tmp_path: Path) -> None:
    segments = [TranscriptSegment(start=0, end=1, text="你好")]
    md = tmp_path / "a.md"
    txt = tmp_path / "a.txt"

    export_markdown(md, "标题", ["[00:00] 你好"])
    export_txt(txt, "标题", ["[00:00] 你好"])

    assert "# 标题" in md.read_text(encoding="utf-8")
    assert "标题" in txt.read_text(encoding="utf-8")
    assert segments[0].text == "你好"
