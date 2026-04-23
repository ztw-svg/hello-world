#!/usr/bin/env bash
set -euo pipefail
pyinstaller --noconfirm --clean --name TranscriberTool --windowed app.py
