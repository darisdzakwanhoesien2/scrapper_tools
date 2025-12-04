# tests/test_merge.py
from core.merger import dedupe_by_key


def test_dedupe():
    existing = [{"id": "1", "x": 1}]
    new = [{"id": "1", "x": 1}, {"id": "2", "x": 2}]
    merged, added, deduped = dedupe_by_key(existing, new, "id")
    assert added == 1
    assert deduped == 1