from services.storage_service import StorageService
from core.merger import dedupe_by_key

class DatasetService:
    def __init__(self):
        self.storage = StorageService()
        self.records = self.storage.load()

    # ---------------------------------------------------------
    # CHECK IF URL ALREADY SCRAPED
    # ---------------------------------------------------------
    def has_url(self, url: str) -> bool:
        """Return True if the dataset already contains records from this URL."""
        return any(
            isinstance(r, dict) and r.get("_source_url") == url
            for r in self.records
        )

    # ---------------------------------------------------------
    # MERGE NEW SCRAPED DATA
    # ---------------------------------------------------------
    def merge(self, new_data):
        if isinstance(new_data, dict):
            new_data = [new_data]

        merged, added, deduped = dedupe_by_key(self.records, new_data)

        self.records = merged
        self.storage.save(self.records)

        return {"added": added, "deduped": deduped}

    # ---------------------------------------------------------
    # GET ALL RECORDS
    # ---------------------------------------------------------
    def get(self):
        return self.records


# from services.storage_service import StorageService
# from core.merger import dedupe_by_key

# class DatasetService:
#     def __init__(self):
#         self.storage = StorageService()
#         self.records = self.storage.load()

#     def merge(self, new_data):
#         if isinstance(new_data, dict):
#             new_data = [new_data]

#         merged, added, deduped = dedupe_by_key(self.records, new_data)
#         self.records = merged
#         self.storage.save(self.records)

#         return {"added": added, "deduped": deduped}

#     def get(self):
#         return self.records
