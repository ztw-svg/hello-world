from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Event

from .pipeline import ImageOptimizationPipeline


@dataclass(slots=True)
class BatchItem:
    input_path: Path
    output_path: Path


class BatchProcessor:
    def __init__(self) -> None:
        self.pipeline = ImageOptimizationPipeline()
        self._paused = Event()
        self._paused.set()

    def pause(self) -> None:
        self._paused.clear()

    def resume(self) -> None:
        self._paused.set()

    def process(
        self,
        items: list[BatchItem],
        preset_name: str | None = None,
        strength: float = 1.0,
    ) -> list[dict]:
        results: list[dict] = []
        total = len(items)
        for idx, item in enumerate(items, start=1):
            self._paused.wait()
            result = self.pipeline.run(item.input_path, item.output_path, preset_name, strength)
            results.append(
                {
                    "index": idx,
                    "total": total,
                    "input": str(item.input_path),
                    "output": str(result.output_path),
                    "analysis": result.analysis.to_dict(),
                    "progress": round(idx / max(total, 1), 4),
                }
            )
        return results
