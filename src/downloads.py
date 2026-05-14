import os
from PyQt6.QtCore import QStandardPaths
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest


class DownloadManager:
    def __init__(self, parent):
        self.parent = parent
        self.active_downloads = []

    def handle_download(self, download: QWebEngineDownloadRequest):
        # Get suggested filename
        suggested = download.downloadFileName()

        # Ask user where to save
        download_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DownloadLocation
        )
        default_path = os.path.join(download_dir, suggested)

        save_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Save File",
            default_path,
            "All Files (*)"
        )

        if save_path:
            download.setDownloadDirectory(os.path.dirname(save_path))
            download.setDownloadFileName(os.path.basename(save_path))
            download.accept()

            # Track progress
            download.receivedBytesChanged.connect(
                lambda: self.on_progress(download)
            )
            download.isFinishedChanged.connect(
                lambda: self.on_finished(download, save_path)
            )

            self.active_downloads.append(download)
            self.parent.status.showMessage(f"Downloading: {suggested}")
        else:
            download.cancel()

    def on_progress(self, download):
        received = download.receivedBytes()
        total = download.totalBytes()
        if total > 0:
            percent = int((received / total) * 100)
            self.parent.status.showMessage(
                f"Downloading: {percent}% "
                f"({received // 1024}KB / {total // 1024}KB)"
            )

    def on_finished(self, download, path):
        if download in self.active_downloads:
            self.active_downloads.remove(download)

        filename = os.path.basename(path)
        self.parent.status.showMessage(
            f"Download complete: {filename}", 5000
        )
