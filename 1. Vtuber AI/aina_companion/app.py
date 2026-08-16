from __future__ import annotations

import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from .ui import MainWindow

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    app.aboutToQuit.connect(window.shutdown)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
