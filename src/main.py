import logging
import sys
from pathlib import Path

import flet as ft

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gui.app_layout import main as gui_main

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Launching the Bin Log Viewer & Map GUI...")
    ft.run(gui_main)


if __name__ == "__main__":
    main()
