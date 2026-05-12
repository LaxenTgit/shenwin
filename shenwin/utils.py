"""
Utility functions for Shenwin.
"""

import urllib.request
import socket
from typing import Optional


def create_opener(proxy: Optional[str] = None, timeout: int = 10):
    """
    Create urllib opener with optional proxy and default headers.
    """
    handlers = []
    
    if proxy:
        proxy_handler = urllib.request.ProxyHandler({
            'http': proxy,
            'https': proxy
        })
        handlers.append(proxy_handler)
    
    # Default SSL context (allows us to customize later)
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # Some sites have cert issues
    
    https_handler = urllib.request.HTTPSHandler(context=ctx)
    handlers.append(https_handler)
    
    opener = urllib.request.build_opener(*handlers)
    
    # Default headers
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        ('Accept-Language', 'en-US,en;q=0.5'),
        ('Accept-Encoding', 'identity'),
        ('Connection', 'keep-alive'),
    ]
    
    return opener


def normalize_username(username: str) -> str:
    """
    Normalize username for URL usage.
    - Lowercase
    - Remove leading @
    - URL encode special chars
    """
    username = username.lower().strip().lstrip("@")
    
    # Basic URL encoding for special chars
    import urllib.parse
    return urllib.parse.quote(username, safe='-_.~')


def is_valid_username(username: str) -> bool:
    """Basic username validation."""
    if not username or len(username) > 50:
        return False
    # Most platforms allow: a-z, 0-9, _, -, .
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-./")
    return all(c in allowed for c in username.lower())


def format_time(seconds: float) -> str:
    """Format seconds to human readable."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.0f}s"


def chunk_list(lst: list, chunk_size: int):
    """Split list into chunks."""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def retry_on_error(func, max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry function on network errors.
    """
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_error = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (socket.timeout, urllib.error.URLError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
        raise last_error
    
    return wrapper
