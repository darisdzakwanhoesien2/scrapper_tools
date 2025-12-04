# config/settings.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOG_DIR = DATA_DIR / "logs"

for d in (RAW_DIR, PROCESSED_DIR, LOG_DIR):
    d.mkdir(parents=True, exist_ok=True)

SETTINGS = {
    "refresh_interval_sec": 300,  # default auto-refresh
    "max_pages": 20,
    "user_agent": "streamlit-scraper/1.0",
    "timeout": 15,
}