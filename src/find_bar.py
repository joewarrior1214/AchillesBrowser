from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import Qt


class FindBar(QWidget):
    def __init__(self, browser: QWebEngineView, parent=None):
        super().__init__(parent)
        self.browser = browser
        self._build_ui()
        self.hide()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Find in page…")
        self.input.setMinimumWidth(220)
        self.input.textChanged.connect(self._search)
        self.input.returnPressed.connect(self._find_next)

        self.result_label = QLabel("")
        self.result_label.setFixedWidth(80)

        prev_btn = QPushButton("▲")
        prev_btn.setFixedSize(28, 28)
        prev_btn.setToolTip("Previous match")
        prev_btn.clicked.connect(self._find_previous)

        next_btn = QPushButton("▼")
        next_btn.setFixedSize(28, 28)
        next_btn.setToolTip("Next match")
        next_btn.clicked.connect(self._find_next)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setToolTip("Close")
        close_btn.clicked.connect(self._close)

        layout.addWidget(self.input)
        layout.addWidget(self.result_label)
        layout.addWidget(prev_btn)
        layout.addWidget(next_btn)
        layout.addStretch()
        layout.addWidget(close_btn)

    # --- Public API expected by BrowserWindow ---

    def focus(self):
        self.input.setFocus()
        self.input.selectAll()

    # --- Internal helpers ---

    def _search(self, text: str):
        self.browser.findText(text, QWebEnginePage.FindFlag(0),
                              self._on_find_result)

    def _find_next(self):
        self.browser.findText(self.input.text(), QWebEnginePage.FindFlag(0),
                              self._on_find_result)

    def _find_previous(self):
        self.browser.findText(
            self.input.text(),
            QWebEnginePage.FindFlag.FindBackward,
            self._on_find_result,
        )

    def _on_find_result(self, result):
        if hasattr(result, 'numberOfMatches'):
            n = result.numberOfMatches()
            self.result_label.setText(f"{n} match{'es' if n != 1 else ''}" if n else "No matches")
        else:
            self.result_label.setText("")

    def _close(self):
        self.browser.findText("")  # Clear highlights
        self.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._close()
        else:
            super().keyPressEvent(event)
