from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from transcriber_tool.config import AppConfig
from transcriber_tool.exporters import export_docx, export_markdown, export_txt, render_lines
from transcriber_tool.models import ProgressUpdate, TranscriptSegment
from transcriber_tool.pipeline import TranscriptionPipeline
from transcriber_tool.utils import has_supported_media_ext


class AppUI:
    def __init__(self, root: tk.Tk, config: AppConfig) -> None:
        self.root = root
        self.config = config
        self.pipeline = TranscriptionPipeline(config)
        self.segments: list[TranscriptSegment] = []
        self.current_job_key = ""

        root.title("视频音频转文字工具")
        root.geometry("1080x760")

        self.file_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.language_var = tk.StringVar(value=config.settings.language)
        self.output_var = tk.StringVar(value=config.settings.output_format)
        self.timestamp_var = tk.StringVar(value=config.settings.timestamp_format)
        self.title_var = tk.StringVar(value="转录结果")
        self.progress_text_var = tk.StringVar(value="进度: 0%")

        self._build_layout()
        self._show_first_run_hint()
        self._schedule_autosave()

    def _build_layout(self) -> None:
        pad = {"padx": 10, "pady": 6}

        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)
        ttk.Label(top, text="视频音频转文字工具", font=("Arial", 14, "bold")).pack(side="left")
        ttk.Button(top, text="设置", command=self.open_settings).pack(side="right", padx=4)
        ttk.Button(top, text="帮助", command=self.show_help).pack(side="right", padx=4)

        source_frame = ttk.LabelFrame(self.root, text="输入源")
        source_frame.pack(fill="x", **pad)

        ttk.Label(source_frame, text="本地文件:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(source_frame, textvariable=self.file_var, width=88).grid(row=0, column=1, **pad)
        ttk.Button(source_frame, text="选择文件", command=self.pick_file).grid(row=0, column=2, **pad)
        ttk.Button(source_frame, text="批量添加", command=self.pick_multi_files).grid(row=0, column=3, **pad)

        ttk.Label(source_frame, text="在线视频URL:").grid(row=1, column=0, sticky="w", **pad)
        ttk.Entry(source_frame, textvariable=self.url_var, width=88).grid(row=1, column=1, columnspan=2, **pad)

        self.batch_box = tk.Listbox(source_frame, height=4)
        self.batch_box.grid(row=2, column=0, columnspan=4, sticky="ew", padx=10, pady=4)

        options = ttk.Frame(self.root)
        options.pack(fill="x", **pad)

        ttk.Label(options, text="语言").pack(side="left")
        ttk.Combobox(options, textvariable=self.language_var, values=["auto", "zh", "en", "ja", "ko"], width=10).pack(side="left", padx=6)
        ttk.Label(options, text="时间戳").pack(side="left")
        ttk.Combobox(options, textvariable=self.timestamp_var, values=["mm:ss", "hh:mm:ss"], width=10).pack(side="left", padx=6)
        ttk.Label(options, text="导出格式").pack(side="left")
        ttk.Combobox(options, textvariable=self.output_var, values=["markdown", "txt", "docx"], width=12).pack(side="left", padx=6)

        ttk.Button(options, text="开始提取", command=self.start_transcribe).pack(side="right")

        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(fill="x", **pad)
        self.progress = ttk.Progressbar(progress_frame, maximum=100)
        self.progress.pack(fill="x", side="left", expand=True)
        ttk.Label(progress_frame, textvariable=self.progress_text_var).pack(side="left", padx=8)

        edit_frame = ttk.LabelFrame(self.root, text="转录结果（可编辑）")
        edit_frame.pack(fill="both", expand=True, **pad)

        toolbar = ttk.Frame(edit_frame)
        toolbar.pack(fill="x")
        ttk.Label(toolbar, text="标题").pack(side="left")
        ttk.Entry(toolbar, textvariable=self.title_var, width=40).pack(side="left", padx=6)
        ttk.Button(toolbar, text="查找替换", command=self.find_replace_dialog).pack(side="right")
        ttk.Button(toolbar, text="导出", command=self.export).pack(side="right", padx=6)

        self.text = tk.Text(edit_frame, undo=True, wrap="word")
        self.text.pack(fill="both", expand=True, padx=8, pady=8)

    def _show_first_run_hint(self) -> None:
        messagebox.showinfo(
            "首次使用说明",
            "1) 选择文件或链接\n2) 点击开始提取\n3) 编辑校正后导出\n\n可在设置中开启说话人/性别标签。",
        )

    def show_help(self) -> None:
        messagebox.showinfo(
            "帮助",
            "支持本地文件和视频链接转录。\n支持说话人分离与可选性别标签（实验性）。\n支持 markdown/txt/docx 导出。",
        )

    def pick_file(self) -> None:
        path = filedialog.askopenfilename(title="选择视频/音频文件")
        if path:
            self.file_var.set(path)

    def pick_multi_files(self) -> None:
        paths = filedialog.askopenfilenames(title="选择多个视频/音频文件")
        for p in paths:
            if p and has_supported_media_ext(Path(p)):
                self.batch_box.insert(tk.END, p)

    def open_settings(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("设置")
        win.geometry("560x380")

        engine_mode = tk.StringVar(value=self.config.settings.engine_mode)
        model_size = tk.StringVar(value=self.config.settings.whisper_model_size)
        device = tk.StringVar(value=self.config.settings.device)
        segment_seconds = tk.StringVar(value=str(self.config.settings.segment_seconds))
        api_base = tk.StringVar(value=self.config.settings.api_base_url)
        api_key = tk.StringVar(value=self.config.settings.api_key)
        diarization = tk.BooleanVar(value=self.config.settings.enable_speaker_diarization)
        gender = tk.BooleanVar(value=self.config.settings.enable_gender_label)
        hf_token = tk.StringVar(value=self.config.settings.hf_token)

        form = ttk.Frame(win)
        form.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(form, text="识别引擎").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Combobox(form, textvariable=engine_mode, values=["local_whisper", "cloud_openai"], width=24).grid(row=0, column=1, sticky="w")

        ttk.Label(form, text="Whisper 模型").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(form, textvariable=model_size, values=["tiny", "base", "small", "medium", "large-v3"], width=24).grid(row=1, column=1, sticky="w")

        ttk.Label(form, text="设备").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Combobox(form, textvariable=device, values=["auto", "cpu", "cuda"], width=24).grid(row=2, column=1, sticky="w")

        ttk.Label(form, text="切片秒数").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=segment_seconds, width=26).grid(row=3, column=1, sticky="w")

        ttk.Checkbutton(form, text="启用说话人分离", variable=diarization).grid(row=4, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Checkbutton(form, text="启用男女标签（实验性）", variable=gender).grid(row=5, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Label(form, text="HF Token(用于说话人分离)").grid(row=6, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=hf_token, width=38, show="*").grid(row=6, column=1, sticky="w")

        ttk.Label(form, text="API Base URL").grid(row=7, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=api_base, width=38).grid(row=7, column=1, sticky="w")

        ttk.Label(form, text="API Key").grid(row=8, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=api_key, width=38, show="*").grid(row=8, column=1, sticky="w")

        def save_settings() -> None:
            self.config.settings.engine_mode = engine_mode.get()
            self.config.settings.whisper_model_size = model_size.get()
            self.config.settings.device = device.get()
            self.config.settings.segment_seconds = max(30, int(segment_seconds.get()))
            self.config.settings.enable_speaker_diarization = bool(diarization.get())
            self.config.settings.enable_gender_label = bool(gender.get())
            self.config.settings.hf_token = hf_token.get().strip()
            self.config.settings.api_base_url = api_base.get().strip()
            self.config.settings.api_key = api_key.get().strip()
            self.config.save()
            self.pipeline.rebuild_engine()
            messagebox.showinfo("设置", "已保存")
            win.destroy()

        ttk.Button(form, text="保存", command=save_settings).grid(row=9, column=1, sticky="e", pady=10)

    def start_transcribe(self) -> None:
        queue: list[str] = []
        file_path = self.file_var.get().strip()
        if file_path:
            queue.append(file_path)
        for i in range(self.batch_box.size()):
            queue.append(self.batch_box.get(i))

        url = self.url_var.get().strip()
        if url:
            queue.append(url)

        if not queue:
            messagebox.showerror("错误", "请先选择本地文件或输入在线视频链接")
            return

        self.config.settings.language = self.language_var.get()
        self.config.settings.timestamp_format = self.timestamp_var.get()
        self.config.settings.output_format = self.output_var.get()
        self.config.save()

        thread = threading.Thread(target=self._run_queue, args=(queue,), daemon=True)
        thread.start()

    def _run_queue(self, queue: list[str]) -> None:
        all_lines: list[str] = []
        for idx, source in enumerate(queue):
            is_url = source.startswith("http://") or source.startswith("https://")
            if not is_url and not has_supported_media_ext(Path(source)):
                continue
            self.current_job_key = Path(source).stem if not is_url else f"url_{idx + 1}"
            self._update_progress(ProgressUpdate(percent=1, eta_seconds=None, message=f"任务 {idx + 1}/{len(queue)}"))
            segments = self.pipeline.run(source=source, is_url=is_url, progress_cb=self._update_progress)
            self.segments = segments
            text_lines = render_lines(segments, self.config.settings.timestamp_format, include_timestamps=True)
            all_lines.append(f"\n===== 来源: {source} =====")
            all_lines.extend(text_lines)
            self._render_text("\n".join(all_lines))

        self._update_progress(ProgressUpdate(percent=100, eta_seconds=0, message="全部完成"))

    def _render_text(self, content: str) -> None:
        def write() -> None:
            self.text.delete("1.0", tk.END)
            self.text.insert(tk.END, content)

        self.root.after(0, write)

    def _update_progress(self, update: ProgressUpdate) -> None:
        def render() -> None:
            self.progress["value"] = update.percent
            eta = ""
            if update.eta_seconds is not None:
                eta = f" 预计剩余: {int(update.eta_seconds // 60)}分{int(update.eta_seconds % 60)}秒"
            self.progress_text_var.set(f"进度: {update.percent:.1f}% {update.message}{eta}")

        self.root.after(0, render)

    def _schedule_autosave(self) -> None:
        self.autosave_draft()
        self.root.after(10000, self._schedule_autosave)

    def autosave_draft(self) -> None:
        if not self.current_job_key:
            return
        content = self.text.get("1.0", tk.END).strip()
        if not content:
            return
        draft_file = self.config.drafts_dir / f"{self.current_job_key}.md"
        draft_file.write_text(content, encoding="utf-8")

    def find_replace_dialog(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("查找替换")
        win.geometry("420x150")

        find_var = tk.StringVar()
        repl_var = tk.StringVar()

        ttk.Label(win, text="查找").pack(anchor="w", padx=8, pady=4)
        ttk.Entry(win, textvariable=find_var).pack(fill="x", padx=8)
        ttk.Label(win, text="替换").pack(anchor="w", padx=8, pady=4)
        ttk.Entry(win, textvariable=repl_var).pack(fill="x", padx=8)

        def apply_replace() -> None:
            src = find_var.get()
            dst = repl_var.get()
            content = self.text.get("1.0", tk.END)
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", content.replace(src, dst))

        ttk.Button(win, text="全部替换", command=apply_replace).pack(pady=8)

    def export(self) -> None:
        fmt = self.output_var.get()
        title = self.title_var.get().strip() or "转录结果"
        include_timestamps = messagebox.askyesno("导出选项", "是否保留时间戳？")

        lines = render_lines(self.segments, self.config.settings.timestamp_format, include_timestamps)
        suffix = {"markdown": ".md", "txt": ".txt", "docx": ".docx"}[fmt]
        path = filedialog.asksaveasfilename(defaultextension=suffix, filetypes=[("All", "*")])
        if not path:
            return

        out = Path(path)
        if fmt == "markdown":
            export_markdown(out, title, lines)
        elif fmt == "txt":
            export_txt(out, title, lines)
        else:
            export_docx(out, title, lines)

        messagebox.showinfo("导出成功", f"已保存到: {out}")
