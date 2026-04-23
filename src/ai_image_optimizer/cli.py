from __future__ import annotations

import argparse
import json
from pathlib import Path

from .batch import BatchItem, BatchProcessor
from .pipeline import ImageOptimizationPipeline
from .image_io import supported_extensions
from .presets import export_preset, import_preset, list_presets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI image optimizer MVP CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    optimize = sub.add_parser("optimize", help="optimize one image")
    optimize.add_argument("input", type=Path)
    optimize.add_argument("output", type=Path)
    optimize.add_argument("--preset", type=str, default=None)
    optimize.add_argument("--strength", type=float, default=1.0)

    analyze = sub.add_parser("analyze", help="analyze one image")
    analyze.add_argument("input", type=Path)

    batch = sub.add_parser("batch", help="batch optimize images")
    batch.add_argument("input_dir", type=Path)
    batch.add_argument("output_dir", type=Path)
    batch.add_argument("--preset", type=str, default=None)
    batch.add_argument("--strength", type=float, default=1.0)

    presets = sub.add_parser("presets", help="list presets")
    presets.add_argument("--export", type=str, default=None)
    presets.add_argument("--to", type=Path, default=None)
    presets.add_argument("--import-file", type=Path, default=None)

    sub.add_parser("gui", help="launch desktop GUI")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        from .analyzer import Analyzer
        from .image_io import read_image

        result = Analyzer().analyze(read_image(args.input)).to_dict()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.command == "optimize":
        pipe = ImageOptimizationPipeline()
        result = pipe.run(args.input, args.output, preset_name=args.preset, strength=args.strength)
        print(json.dumps({"output": str(result.output_path), "analysis": result.analysis.to_dict()}, ensure_ascii=False, indent=2))
        return

    if args.command == "batch":
        items = [
            BatchItem(path, args.output_dir / path.name)
            for path in sorted(args.input_dir.iterdir())
            if path.suffix.lower() in supported_extensions()
        ]
        results = BatchProcessor().process(items, preset_name=args.preset, strength=args.strength)
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if args.command == "gui":
        from .gui import main as gui_main

        gui_main()
        return

    if args.command == "presets":
        if args.export:
            if not args.to:
                raise SystemExit("--to is required with --export")
            export_preset(args.export, args.to)
            print(f"Exported: {args.export} -> {args.to}")
            return
        if args.import_file:
            params = import_preset(args.import_file)
            print(json.dumps(params, ensure_ascii=False, indent=2))
            return
        print("\n".join(list_presets()))
        return


if __name__ == "__main__":
    main()
