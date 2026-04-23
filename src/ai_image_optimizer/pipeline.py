from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .analyzer import Analyzer
from .image_io import read_image, write_image
from .models import AnalysisResult
from .optimizer import Optimizer
from .presets import get_preset


@dataclass(slots=True)
class PipelineResult:
    analysis: AnalysisResult
    output_path: Path


class ImageOptimizationPipeline:
    def __init__(self) -> None:
        self.analyzer = Analyzer()
        self.optimizer = Optimizer()

    def run(
        self,
        input_path: str | Path,
        output_path: str | Path,
        preset_name: str | None = None,
        strength: float = 1.0,
    ) -> PipelineResult:
        src = Path(input_path)
        dst = Path(output_path)
        image = read_image(src)

        analysis = self.analyzer.analyze(image)
        preset = get_preset(preset_name) if preset_name else None
        out = self.optimizer.optimize(image, analysis, preset=preset, strength=strength)

        write_image(out, dst)
        return PipelineResult(analysis=analysis, output_path=dst)
