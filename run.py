#!/usr/bin/env python3
"""GameHub — launcher unificado de jogos (PC + emuladores)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

from gamehub.app import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("GameHub")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
