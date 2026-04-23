# 智能图像优化工具（MVP，可运行）

已进入“下一步”实现：在原有 CLI 流程基础上，增加了 GUI 入口与可选 Pillow 后端。

## 当前能力

- 智能图像分析（类型/曝光/光线/噪点/情绪）
- 一键智能优化（自动策略 + 预设叠加 + 强度控制）
- 风格预设系统（内置 5 个预设 + 导入/导出）
- 批量处理（目录扫描、逐张进度）
- CLI + 桌面 GUI（Tkinter）
- 图像格式：
  - 默认离线零依赖：`.ppm`
  - 安装 Pillow 后：`.jpg/.jpeg/.png/.bmp/.tif/.tiff/.webp`

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
# 若需常见格式支持
pip install -e .[imaging]
```

## CLI 用法

```bash
# 分析
aio analyze input.ppm

# 一键优化
aio optimize input.ppm output.ppm --preset "奶油肌" --strength 0.9

# 批量
aio batch ./inputs ./outputs --preset "电商质感"

# 预设
aio presets
aio presets --export "清新" --to ./preset-qingxin.json
aio presets --import-file ./preset-qingxin.json

# GUI
aio gui
```

## 项目结构

```text
src/ai_image_optimizer/
  models.py
  interfaces.py
  image_io.py
  analyzer.py
  optimizer.py
  pipeline.py
  batch.py
  presets.py
  cli.py
  gui.py
tests/
```

## 研发文档

- 架构与分阶段实现方案：`docs/ai-image-optimizer-architecture.md`
