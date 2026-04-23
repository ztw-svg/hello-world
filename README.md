# 视频/音频转文字工具（完整交付版）

一个可本地优先运行的桌面应用，支持：
- 本地视频/音频文件转文字
- 在线视频链接下载并转录（`yt-dlp`）
- 本地 Whisper（`faster-whisper`）或云端 OpenAI 转录
- 说话人分离（Speaker A/B）与可选男女标签（实验性）
- 长音频自动切片、断点续跑（checkpoint）
- 可编辑结果、查找替换、自动草稿保存
- 导出 Markdown / TXT / DOCX
- Windows / macOS 打包脚本

## 一、安装

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

系统工具：
- `ffmpeg`（需包含 `ffprobe`）
- `yt-dlp`

> 若启用说话人分离，需要配置 Hugging Face Token（用于 `pyannote/speaker-diarization-3.1`）。

## 二、启动

```bash
python app.py
```

## 三、使用说明

1. 选择本地文件、批量文件，或粘贴视频链接。
2. 在设置中可启用“说话人分离”和“男女标签”。
3. 点击“开始提取”。
4. 在编辑区修正文稿，支持查找替换。
5. 导出 `.md/.txt/.docx`，可选是否保留时间戳。

## 四、设置页能力

- 识别引擎：`local_whisper` / `cloud_openai`
- Whisper 模型大小：tiny/base/small/medium/large-v3
- 设备：auto/cpu/cuda
- 分片长度（秒）
- 说话人分离开关
- 男女标签开关（实验性）
- HF Token（用于 pyannote 说话人分离）
- API Base URL / API Key

## 五、打包

### Windows
```bat
scripts\build_windows.bat
```

### macOS
```bash
./scripts/build_macos.sh
```

构建后产物位于 `dist/TranscriberTool`。

## 六、说明与限制

- 无法识别片段会标记 `[无法识别]`。
- 默认不做内容过滤，完整输出识别结果。
- 说话人分离依赖外部模型下载，首次运行较慢。
- 男女标签是基于音高的近似估计，仅供参考。
