from __future__ import annotations

from dataclasses import dataclass

from .image_io import SimpleImage
from .models import AnalysisResult, ExposureInfo, FaceInfo, LightingInfo, QualityInfo


@dataclass(slots=True)
class Analyzer:
    """Rule-based analyzer for MVP (stdlib-only)."""

    def analyze(self, image: SimpleImage) -> AnalysisResult:
        gray_values = [(0.299 * r + 0.587 * g + 0.114 * b) for r, g, b in image.pixels]
        brightness = sum(gray_values) / (len(gray_values) * 255.0)
        mean = sum(gray_values) / len(gray_values)
        variance = sum((v - mean) ** 2 for v in gray_values) / max(1, len(gray_values))
        std = (variance**0.5) / 255.0

        clipped_dark = sum(v < 8 for v in gray_values) / len(gray_values)
        clipped_bright = sum(v > 247 for v in gray_values) / len(gray_values)

        ev = (brightness - 0.5) * 2
        exposure_state = "under" if brightness < 0.35 else "over" if brightness > 0.72 else "normal"
        dynamic_range = "low" if std < 0.12 else "mid" if std < 0.23 else "high"

        warm_score = sum((r - b) for r, _, b in image.pixels) / (len(image.pixels) * 255.0)
        wb_shift = max(-0.3, min(0.3, warm_score))
        cct = int(5600 - wb_shift * 4000)

        if clipped_bright > 0.2:
            light_type = "back"
        elif std < 0.1:
            light_type = "diffuse"
        else:
            light_type = "front"

        noise = "high" if clipped_dark > 0.25 else "mid" if clipped_dark > 0.1 else "low"

        edge_energy = 0.0
        for y in range(image.height - 1):
            for x in range(image.width - 1):
                i = y * image.width + x
                g0 = gray_values[i]
                g1 = gray_values[i + 1]
                g2 = gray_values[i + image.width]
                edge_energy += abs(g0 - g1) + abs(g0 - g2)
        edge_energy /= max(1, (image.width - 1) * (image.height - 1))
        blur = "high" if edge_energy < 10 else "mid" if edge_energy < 22 else "low"

        image_type = self._guess_image_type(image, brightness, std)
        mood = self._guess_mood(wb_shift, std)

        faces: list[FaceInfo] = []
        if image_type == "portrait":
            faces = [
                FaceInfo(
                    bbox=[image.width // 4, image.height // 5, image.width // 2, (image.height * 3) // 5],
                    age_group="adult",
                    gender="unknown",
                )
            ]

        return AnalysisResult(
            image_type=image_type,
            lighting=LightingInfo(type=light_type, cct=cct, wb_shift=float(wb_shift)),
            exposure=ExposureInfo(state=exposure_state, ev=float(ev), dynamic_range=dynamic_range),
            quality=QualityInfo(noise=noise, blur=blur),
            mood=mood,
            faces=faces,
        )

    def _guess_image_type(self, image: SimpleImage, brightness: float, std: float) -> str:
        ratio = image.width / max(1, image.height)
        sat = self._saturation(image)
        if 0.7 < ratio < 1.4 and brightness > 0.35 and sat < 0.35:
            return "portrait"
        if sat > 0.45 and std > 0.2:
            return "food"
        if ratio > 1.4:
            return "landscape"
        if brightness > 0.8 and sat < 0.2:
            return "product"
        return "landscape"

    def _guess_mood(self, wb_shift: float, std: float) -> str:
        if wb_shift > 0.05:
            return "warm"
        if wb_shift < -0.05:
            return "cool"
        return "lively" if std > 0.18 else "calm"

    def _saturation(self, image: SimpleImage) -> float:
        sat_sum = 0.0
        for r, g, b in image.pixels:
            max_c = max(r, g, b)
            min_c = min(r, g, b)
            sat_sum += 0.0 if max_c == 0 else (max_c - min_c) / max_c
        return sat_sum / max(1, len(image.pixels))
