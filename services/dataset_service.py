from services.storage_service import StorageService
from core.merger import dedupe_by_key

class DatasetService:
    def __init__(self):
        self.storage = StorageService()
        self.records = self.storage.load()

    def merge(self, new_data):
        if isinstance(new_data, dict):
            new_data = [new_data]

        merged, added, deduped = dedupe_by_key(self.records, new_data)
        self.records = merged
        self.storage.save(self.records)

        return {"added": added, "deduped": deduped}

    def get(self):
        return self.records
