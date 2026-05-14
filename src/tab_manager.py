from PyQt6.QtCore import pyqtSignal, QUrl
from PyQt6.QtWidgets import QTabWidget, QTabBar
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage


class TabManager(QTabWidget):
    url_changed = pyqtSignal(QUrl)
    title_changed = pyqtSignal(str)
    loading_started = pyqtSignal()
    loading_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setDocumentMode(True)

        # Enable scrollable tabs when many are open
        self.tabBar().setExpanding(False)

        # Signals
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.on_tab_switched)

        # Add tab button
        self.add_tab_btn = QTabBar()
        self.setCornerWidget(self._create_add_button())

    def _create_add_button(self):
        from PyQt6.QtWidgets import QPushButton
        btn = QPushButton("+")
        btn.setFixedSize(30, 30)
        btn.setToolTip("New Tab")
        btn.clicked.connect(lambda: self.add_tab(
            QUrl("https://duckduckgo.com"), "New Tab"
        ))
        return btn

    def add_tab(self, url, title="New Tab"):
        browser = QWebEngineView()

        # Configure settings for this tab
        settings = browser.settings()
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.PluginsEnabled, False
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, False
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True
        )
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True
        )

        # Load URL
        browser.setUrl(url)

        # Add tab
        index = self.addTab(browser, title)
        self.setCurrentIndex(index)

        # Connect signals
        browser.urlChanged.connect(
            lambda u, b=browser: self._on_url_changed(b, u)
        )
        browser.titleChanged.connect(
            lambda t, idx=index, b=browser: self._on_title_changed(b, t)
        )
        browser.loadStarted.connect(self.loading_started.emit)
        browser.loadFinished.connect(self.loading_finished.emit)
        browser.iconChanged.connect(
            lambda icon, b=browser: self._on_icon_changed(b, icon)
        )

        # Handle new window requests (open in new tab instead)
        browser.page().newWindowRequested.connect(
            lambda request: self._handle_new_window(request)
        )

        return index

    def _on_url_changed(self, browser, url):
        if browser == self.current_browser():
            self.url_changed.emit(url)

    def _on_title_changed(self, browser, title):
        index = self.indexOf(browser)
        if index != -1:
            # Truncate long titles
            display_title = title[:25] + "..." if len(title) > 25 else title
            self.setTabText(index, display_title)
            self.setTabToolTip(index, title)
        if browser == self.current_browser():
            self.title_changed.emit(title)

    def _on_icon_changed(self, browser, icon):
        index = self.indexOf(browser)
        if index != -1:
            self.setTabIcon(index, icon)

    def _handle_new_window(self, request):
        self.add_tab(request.requestedUrl(), "New Tab")
        request.openIn(self.current_browser().page())

    def close_tab(self, index):
        if self.count() > 1:
            widget = self.widget(index)
            self.removeTab(index)
            widget.deleteLater()
        elif self.count() == 1:
            # Last tab - navigate to home instead of closing
            self.current_browser().setUrl(QUrl("https://duckduckgo.com"))

    def close_current_tab(self):
        self.close_tab(self.currentIndex())

    def current_browser(self):
        return self.currentWidget()

    def navigate_current(self, url):
        browser = self.current_browser()
        if browser:
            browser.setUrl(url)

    def on_tab_switched(self, index):
        browser = self.current_browser()
        if browser:
            self.url_changed.emit(browser.url())
            self.title_changed.emit(browser.title())

    def next_tab(self):
        current = self.currentIndex()
        if current < self.count() - 1:
            self.setCurrentIndex(current + 1)
        else:
            self.setCurrentIndex(0)

    def previous_tab(self):
        current = self.currentIndex()
        if current > 0:
            self.setCurrentIndex(current - 1)
        else:
            self.setCurrentIndex(self.count() - 1)
