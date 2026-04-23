from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Literal

ImageType = Literal[
    "portrait",
    "landscape",
    "product",
    "food",
    "wedding",
    "kids",
    "id",
    "old_photo",
]


@dataclass(slots=True)
class LightingInfo:
    type: Literal["front", "back", "side", "diffuse", "artificial"]
    cct: int
    wb_shift: float


@dataclass(slots=True)
class ExposureInfo:
    state: Literal["under", "normal", "over"]
    ev: float
    dynamic_range: Literal["low", "mid", "high"]


@dataclass(slots=True)
class QualityInfo:
    noise: Literal["low", "mid", "high"]
    blur: Literal["low", "mid", "high"]


@dataclass(slots=True)
class FaceInfo:
    bbox: list[int]
    age_group: Literal["child", "adult", "elder"]
    gender: Literal["male", "female", "unknown"]
    landmarks: str = "68pts"


@dataclass(slots=True)
class AnalysisResult:
    image_type: ImageType
    lighting: LightingInfo
    exposure: ExposureInfo
    quality: QualityInfo
    mood: Literal["warm", "cool", "lively", "calm"]
    faces: list[FaceInfo]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload
