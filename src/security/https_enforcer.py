class HttpsEnforcer:
    """Forces HTTPS on all navigations"""

    # Domains known to not support HTTPS
    EXCEPTIONS = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    }

    def enforce(self, url_string):
        """Convert HTTP URLs to HTTPS"""
        url_string = url_string.strip()

        # Skip local addresses
        for exception in self.EXCEPTIONS:
            if exception in url_string:
                return url_string

        # Force HTTPS
        if url_string.startswith("http://"):
            url_string = url_string.replace("http://", "https://", 1)
        elif not url_string.startswith(("https://", "file://", "about:")):
            if not url_string.startswith("https://"):
                url_string = "https://" + url_string

        return url_string
