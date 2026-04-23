from __future__ import annotations

import tkinter as tk
from pathlib import Path

from transcriber_tool.config import AppConfig
from transcriber_tool.ui import AppUI


def main() -> None:
    workspace = Path.home() / ".transcriber_tool"
    config = AppConfig.load(workspace)

    root = tk.Tk()
    AppUI(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
