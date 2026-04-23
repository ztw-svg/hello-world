# 部署与打包说明

## 环境
- Python 3.10+
- pip
- ffmpeg/ffprobe

## 安装依赖
```bash
pip install -r requirements.txt
```

## 本地运行
```bash
python app.py
```

## Windows 打包
```bat
scripts\build_windows.bat
```

## macOS 打包
```bash
./scripts/build_macos.sh
```

## 发布清单
- `dist/TranscriberTool/` 可执行目录
- `README.md`
- `docs/USER_GUIDE.md`
- `docs/DEPLOYMENT.md`
