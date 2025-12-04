# tests/test_scraper.py
from core.validator import validate_url


def test_validate():
    ok = validate_url("https://example.com")
    assert ok["ok"]
    bad = validate_url("notaurl")
    assert not bad["ok"]