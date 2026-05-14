import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from src.browser import BrowserWindow


def main():
    # High DPI support
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("SecureBrowse")
    app.setApplicationVersion("1.0.0")

    # Load stylesheet
    style_path = os.path.join(os.path.dirname(__file__), "styles", "dark_theme.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())

    window = BrowserWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
