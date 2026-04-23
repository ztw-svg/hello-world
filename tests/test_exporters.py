from pathlib import Path

from transcriber_tool.exporters import export_markdown, export_txt, render_lines
from transcriber_tool.models import TranscriptSegment


def test_export_text_files(tmp_path: Path) -> None:
    segments = [TranscriptSegment(start=0, end=1, text="你好", speaker="Speaker_1", gender="女")]
    lines = render_lines(segments, "mm:ss", include_timestamps=True)
    md = tmp_path / "a.md"
    txt = tmp_path / "a.txt"

    export_markdown(md, "标题", lines)
    export_txt(txt, "标题", lines)

    assert "# 标题" in md.read_text(encoding="utf-8")
    assert "[Speaker_1][女]" in md.read_text(encoding="utf-8")
    assert "标题" in txt.read_text(encoding="utf-8")
    assert segments[0].text == "你好"
