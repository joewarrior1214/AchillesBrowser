import json
import os
from datetime import datetime
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QLineEdit,
    QMessageBox
)


class BookmarkManager:
    def __init__(self, data_dir):
        self.file_path = os.path.join(data_dir, "bookmarks.json")
        self.bookmarks = self.load()

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
            json.dump(self.bookmarks, f, indent=2)

    def add_bookmark(self, url, title):
        bookmark = {
            "url": url,
            "title": title,
            "added": datetime.now().isoformat()
        }
        self.bookmarks.append(bookmark)
        self.save()

    def remove_bookmark(self, url):
        self.bookmarks = [b for b in self.bookmarks if b["url"] != url]
        self.save()

    def is_bookmarked(self, url):
        return any(b["url"] == url for b in self.bookmarks)

    def create_dialog(self, parent):
        return BookmarkDialog(self, parent)


class BookmarkDialog(QDialog):
    bookmark_selected = pyqtSignal(str)

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Bookmarks")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search bookmarks...")
        self.search_bar.textChanged.connect(self.filter_bookmarks)
        layout.addWidget(self.search_bar)

        # Bookmark list
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_selected)
        layout.addWidget(self.list_widget)

        # Buttons
        btn_layout = QHBoxLayout()
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.open_selected)
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.delete_selected)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)

        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.populate_list()

    def populate_list(self, filter_text=""):
        self.list_widget.clear()
        for bookmark in reversed(self.manager.bookmarks):
            title = bookmark.get("title", "Untitled")
            url = bookmark.get("url", "")
            if filter_text and filter_text.lower() not in (
                title + url
            ).lower():
                continue
            item = QListWidgetItem(f"{title}\n{url}")
            item.setData(256, url)  # Store URL in custom role
            self.list_widget.addItem(item)

    def filter_bookmarks(self, text):
        self.populate_list(text)

    def on_item_selected(self, item):
        url = item.data(256)
        if url:
            self.bookmark_selected.emit(url)
            self.close()

    def open_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self.on_item_selected(item)

    def delete_selected(self):
        item = self.list_widget.currentItem()
        if item:
            url = item.data(256)
            self.manager.remove_bookmark(url)
            self.populate_list()
