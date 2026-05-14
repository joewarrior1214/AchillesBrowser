import json
import os
from datetime import datetime
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLineEdit
)


class HistoryManager:
    def __init__(self, data_dir):
        self.file_path = os.path.join(data_dir, "history.json")
        self.max_entries = 1000
        self.history = self.load()

    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.history[-self.max_entries:], f, indent=2)

    def add_entry(self, url, title):
        # Don't record empty or special URLs
        if not url or url in ("about:blank", ""):
            return

        entry = {
            "url": url,
            "title": title or url,
            "visited": datetime.now().isoformat()
        }
        self.history.append(entry)

        # Trim if too large
        if len(self.history) > self.max_entries:
            self.history = self.history[-self.max_entries:]

    def clear(self):
        self.history = []
        self.save()

    def create_dialog(self, parent):
        return HistoryDialog(self, parent)


class HistoryDialog(QDialog):
    url_selected = pyqtSignal(str)

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Browsing History")
        self.setMinimumSize(600, 450)

        layout = QVBoxLayout()

        # Search
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search history...")
        self.search_bar.textChanged.connect(self.filter_history)
        layout.addWidget(self.search_bar)

        # List
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_selected)
        layout.addWidget(self.list_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_selected)
        clear_btn = QPushButton("Clear All History")
        clear_btn.clicked.connect(self.clear_all)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.populate_list()

    def populate_list(self, filter_text=""):
        self.list_widget.clear()
        for entry in reversed(self.manager.history):
            title = entry.get("title", "Untitled")
            url = entry.get("url", "")
            visited = entry.get("visited", "")[:16].replace("T", " ")

            if filter_text and filter_text.lower() not in (
                title + url
            ).lower():
                continue

            item = QListWidgetItem(f"{title}\n{url}\n{visited}")
            item.setData(256, url)
            self.list_widget.addItem(item)

    def filter_history(self, text):
        self.populate_list(text)

    def on_item_selected(self, item):
        url = item.data(256)
        if url:
            self.url_selected.emit(url)
            self.close()

    def open_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self.on_item_selected(item)

    def clear_all(self):
        self.manager.clear()
        self.populate_list()
