from pathlib import Path

from ai_image_optimizer.image_io import SimpleImage, supported_extensions, write_image
from ai_image_optimizer.pipeline import ImageOptimizationPipeline
from ai_image_optimizer.presets import list_presets


def test_pipeline_run(tmp_path: Path) -> None:
    pixels = [(120, 100, 90)] * (64 * 64)
    img = SimpleImage(width=64, height=64, pixels=pixels)
    input_path = tmp_path / "input.ppm"
    output_path = tmp_path / "output.ppm"
    write_image(img, input_path)

    pipe = ImageOptimizationPipeline()
    result = pipe.run(input_path, output_path, preset_name="清新", strength=1.0)

    assert output_path.exists()
    assert result.analysis.image_type in {"portrait", "landscape", "product", "food"}


def test_presets_non_empty() -> None:
    assert "奶油肌" in list_presets()


def test_supported_extensions_contains_ppm() -> None:
    assert ".ppm" in supported_extensions()
