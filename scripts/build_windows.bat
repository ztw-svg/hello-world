@echo off
setlocal
pyinstaller --noconfirm --clean --name TranscriberTool --windowed app.py
endlocal
