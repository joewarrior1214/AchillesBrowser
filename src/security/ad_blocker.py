import os
from PyQt6.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt6.QtCore import QUrl


class AdBlocker(QWebEngineUrlRequestInterceptor):
    def __init__(self, data_dir):
        super().__init__()
        self.blocked_domains = set()
        self.blocked_count = 0
        self.data_dir = data_dir
        self.load_blocklist()

    def load_blocklist(self):
        """Load blocked domains from file"""
        blocklist_path = os.path.join(self.data_dir, "blocklist.txt")

        # Create default blocklist if none exists
        if not os.path.exists(blocklist_path):
            self.create_default_blocklist(blocklist_path)

        try:
            with open(blocklist_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Support hosts file format: "0.0.0.0 domain.com"
                        parts = line.split()
                        if len(parts) >= 2:
                            domain = parts[1].strip()
                        else:
                            domain = parts[0].strip()

                        if domain and domain != "localhost":
                            self.blocked_domains.add(domain)
        except FileNotFoundError:
            pass

        print(f"[AdBlocker] Loaded {len(self.blocked_domains)} blocked domains")

    def create_default_blocklist(self, path):
        """Create a basic blocklist with common ad/tracker domains"""
        default_domains = """# SecureBrowse Ad/Tracker Blocklist
# Add domains to block, one per line
# Format: 0.0.0.0 domain.com

# --- Ads ---
0.0.0.0 doubleclick.net
0.0.0.0 googleadservices.com
0.0.0.0 googlesyndication.com
0.0.0.0 adservice.google.com
0.0.0.0 pagead2.googlesyndication.com
0.0.0.0 ads.youtube.com
0.0.0.0 ad.doubleclick.net
0.0.0.0 adnxs.com
0.0.0.0 adsrvr.org
0.0.0.0 advertising.com
0.0.0.0 outbrain.com
0.0.0.0 taboola.com
0.0.0.0 adcolony.com
0.0.0.0 serving-sys.com

# --- Trackers ---
0.0.0.0 google-analytics.com
0.0.0.0 googletagmanager.com
0.0.0.0 facebook.net
0.0.0.0 connect.facebook.net
0.0.0.0 pixel.facebook.com
0.0.0.0 analytics.twitter.com
0.0.0.0 t.co
0.0.0.0 scorecardresearch.com
0.0.0.0 quantserve.com
0.0.0.0 hotjar.com
0.0.0.0 fullstory.com
0.0.0.0 mouseflow.com
0.0.0.0 clicktale.net
0.0.0.0 mixpanel.com
0.0.0.0 segment.io
0.0.0.0 amplitude.com
0.0.0.0 newrelic.com
0.0.0.0 nr-data.net

# --- Malware / Suspicious ---
0.0.0.0 malware-check.disconnect.me
0.0.0.0 tracking.opencandy.com

# For a comprehensive list, download from:
# https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts
"""
        with open(path, "w") as f:
            f.write(default_domains)

    def interceptRequest(self, info):
        """Intercept and potentially block each request"""
        url = info.requestUrl()
        host = url.host().lower()

        # Check if domain or parent domain is blocked
        if self.should_block(host):
            info.block(True)
            self.blocked_count += 1
            return

    def should_block(self, host):
        """Check if host matches any blocked domain"""
        # Direct match
        if host in self.blocked_domains:
            return True

        # Subdomain match (e.g., block "ads.example.com"
        # if "example.com" is blocked)
        parts = host.split(".")
        for i in range(len(parts) - 1):
            parent = ".".join(parts[i:])
            if parent in self.blocked_domains:
                return True

        return False

    def reset_count(self):
        self.blocked_count = 0
