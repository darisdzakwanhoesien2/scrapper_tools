# core/validator.py
import validators
from config.constants import URL_REGEX


def validate_url(url: str) -> dict:
    if not url or not isinstance(url, str):
        return {"ok": False, "error": "URL is empty"}

    if not validators.url(url):
        return {"ok": False, "error": "Invalid URL format"}

    return {"ok": True}