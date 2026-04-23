from __future__ import annotations

from pathlib import Path


def format_timestamp(seconds: float, mode: str) -> str:
    total = int(max(0, seconds))
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if mode == "hh:mm:ss":
        return f"[{h:02d}:{m:02d}:{s:02d}]"
    return f"[{(h * 60) + m:02d}:{s:02d}]"


def has_supported_media_ext(path: Path) -> bool:
    from transcriber_tool.config import SUPPORTED_AUDIO_EXTENSIONS, SUPPORTED_VIDEO_EXTENSIONS

    ext = path.suffix.lower()
    return ext in SUPPORTED_AUDIO_EXTENSIONS or ext in SUPPORTED_VIDEO_EXTENSIONS
