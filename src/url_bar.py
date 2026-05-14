from PyQt6.QtCore import pyqtSignal, Qt, QUrl
from PyQt6.QtWidgets import QLineEdit, QCompleter
from PyQt6.QtGui import QAction
import re


class SmartUrlBar(QLineEdit):
    url_submitted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setPlaceholderText("Search or enter URL...")
        self.setMinimumHeight(35)
        self.setClearButtonEnabled(True)

        # Connect enter key
        self.returnPressed.connect(self.on_submit)

        # Search engine template
        self.search_template = "https://duckduckgo.com/?q={}"

    def on_submit(self):
        text = self.text().strip()
        if not text:
            return

        url = self.smart_resolve(text)
        self.url_submitted.emit(url)

    def smart_resolve(self, text):
        """Determine if input is a URL or search query"""

        # Already a full URL
        if text.startswith(("http://", "https://", "file://")):
            return text

        # Looks like a domain (contains dot, no spaces)
        if "." in text and " " not in text:
            # Check for common TLDs or IP-like patterns
            if re.match(
                r'^[\w\-]+(\.[\w\-]+)+(:\d+)?(/.*)?$', text
            ):
                return "https://" + text

        # Localhost
        if text.startswith("localhost") or text.startswith("127."):
            return "http://" + text

        # Otherwise treat as search query
        return self.search_template.format(text.replace(" ", "+"))

    def set_url(self, url):
        """Update the URL bar display"""
        if isinstance(url, QUrl):
            url = url.toString()
        self.setText(url)

    def focus_and_select(self):
        """Focus the URL bar and select all text"""
        self.setFocus()
        self.selectAll()

    def keyPressEvent(self, event):
        # Escape clears focus
        if event.key() == Qt.Key.Key_Escape:
            self.clearFocus()
            return
        super().keyPressEvent(event)
