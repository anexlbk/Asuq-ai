"""Jinja2 template filters for safe HTML rendering."""

import re
from urllib.parse import urlparse, quote


_SAFE_SCHEMES = frozenset({"http", "https", "mailto", "tel"})
_JAVASCRIPT_RE = re.compile(r"^\s*javascript:", re.IGNORECASE)


def safe_url(url: str) -> str:
    """Sanitize a URL to prevent XSS from javascript: URLs.

    Usage in Jinja2:
        from app.utils.template_filters import safe_url
        env.filters["safe_url"] = safe_url
    """
    if not url:
        return ""
    if _JAVASCRIPT_RE.match(url):
        return "#blocked"
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.scheme not in _SAFE_SCHEMES:
            return "#blocked"
    except Exception:
        return "#blocked"
    return url
