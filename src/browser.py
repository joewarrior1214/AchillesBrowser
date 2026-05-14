import json
import os
from PyQt6.QtCore import Qt, QUrl, QSize
from PyQt6.QtGui import QAction, QKeySequence, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QStatusBar, QMenu,
    QMenuBar, QDialog, QVBoxLayout, QLabel,
    QWidget, QHBoxLayout, QPushButton, QSplitter
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEngineSettings, QWebEnginePage
)

from src.tab_manager import TabManager
from src.url_bar import SmartUrlBar
from src.bookmarks import BookmarkManager
from src.history import HistoryManager
from src.downloads import DownloadManager
from src.security.ad_blocker import AdBlocker
from src.security.privacy import PrivacyManager
from src.security.https_enforcer import HttpsEnforcer


class BrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SecureBrowse")
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(800, 600)

        # Data paths
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)

        # Load settings
        self.settings = self.load_settings()

        # Initialize managers
        self.bookmark_manager = BookmarkManager(self.data_dir)
        self.history_manager = HistoryManager(self.data_dir)
        self.download_manager = DownloadManager(self)

        # Configure browser profile (security)
        self.setup_profile()

        # Build UI
        self.setup_ui()
        self.setup_menu_bar()
        self.setup_shortcuts()

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Open default tab
        home_url = self.settings.get("home_page", "https://duckduckgo.com")
        self.tab_manager.add_tab(QUrl(home_url), "Home")

    def load_settings(self):
        settings_path = os.path.join(self.data_dir, "settings.json")
        default_settings = {
            "home_page": "https://duckduckgo.com",
            "search_engine": "https://duckduckgo.com/?q={}",
            "ad_block_enabled": True,
            "https_enforced": True,
            "javascript_enabled": True,
            "auto_clear_on_exit": True,
            "block_third_party_cookies": True,
            "do_not_track": True
        }
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r") as f:
                    loaded = json.load(f)
                    default_settings.update(loaded)
            except Exception:
                pass
        return default_settings

    def save_settings(self):
        settings_path = os.path.join(self.data_dir, "settings.json")
        with open(settings_path, "w") as f:
            json.dump(self.settings, f, indent=2)

    def setup_profile(self):
        self.profile = QWebEngineProfile.defaultProfile()

        # Memory-only cache for privacy
        self.profile.setHttpCacheType(
            QWebEngineProfile.HttpCacheType.MemoryHttpCache
        )

        # Custom user agent
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        # Do Not Track
        if self.settings.get("do_not_track", True):
            self.profile.setHttpAcceptLanguage("en-US,en;q=0.9")

        # Ad blocker
        self.ad_blocker = AdBlocker(self.data_dir)
        if self.settings.get("ad_block_enabled", True):
            self.profile.setUrlRequestInterceptor(self.ad_blocker)

        # HTTPS enforcer
        self.https_enforcer = HttpsEnforcer()

        # Privacy manager
        self.privacy_manager = PrivacyManager(self.profile)

        # Download handler
        self.profile.downloadRequested.connect(
            self.download_manager.handle_download
        )

    def setup_ui(self):
        # Main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Navigation toolbar
        nav_toolbar = QToolBar("Navigation")
        nav_toolbar.setMovable(False)
        nav_toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(nav_toolbar)

        # Back button
        self.back_btn = QPushButton("◀")
        self.back_btn.setFixedSize(35, 35)
        self.back_btn.setToolTip("Back")
        self.back_btn.clicked.connect(self.navigate_back)
        nav_toolbar.addWidget(self.back_btn)

        # Forward button
        self.forward_btn = QPushButton("▶")
        self.forward_btn.setFixedSize(35, 35)
        self.forward_btn.setToolTip("Forward")
        self.forward_btn.clicked.connect(self.navigate_forward)
        nav_toolbar.addWidget(self.forward_btn)

        # Reload button
        self.reload_btn = QPushButton("⟳")
        self.reload_btn.setFixedSize(35, 35)
        self.reload_btn.setToolTip("Reload")
        self.reload_btn.clicked.connect(self.reload_page)
        nav_toolbar.addWidget(self.reload_btn)

        # Home button
        self.home_btn = QPushButton("⌂")
        self.home_btn.setFixedSize(35, 35)
        self.home_btn.setToolTip("Home")
        self.home_btn.clicked.connect(self.go_home)
        nav_toolbar.addWidget(self.home_btn)

        # URL bar
        self.url_bar = SmartUrlBar(self)
        self.url_bar.url_submitted.connect(self.navigate_to_url)
        nav_toolbar.addWidget(self.url_bar)

        # Bookmark button
        self.bookmark_btn = QPushButton("☆")
        self.bookmark_btn.setFixedSize(35, 35)
        self.bookmark_btn.setToolTip("Bookmark this page")
        self.bookmark_btn.clicked.connect(self.toggle_bookmark)
        nav_toolbar.addWidget(self.bookmark_btn)

        # Security indicator
        self.security_btn = QPushButton("🔒")
        self.security_btn.setFixedSize(35, 35)
        self.security_btn.setToolTip("Security Status")
        self.security_btn.clicked.connect(self.show_security_info)
        nav_toolbar.addWidget(self.security_btn)

        # Menu button
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setFixedSize(35, 35)
        self.menu_btn.setToolTip("Menu")
        self.menu_btn.clicked.connect(self.show_main_menu)
        nav_toolbar.addWidget(self.menu_btn)

        # Tab manager
        self.tab_manager = TabManager(self)
        main_layout.addWidget(self.tab_manager)

        # Connect tab signals
        self.tab_manager.url_changed.connect(self.on_url_changed)
        self.tab_manager.title_changed.connect(self.on_title_changed)
        self.tab_manager.loading_started.connect(
            lambda: self.status.showMessage("Loading...")
        )
        self.tab_manager.loading_finished.connect(
            lambda: self.status.showMessage("Done", 2000)
        )

        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def setup_menu_bar(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_action.triggered.connect(
            lambda: self.tab_manager.add_tab(
                QUrl(self.settings.get("home_page", "https://duckduckgo.com")),
                "New Tab"
            )
        )
        file_menu.addAction(new_tab_action)

        close_tab_action = QAction("Close Tab", self)
        close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_action.triggered.connect(self.tab_manager.close_current_tab)
        file_menu.addAction(close_tab_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # View menu
        view_menu = menu_bar.addMenu("&View")

        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut(QKeySequence("Ctrl++"))
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        reset_zoom_action = QAction("Reset Zoom", self)
        reset_zoom_action.setShortcut(QKeySequence("Ctrl+0"))
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)

        view_menu.addSeparator()

        fullscreen_action = QAction("Toggle Fullscreen", self)
        fullscreen_action.setShortcut(QKeySequence("F11"))
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)

        # Bookmarks menu
        bookmarks_menu = menu_bar.addMenu("&Bookmarks")

        show_bookmarks_action = QAction("Show All Bookmarks", self)
        show_bookmarks_action.setShortcut(QKeySequence("Ctrl+B"))
        show_bookmarks_action.triggered.connect(self.show_bookmarks)
        bookmarks_menu.addAction(show_bookmarks_action)

        add_bookmark_action = QAction("Bookmark This Page", self)
        add_bookmark_action.setShortcut(QKeySequence("Ctrl+D"))
        add_bookmark_action.triggered.connect(self.toggle_bookmark)
        bookmarks_menu.addAction(add_bookmark_action)

        # History menu
        history_menu = menu_bar.addMenu("&History")

        show_history_action = QAction("Show History", self)
        show_history_action.setShortcut(QKeySequence("Ctrl+H"))
        show_history_action.triggered.connect(self.show_history)
        history_menu.addAction(show_history_action)

        clear_history_action = QAction("Clear History", self)
        clear_history_action.triggered.connect(self.clear_history)
        history_menu.addAction(clear_history_action)

        # Security menu
        security_menu = menu_bar.addMenu("&Security")

        toggle_adblock = QAction("Toggle Ad Blocker", self)
        toggle_adblock.setCheckable(True)
        toggle_adblock.setChecked(self.settings.get("ad_block_enabled", True))
        toggle_adblock.triggered.connect(self.toggle_ad_blocker)
        security_menu.addAction(toggle_adblock)

        toggle_js = QAction("Toggle JavaScript", self)
        toggle_js.setCheckable(True)
        toggle_js.setChecked(self.settings.get("javascript_enabled", True))
        toggle_js.triggered.connect(self.toggle_javascript)
        security_menu.addAction(toggle_js)

        clear_data_action = QAction("Clear All Browsing Data", self)
        clear_data_action.setShortcut(QKeySequence("Ctrl+Shift+Delete"))
        clear_data_action.triggered.connect(self.clear_all_data)
        security_menu.addAction(clear_data_action)

    def setup_shortcuts(self):
        # Focus URL bar
        focus_url = QAction(self)
        focus_url.setShortcut(QKeySequence("Ctrl+L"))
        focus_url.triggered.connect(self.url_bar.focus_and_select)
        self.addAction(focus_url)

        # Find in page
        find_action = QAction(self)
        find_action.setShortcut(QKeySequence("Ctrl+F"))
        find_action.triggered.connect(self.find_in_page)
        self.addAction(find_action)

        # Reload
        reload_action = QAction(self)
        reload_action.setShortcut(QKeySequence("F5"))
        reload_action.triggered.connect(self.reload_page)
        self.addAction(reload_action)

        # Navigate tabs
        next_tab = QAction(self)
        next_tab.setShortcut(QKeySequence("Ctrl+Tab"))
        next_tab.triggered.connect(self.tab_manager.next_tab)
        self.addAction(next_tab)

        prev_tab = QAction(self)
        prev_tab.setShortcut(QKeySequence("Ctrl+Shift+Tab"))
        prev_tab.triggered.connect(self.tab_manager.previous_tab)
        self.addAction(prev_tab)

    # --- Navigation ---

    def navigate_to_url(self, url_string):
        url_string = self.https_enforcer.enforce(url_string)
        url = QUrl(url_string)
        self.tab_manager.navigate_current(url)

    def navigate_back(self):
        browser = self.tab_manager.current_browser()
        if browser:
            browser.back()

    def navigate_forward(self):
        browser = self.tab_manager.current_browser()
        if browser:
            browser.forward()

    def reload_page(self):
        browser = self.tab_manager.current_browser()
        if browser:
            browser.reload()

    def go_home(self):
        home = self.settings.get("home_page", "https://duckduckgo.com")
        self.tab_manager.navigate_current(QUrl(home))

    # --- URL & Title Updates ---

    def on_url_changed(self, url):
        self.url_bar.set_url(url)
        self.update_security_indicator(url)
        self.update_bookmark_indicator(url)

        # Record history
        browser = self.tab_manager.current_browser()
        title = browser.title() if browser else ""
        self.history_manager.add_entry(url.toString(), title)

    def on_title_changed(self, title):
        if title:
            self.setWindowTitle(f"{title} - SecureBrowse")
        else:
            self.setWindowTitle("SecureBrowse")

    def update_security_indicator(self, url):
        if url.scheme() == "https":
            self.security_btn.setText("🔒")
            self.security_btn.setToolTip("Secure Connection (HTTPS)")
        else:
            self.security_btn.setText("🔓")
            self.security_btn.setToolTip("Insecure Connection")

    def update_bookmark_indicator(self, url):
        if self.bookmark_manager.is_bookmarked(url.toString()):
            self.bookmark_btn.setText("★")
        else:
            self.bookmark_btn.setText("☆")

    # --- Bookmarks ---

    def toggle_bookmark(self):
        browser = self.tab_manager.current_browser()
        if browser:
            url = browser.url().toString()
            title = browser.title()
            if self.bookmark_manager.is_bookmarked(url):
                self.bookmark_manager.remove_bookmark(url)
                self.bookmark_btn.setText("☆")
                self.status.showMessage("Bookmark removed", 2000)
            else:
                self.bookmark_manager.add_bookmark(url, title)
                self.bookmark_btn.setText("★")
                self.status.showMessage("Bookmark added", 2000)

    def show_bookmarks(self):
        dialog = self.bookmark_manager.create_dialog(self)
        dialog.bookmark_selected.connect(
            lambda url: self.tab_manager.navigate_current(QUrl(url))
        )
        dialog.exec()

    # --- History ---

    def show_history(self):
        dialog = self.history_manager.create_dialog(self)
        dialog.url_selected.connect(
            lambda url: self.tab_manager.navigate_current(QUrl(url))
        )
        dialog.exec()

    def clear_history(self):
        self.history_manager.clear()
        self.status.showMessage("History cleared", 2000)

    # --- Security Controls ---

    def toggle_ad_blocker(self, enabled):
        self.settings["ad_block_enabled"] = enabled
        if enabled:
            self.profile.setUrlRequestInterceptor(self.ad_blocker)
            self.status.showMessage("Ad blocker enabled", 2000)
        else:
            self.profile.setUrlRequestInterceptor(None)
            self.status.showMessage("Ad blocker disabled", 2000)
        self.save_settings()

    def toggle_javascript(self, enabled):
        self.settings["javascript_enabled"] = enabled
        browser = self.tab_manager.current_browser()
        if browser:
            browser.settings().setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled,
                enabled
            )
        msg = "JavaScript enabled" if enabled else "JavaScript disabled"
        self.status.showMessage(msg, 2000)
        self.save_settings()

    def clear_all_data(self):
        self.privacy_manager.clear_all()
        self.history_manager.clear()
        self.status.showMessage("All browsing data cleared", 3000)

    def show_security_info(self):
        browser = self.tab_manager.current_browser()
        if not browser:
            return
        url = browser.url()
        blocked = self.ad_blocker.blocked_count
        dialog = QDialog(self)
        dialog.setWindowTitle("Security Info")
        dialog.setFixedSize(350, 250)
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"<b>URL:</b> {url.toString()[:50]}..."))
        layout.addWidget(QLabel(
            f"<b>Protocol:</b> {url.scheme().upper()}"
        ))
        layout.addWidget(QLabel(
            f"<b>Secure:</b> {'Yes ✅' if url.scheme() == 'https' else 'No ❌'}"
        ))
        layout.addWidget(QLabel(f"<b>Ads/Trackers Blocked:</b> {blocked}"))
        layout.addWidget(QLabel(
            f"<b>JavaScript:</b> "
            f"{'Enabled' if self.settings.get('javascript_enabled') else 'Disabled'}"
        ))
        layout.addWidget(QLabel(
            f"<b>Ad Blocker:</b> "
            f"{'Active' if self.settings.get('ad_block_enabled') else 'Inactive'}"
        ))
        dialog.setLayout(layout)
        dialog.exec()

    # --- View Controls ---

    def zoom_in(self):
        browser = self.tab_manager.current_browser()
        if browser:
            browser.setZoomFactor(browser.zoomFactor() + 0.1)

    def zoom_out(self):
        browser = self.tab_manager.current_browser()
        if browser:
            browser.setZoomFactor(max(0.25, browser.zoomFactor() - 0.1))

    def reset_zoom(self):
        browser = self.tab_manager.current_browser()
        if browser:
            browser.setZoomFactor(1.0)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def find_in_page(self):
        browser = self.tab_manager.current_browser()
        if not browser:
            return
        from src.find_bar import FindBar
        if not hasattr(self, 'find_bar'):
            self.find_bar = FindBar(browser, self)
            self.centralWidget().layout().addWidget(self.find_bar)
        self.find_bar.show()
        self.find_bar.focus()

    def show_main_menu(self):
        menu = QMenu(self)
        menu.addAction("New Tab", lambda: self.tab_manager.add_tab(
            QUrl(self.settings.get("home_page")), "New Tab"
        ))
        menu.addAction("Bookmarks", self.show_bookmarks)
        menu.addAction("History", self.show_history)
        menu.addSeparator()
        menu.addAction("Clear Data", self.clear_all_data)
        menu.addSeparator()
        menu.addAction("Quit", self.close)
        menu.exec(self.menu_btn.mapToGlobal(self.menu_btn.rect().bottomLeft()))

    # --- Cleanup ---

    def closeEvent(self, event):
        if self.settings.get("auto_clear_on_exit", True):
            self.privacy_manager.clear_all()
        self.save_settings()
        self.history_manager.save()
        event.accept()
