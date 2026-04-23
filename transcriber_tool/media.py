from __future__ import annotations

import json
import subprocess
from pathlib import Path


class MediaError(RuntimeError):
    pass


def download_from_url(url: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(output_dir / "%(title)s.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f",
        "bestaudio/best",
        "-o",
        output_template,
        "--restrict-filenames",
        "--no-playlist",
        url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MediaError(f"yt-dlp 下载失败: {result.stderr.strip()}")

    files = sorted(output_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise MediaError("下载完成但未找到文件")
    return files[0]


def extract_audio_to_wav(input_path: Path, output_wav: Path) -> Path:
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_wav),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MediaError(f"FFmpeg 音频提取失败: {result.stderr.strip()}")
    return output_wav


def get_duration_seconds(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MediaError(f"ffprobe 失败: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def split_audio(input_wav: Path, output_dir: Path, segment_seconds: int) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    pattern = output_dir / "chunk_%04d.wav"
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_wav),
        "-f",
        "segment",
        "-segment_time",
        str(segment_seconds),
        "-c",
        "copy",
        str(pattern),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise MediaError(f"FFmpeg 切片失败: {result.stderr.strip()}")
    chunks = sorted(output_dir.glob("chunk_*.wav"))
    if not chunks:
        return [input_wav]
    return chunks
