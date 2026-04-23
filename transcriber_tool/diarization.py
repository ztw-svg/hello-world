from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path

from transcriber_tool.models import TranscriptSegment


class DiarizationError(RuntimeError):
    pass


@dataclass
class SpeakerChunk:
    start: float
    end: float
    speaker: str


def diarize_speakers(wav_path: Path, hf_token: str) -> list[SpeakerChunk]:
    if importlib.util.find_spec("pyannote.audio") is None:
        raise DiarizationError("缺少 pyannote.audio，请安装 requirements.txt")
    if not hf_token:
        raise DiarizationError("说话人分离需要 Hugging Face Token")

    from pyannote.audio import Pipeline

    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=hf_token)
    diarization = pipeline(str(wav_path))

    chunks: list[SpeakerChunk] = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        chunks.append(SpeakerChunk(start=float(turn.start), end=float(turn.end), speaker=str(speaker)))
    chunks.sort(key=lambda c: c.start)
    return chunks


def assign_speakers(segments: list[TranscriptSegment], speakers: list[SpeakerChunk]) -> list[TranscriptSegment]:
    if not speakers:
        for seg in segments:
            if seg.speaker is None:
                seg.speaker = "Speaker_1"
        return segments

    for seg in segments:
        seg_mid = (seg.start + seg.end) / 2
        best = None
        best_dist = 1e9
        for spk in speakers:
            if spk.start <= seg_mid <= spk.end:
                best = spk.speaker
                break
            dist = min(abs(seg_mid - spk.start), abs(seg_mid - spk.end))
            if dist < best_dist:
                best_dist = dist
                best = spk.speaker
        seg.speaker = best or "Speaker_1"
    return segments


def estimate_gender_for_speakers(wav_path: Path, speakers: list[SpeakerChunk]) -> dict[str, str]:
    if importlib.util.find_spec("librosa") is None or importlib.util.find_spec("numpy") is None:
        raise DiarizationError("性别估计需要 librosa 与 numpy")

    import librosa
    import numpy as np

    audio, sr = librosa.load(str(wav_path), sr=16000, mono=True)
    mapping: dict[str, list[float]] = {}

    for chunk in speakers:
        start = int(chunk.start * sr)
        end = int(chunk.end * sr)
        frame = audio[start:end]
        if frame.size < sr:
            continue
        f0 = librosa.yin(frame, fmin=70, fmax=350, sr=sr)
        clean = f0[np.isfinite(f0)]
        if clean.size == 0:
            continue
        mapping.setdefault(chunk.speaker, []).append(float(np.median(clean)))

    labels: dict[str, str] = {}
    for speaker, pitches in mapping.items():
        if not pitches:
            labels[speaker] = "未知"
            continue
        p = sum(pitches) / len(pitches)
        if p >= 180:
            labels[speaker] = "女"
        elif p <= 155:
            labels[speaker] = "男"
        else:
            labels[speaker] = "未知"
    return labels
