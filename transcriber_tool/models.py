from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str
    confidence: float | None = None


@dataclass
class ProgressUpdate:
    percent: float
    eta_seconds: float | None
    message: str
