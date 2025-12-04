import json
from pathlib import Path
from datetime import datetime
import re


class StorageService:
    def __init__(self):
        # Raw files saved here
        self.raw_dir = Path("data/raw")
        self.raw_dir.mkdir(parents=True, exist_ok=True)

        # Dataset (merged records)
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        self.dataset_file = self.processed_dir / "dataset.json"

    # ------------------------------
    # Save SCRAPED RESULT file
    # ------------------------------
    def sanitize_filename(self, url: str):
        ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        name = url.split("/")[-1] or "index"
        safe = re.sub(r"[^a-zA-Z0-9-_]", "_", name)
        return f"{ts}_{safe}.json"

    def save_json(self, url: str, data):
        filename = self.sanitize_filename(url)
        filepath = self.raw_dir / filename
        filepath.write_text(json.dumps(data, indent=2))
        return str(filepath)

    # ------------------------------
    # Dataset operations
    # ------------------------------
    def load(self):
        """Load merged dataset records."""
        if not self.dataset_file.exists():
            return []
        return json.loads(self.dataset_file.read_text())

    def save(self, records):
        """Save merged dataset records."""
        self.dataset_file.write_text(json.dumps(records, indent=2))



# import json
# from pathlib import Path

# class StorageService:
#     def __init__(self):
#         self.data_dir = Path("data/processed")
#         self.data_dir.mkdir(parents=True, exist_ok=True)
#         self.file = self.data_dir / "dataset.json"

#     def load(self):
#         if not self.file.exists():
#             return []
#         return json.loads(self.file.read_text())

#     def save(self, records):
#         self.file.write_text(json.dumps(records, indent=2))
