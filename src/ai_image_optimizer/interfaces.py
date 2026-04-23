from __future__ import annotations

from typing import Protocol

from .image_io import SimpleImage


class PortraitRetouchEngine(Protocol):
    def enhance_skin(self, image: SimpleImage, intensity: float) -> SimpleImage: ...

    def enhance_face_details(self, image: SimpleImage, intensity: float) -> SimpleImage: ...


class SceneEnhanceEngine(Protocol):
    def hdr(self, image: SimpleImage, intensity: float) -> SimpleImage: ...

    def color_boost(self, image: SimpleImage, intensity: float) -> SimpleImage: ...


class ColorMatchEngine(Protocol):
    def match_reference(self, image: SimpleImage, reference: SimpleImage, strength: float) -> SimpleImage: ...
