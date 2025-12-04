import json
from pathlib import Path

class StorageService:
    def __init__(self):
        self.data_dir = Path("data/processed")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.file = self.data_dir / "dataset.json"

    def load(self):
        if not self.file.exists():
            return []
        return json.loads(self.file.read_text())

    def save(self, records):
        self.file.write_text(json.dumps(records, indent=2))
