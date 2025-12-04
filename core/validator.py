from urllib.parse import urlparse

def validate_url(url: str):
    if not url:
        return {"ok": False, "error": "URL is empty"}

    try:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return {"ok": True}
        return {"ok": False, "error": "Invalid URL format"}
    except:
        return {"ok": False, "error": "Invalid URL"}
