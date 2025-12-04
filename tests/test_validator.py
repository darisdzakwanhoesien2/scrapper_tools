# tests/test_validator.py
from core.validator import validate_url


def test_empty():
    r = validate_url("")
    assert not r["ok"]