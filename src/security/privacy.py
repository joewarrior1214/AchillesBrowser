from PyQt6.QtWebEngineCore import QWebEngineProfile


class PrivacyManager:
    def __init__(self, profile: QWebEngineProfile):
        self.profile = profile

    def clear_cookies(self):
        self.profile.cookieStore().deleteAllCookies()

    def clear_cache(self):
        self.profile.clearHttpCache()

    def clear_history(self):
        self.profile.clearAllVisitedLinks()

    def clear_all(self):
        self.clear_cookies()
        self.clear_cache()
        self.clear_history()
        print("[Privacy] All browsing data cleared")
