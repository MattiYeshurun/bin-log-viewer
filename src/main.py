import sys
from pathlib import Path

import flet as ft

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gui.app_layout import main as gui_main


def main() -> None:
    print("Launching the Bin Log Viewer & Map GUI...")
    ft.run(gui_main)


if __name__ == "__main__":
    main()
