from __future__ import annotations

import json
from pathlib import Path

BUILTIN_PRESETS: dict[str, dict[str, float]] = {
    "质感肌": {
        "brightness": 0.03,
        "contrast": 0.08,
        "saturation": -0.03,
        "sharpness": 0.15,
        "skin_smooth": 0.2,
    },
    "奶油肌": {
        "brightness": 0.08,
        "contrast": -0.03,
        "saturation": 0.02,
        "sharpness": -0.08,
        "skin_smooth": 0.45,
    },
    "胶片感": {
        "brightness": -0.02,
        "contrast": 0.12,
        "saturation": -0.06,
        "sharpness": 0.02,
        "skin_smooth": 0.15,
    },
    "清新": {
        "brightness": 0.06,
        "contrast": 0.02,
        "saturation": 0.08,
        "sharpness": 0.06,
        "skin_smooth": 0.2,
    },
    "电商质感": {
        "brightness": 0.04,
        "contrast": 0.15,
        "saturation": 0.01,
        "sharpness": 0.2,
        "skin_smooth": 0.0,
    },
}


def list_presets() -> list[str]:
    return sorted(BUILTIN_PRESETS.keys())


def get_preset(name: str) -> dict[str, float]:
    if name not in BUILTIN_PRESETS:
        raise KeyError(f"Unknown preset: {name}")
    return dict(BUILTIN_PRESETS[name])


def export_preset(name: str, output: str | Path) -> None:
    payload = {"name": name, "params": get_preset(name)}
    Path(output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def import_preset(path: str | Path) -> dict[str, float]:
    content = json.loads(Path(path).read_text(encoding="utf-8"))
    return content["params"]
