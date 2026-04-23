from __future__ import annotations

from .image_io import SimpleImage
from .models import AnalysisResult


class Optimizer:
    def optimize(
        self,
        image: SimpleImage,
        analysis: AnalysisResult,
        preset: dict[str, float] | None = None,
        strength: float = 1.0,
    ) -> SimpleImage:
        params = self._auto_params(analysis)
        if preset:
            for key, value in preset.items():
                params[key] = params.get(key, 0.0) + value
        params = {k: float(v) * strength for k, v in params.items()}

        new_pixels: list[tuple[int, int, int]] = []
        for r, g, b in image.pixels:
            nr, ng, nb = self._adjust_pixel(r, g, b, params)
            new_pixels.append((nr, ng, nb))

        out = SimpleImage(width=image.width, height=image.height, pixels=new_pixels)
        smooth = max(0.0, params.get("skin_smooth", 0.0))
        if smooth > 0:
            out = self._box_smooth(out, rounds=1 if smooth < 0.3 else 2)
        return out

    def _adjust_pixel(self, r: int, g: int, b: int, params: dict[str, float]) -> tuple[int, int, int]:
        brightness = params.get("brightness", 0.0)
        contrast = params.get("contrast", 0.0)
        saturation = params.get("saturation", 0.0)

        rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
        rf += brightness
        gf += brightness
        bf += brightness

        rf = (rf - 0.5) * (1 + contrast) + 0.5
        gf = (gf - 0.5) * (1 + contrast) + 0.5
        bf = (bf - 0.5) * (1 + contrast) + 0.5

        gray = 0.299 * rf + 0.587 * gf + 0.114 * bf
        rf = gray + (rf - gray) * (1 + saturation)
        gf = gray + (gf - gray) * (1 + saturation)
        bf = gray + (bf - gray) * (1 + saturation)

        return self._clamp255(rf * 255), self._clamp255(gf * 255), self._clamp255(bf * 255)

    def _box_smooth(self, image: SimpleImage, rounds: int = 1) -> SimpleImage:
        current = image
        for _ in range(rounds):
            nxt: list[tuple[int, int, int]] = []
            for y in range(current.height):
                for x in range(current.width):
                    rs = gs = bs = cnt = 0
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < current.height and 0 <= nx < current.width:
                                pr, pg, pb = current.pixels[ny * current.width + nx]
                                rs += pr
                                gs += pg
                                bs += pb
                                cnt += 1
                    nxt.append((rs // cnt, gs // cnt, bs // cnt))
            current = SimpleImage(current.width, current.height, nxt)
        return current

    def _auto_params(self, analysis: AnalysisResult) -> dict[str, float]:
        params = {"brightness": 0.0, "contrast": 0.0, "saturation": 0.0, "skin_smooth": 0.0}
        if analysis.image_type == "portrait":
            params["skin_smooth"] = 0.22
            params["brightness"] += 0.04
        elif analysis.image_type == "landscape":
            params["contrast"] += 0.08
            params["saturation"] += 0.06
        elif analysis.image_type == "product":
            params["contrast"] += 0.12

        if analysis.exposure.state == "under":
            params["brightness"] += 0.12
        elif analysis.exposure.state == "over":
            params["brightness"] -= 0.06
        return params

    def _clamp255(self, value: float) -> int:
        return int(max(0, min(255, round(value))))
