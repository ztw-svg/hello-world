from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"}
DEFAULT_SEGMENT_SECONDS = 600


@dataclass
class Settings:
    language: str = "auto"
    timestamp_format: str = "mm:ss"
    output_format: str = "markdown"
    segment_seconds: int = DEFAULT_SEGMENT_SECONDS
    engine_mode: str = "local_whisper"
    whisper_model_size: str = "small"
    device: str = "auto"
    api_base_url: str = "https://api.openai.com/v1"
    api_key: str = ""


@dataclass
class AppConfig:
    workspace: Path
    settings: Settings

    @property
    def checkpoints_dir(self) -> Path:
        d = self.workspace / "checkpoints"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def cache_dir(self) -> Path:
        d = self.workspace / "cache"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def drafts_dir(self) -> Path:
        d = self.workspace / "drafts"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def settings_file(self) -> Path:
        return self.workspace / "settings.json"

    @classmethod
    def load(cls, workspace: Path) -> "AppConfig":
        workspace.mkdir(parents=True, exist_ok=True)
        settings_file = workspace / "settings.json"
        if not settings_file.exists():
            settings = Settings()
            cfg = cls(workspace=workspace, settings=settings)
            cfg.save()
            return cfg

        data = json.loads(settings_file.read_text(encoding="utf-8"))
        settings = Settings(**data)
        return cls(workspace=workspace, settings=settings)

    def save(self) -> None:
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.settings_file.write_text(
            json.dumps(asdict(self.settings), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
