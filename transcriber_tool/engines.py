from __future__ import annotations

import importlib.util
from pathlib import Path

from transcriber_tool.models import TranscriptSegment


class EngineError(RuntimeError):
    pass


class BaseEngine:
    def transcribe_file(self, wav_path: Path, language: str = "auto") -> list[TranscriptSegment]:
        raise NotImplementedError


class WhisperEngine(BaseEngine):
    def __init__(self, model_size: str = "small", device: str = "auto") -> None:
        if importlib.util.find_spec("faster_whisper") is None:
            raise EngineError("缺少 faster-whisper，请先安装 requirements.txt")
        from faster_whisper import WhisperModel

        self.model = WhisperModel(model_size, device=device)

    def transcribe_file(self, wav_path: Path, language: str = "auto") -> list[TranscriptSegment]:
        lang = None if language == "auto" else language
        segments, _ = self.model.transcribe(
            str(wav_path),
            language=lang,
            vad_filter=True,
            word_timestamps=True,
        )
        parsed: list[TranscriptSegment] = []
        for seg in segments:
            text = seg.text.strip() or "[无法识别]"
            confidence = float(seg.avg_logprob) if hasattr(seg, "avg_logprob") else None
            parsed.append(
                TranscriptSegment(
                    start=float(seg.start),
                    end=float(seg.end),
                    text=text,
                    confidence=confidence,
                )
            )
        if not parsed:
            parsed.append(TranscriptSegment(start=0.0, end=0.0, text="[无法识别]"))
        return parsed


class OpenAIEngine(BaseEngine):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1") -> None:
        if importlib.util.find_spec("openai") is None:
            raise EngineError("缺少 openai SDK，请先安装 requirements.txt")
        if not api_key:
            raise EngineError("云端识别模式需要 API Key")

        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def transcribe_file(self, wav_path: Path, language: str = "auto") -> list[TranscriptSegment]:
        with wav_path.open("rb") as audio_file:
            kwargs = {
                "model": "gpt-4o-mini-transcribe",
                "file": audio_file,
                "response_format": "verbose_json",
            }
            if language != "auto":
                kwargs["language"] = language
            response = self.client.audio.transcriptions.create(**kwargs)

        segments: list[TranscriptSegment] = []
        if hasattr(response, "segments") and response.segments:
            for seg in response.segments:
                text = (seg.text or "").strip() or "[无法识别]"
                confidence = getattr(seg, "avg_logprob", None)
                segments.append(
                    TranscriptSegment(
                        start=float(seg.start),
                        end=float(seg.end),
                        text=text,
                        confidence=float(confidence) if confidence is not None else None,
                    )
                )
        else:
            text = getattr(response, "text", "").strip() or "[无法识别]"
            segments.append(TranscriptSegment(start=0.0, end=0.0, text=text))
        return segments


def build_engine(mode: str, whisper_model_size: str, device: str, api_key: str, api_base_url: str) -> BaseEngine:
    if mode == "cloud_openai":
        return OpenAIEngine(api_key=api_key, base_url=api_base_url)
    return WhisperEngine(model_size=whisper_model_size, device=device)
