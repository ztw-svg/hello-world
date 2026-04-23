from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from .pipeline import ImageOptimizationPipeline
from .presets import list_presets


class OptimizerApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("智能图像优化工具 MVP")
        self.root.geometry("860x560")

        self.pipeline = ImageOptimizationPipeline()
        self.input_path: Path | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=12, pady=8)

        tk.Button(top, text="导入图片", command=self._choose_input).pack(side=tk.LEFT)
        tk.Button(top, text="一键智能优化", command=self._run_optimize).pack(side=tk.LEFT, padx=8)

        self.preset_var = tk.StringVar(value=list_presets()[0])
        tk.OptionMenu(top, self.preset_var, *list_presets()).pack(side=tk.LEFT, padx=8)

        self.strength = tk.DoubleVar(value=1.0)
        tk.Scale(top, from_=0.2, to=1.5, resolution=0.1, orient=tk.HORIZONTAL, label="优化强度", variable=self.strength).pack(side=tk.RIGHT)

        self.status = tk.StringVar(value="请先导入图片")
        tk.Label(self.root, textvariable=self.status, anchor="w").pack(fill=tk.X, padx=12)

        self.text = tk.Text(self.root, height=24)
        self.text.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

    def _choose_input(self) -> None:
        path = filedialog.askopenfilename(title="选择图片")
        if path:
            self.input_path = Path(path)
            self.status.set(f"已选择: {self.input_path}")

    def _run_optimize(self) -> None:
        if not self.input_path:
            messagebox.showwarning("提示", "请先导入图片")
            return
        out = self.input_path.with_name(f"{self.input_path.stem}_optimized{self.input_path.suffix}")
        try:
            result = self.pipeline.run(
                input_path=self.input_path,
                output_path=out,
                preset_name=self.preset_var.get(),
                strength=float(self.strength.get()),
            )
            self.status.set(f"处理完成 -> {out}")
            self.text.delete("1.0", tk.END)
            self.text.insert(tk.END, f"分析结果:\n{result.analysis.to_dict()}\n")
        except Exception as exc:
            messagebox.showerror("处理失败", str(exc))

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    OptimizerApp().run()


if __name__ == "__main__":
    main()
