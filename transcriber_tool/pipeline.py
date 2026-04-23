from __future__ import annotations

import json
import time
from pathlib import Path

from transcriber_tool.config import AppConfig
from transcriber_tool.diarization import DiarizationError, assign_speakers, diarize_speakers, estimate_gender_for_speakers
from transcriber_tool.engines import BaseEngine, build_engine
from transcriber_tool.media import download_from_url, extract_audio_to_wav, get_duration_seconds, split_audio
from transcriber_tool.models import ProgressUpdate, TranscriptSegment


class TranscriptionPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.engine: BaseEngine = build_engine(
            mode=config.settings.engine_mode,
            whisper_model_size=config.settings.whisper_model_size,
            device=config.settings.device,
            api_key=config.settings.api_key,
            api_base_url=config.settings.api_base_url,
        )

    def rebuild_engine(self) -> None:
        self.engine = build_engine(
            mode=self.config.settings.engine_mode,
            whisper_model_size=self.config.settings.whisper_model_size,
            device=self.config.settings.device,
            api_key=self.config.settings.api_key,
            api_base_url=self.config.settings.api_base_url,
        )

    def _checkpoint_path(self, job_name: str) -> Path:
        return self.config.checkpoints_dir / f"{job_name}.json"

    def _load_checkpoint(self, job_name: str) -> dict:
        cp = self._checkpoint_path(job_name)
        if cp.exists():
            return json.loads(cp.read_text(encoding="utf-8"))
        return {"completed": {}}

    def _save_checkpoint(self, job_name: str, data: dict) -> None:
        self._checkpoint_path(job_name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _apply_diarization(self, wav_path: Path, merged: list[TranscriptSegment], progress_cb) -> list[TranscriptSegment]:
        if not self.config.settings.enable_speaker_diarization:
            return merged

        progress_cb(ProgressUpdate(percent=96, eta_seconds=None, message="说话人分离中"))
        speakers = diarize_speakers(wav_path, hf_token=self.config.settings.hf_token)
        assign_speakers(merged, speakers)

        if self.config.settings.enable_gender_label:
            progress_cb(ProgressUpdate(percent=98, eta_seconds=None, message="性别标签估计中"))
            labels = estimate_gender_for_speakers(wav_path, speakers)
            for seg in merged:
                if seg.speaker:
                    seg.gender = labels.get(seg.speaker, "未知")
        return merged

    def run(self, source: str, is_url: bool, progress_cb) -> list[TranscriptSegment]:
        work = self.config.cache_dir / str(int(time.time()))
        work.mkdir(parents=True, exist_ok=True)

        source_path = Path(source)
        if is_url:
            progress_cb(ProgressUpdate(percent=2, eta_seconds=None, message="下载在线视频"))
            source_path = download_from_url(source, work / "download")

        progress_cb(ProgressUpdate(percent=8, eta_seconds=None, message="提取音频"))
        wav_path = extract_audio_to_wav(source_path, work / "audio.wav")
        total_duration = get_duration_seconds(wav_path)

        progress_cb(ProgressUpdate(percent=12, eta_seconds=None, message="切片长音频"))
        chunks = split_audio(wav_path, work / "chunks", self.config.settings.segment_seconds)

        job_name = f"{source_path.stem}_{int(total_duration)}"
        checkpoint = self._load_checkpoint(job_name)
        completed = checkpoint.get("completed", {})

        merged: list[TranscriptSegment] = []
        elapsed_audio = 0.0
        started = time.time()

        for index, chunk in enumerate(chunks):
            chunk_key = str(index)
            chunk_duration = get_duration_seconds(chunk)
            chunk_offset = elapsed_audio

            if completed.get(chunk_key):
                for seg in completed[chunk_key]:
                    merged.append(
                        TranscriptSegment(
                            start=float(seg["start"]),
                            end=float(seg["end"]),
                            text=seg["text"],
                            confidence=seg.get("confidence"),
                        )
                    )
                elapsed_audio += chunk_duration
                continue

            chunk_segments = self.engine.transcribe_file(chunk, language=self.config.settings.language)
            stored: list[dict] = []
            for seg in chunk_segments:
                adjusted = TranscriptSegment(
                    start=seg.start + chunk_offset,
                    end=seg.end + chunk_offset,
                    text=seg.text,
                    confidence=seg.confidence,
                )
                merged.append(adjusted)
                stored.append(
                    {
                        "start": adjusted.start,
                        "end": adjusted.end,
                        "text": adjusted.text,
                        "confidence": adjusted.confidence,
                    }
                )

            completed[chunk_key] = stored
            checkpoint["completed"] = completed
            self._save_checkpoint(job_name, checkpoint)

            elapsed_audio += chunk_duration
            speed = elapsed_audio / max(0.001, (time.time() - started))
            remaining = max(0.0, total_duration - elapsed_audio)
            eta = remaining / max(speed, 1e-6)
            percent = 12 + 82 * min(1.0, elapsed_audio / max(total_duration, 1e-6))
            progress_cb(
                ProgressUpdate(
                    percent=percent,
                    eta_seconds=eta,
                    message=f"识别中 {index + 1}/{len(chunks)}",
                )
            )

        merged.sort(key=lambda s: s.start)
        try:
            merged = self._apply_diarization(wav_path, merged, progress_cb)
        except DiarizationError:
            pass

        return merged
