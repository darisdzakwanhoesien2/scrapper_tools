import logging
from pathlib import Path

LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "scraper.log"

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("scraper")

# # utils/logger.py
# import logging
# from config.settings import LOG_DIR

# LOG_FILE = LOG_DIR / "app.log"

# logging.basicConfig(level=logging.INFO, filename=str(LOG_FILE), filemode='a',
#                     format='%(asctime)s %(levelname)s %(message)s')

# logger = logging.getLogger("scraper_app")