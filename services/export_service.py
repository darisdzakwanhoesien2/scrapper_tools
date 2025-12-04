# services/export_service.py
import csv
from pathlib import Path
from services.storage_service import StorageService

storage = StorageService()


def export_csv(filename: str, records: list, fields: list = None) -> str:
    p = Path(storage.processed_dir) / filename
    with p.open("w", newline='', encoding='utf-8') as f:
        if not records:
            f.write("")
            return str(p)
        if not fields:
            # infer fields from first record
            fields = list(records[0].keys())
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in records:
            writer.writerow(r)
    return str(p)


def export_json(filename: str, records: list) -> str:
    return storage.save_processed(filename, records)