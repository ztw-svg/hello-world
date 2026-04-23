from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from PIL import Image
except ModuleNotFoundError:  # optional dependency
    Image = None  # type: ignore[assignment]


@dataclass(slots=True)
class SimpleImage:
    width: int
    height: int
    pixels: list[tuple[int, int, int]]

    def copy(self) -> "SimpleImage":
        return SimpleImage(self.width, self.height, list(self.pixels))


def supported_extensions() -> set[str]:
    basic = {".ppm"}
    if Image is not None:
        basic |= {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    return basic


def read_image(path: str | Path) -> SimpleImage:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".ppm":
        return _read_ppm(p)
    if Image is None:
        raise ValueError("Install Pillow to read non-PPM files (jpg/png/webp/tiff/bmp)")
    with Image.open(p) as img:
        rgb = img.convert("RGB")
        w, h = rgb.size
        pixels = list(rgb.getdata())
    return SimpleImage(width=w, height=h, pixels=pixels)


def write_image(image: SimpleImage, path: str | Path) -> None:
    p = Path(path)
    suffix = p.suffix.lower()
    p.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".ppm":
        header = f"P6\n{image.width} {image.height}\n255\n".encode("ascii")
        body = bytearray()
        for r, g, b in image.pixels:
            body.extend((r, g, b))
        p.write_bytes(header + body)
        return
    if Image is None:
        raise ValueError("Install Pillow to write non-PPM files (jpg/png/webp/tiff/bmp)")
    img = Image.new("RGB", (image.width, image.height))
    img.putdata(image.pixels)
    img.save(p)


def _read_ppm(path: Path) -> SimpleImage:
    data = path.read_bytes()
    if data.startswith(b"P6"):
        return _read_p6(data)
    if data.startswith(b"P3"):
        return _read_p3(data.decode("ascii"))
    raise ValueError("Unsupported PPM format")


def _read_p3(text: str) -> SimpleImage:
    tokens = [t for t in text.split() if not t.startswith("#")]
    if tokens[0] != "P3":
        raise ValueError("Bad P3 header")
    w, h = int(tokens[1]), int(tokens[2])
    maxv = int(tokens[3])
    if maxv != 255:
        raise ValueError("Only max value 255 supported")
    nums = list(map(int, tokens[4:]))
    pixels = [(nums[i], nums[i + 1], nums[i + 2]) for i in range(0, len(nums), 3)]
    return SimpleImage(w, h, pixels)


def _read_p6(data: bytes) -> SimpleImage:
    lines = data.split(b"\n", 3)
    magic = lines[0]
    dims = lines[1]
    maxv = lines[2]
    body = lines[3]
    if magic != b"P6":
        raise ValueError("Bad P6 header")
    w, h = map(int, dims.split())
    if int(maxv) != 255:
        raise ValueError("Only max value 255 supported")
    raw = list(body[: w * h * 3])
    pixels = [(raw[i], raw[i + 1], raw[i + 2]) for i in range(0, len(raw), 3)]
    return SimpleImage(w, h, pixels)
