# tests/test_storage.py
from services.storage_service import StorageService

def test_save_load():
    s = StorageService()
    sample = {"a": 1}
    s.save_processed("test.json", [sample])
    loaded = s.load_processed("test.json")
    assert loaded[0]["a"] == 1