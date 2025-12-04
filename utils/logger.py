# utils/logger.py
import logging
from config.settings import LOG_DIR

LOG_FILE = LOG_DIR / "app.log"

logging.basicConfig(level=logging.INFO, filename=str(LOG_FILE), filemode='a',
                    format='%(asctime)s %(levelname)s %(message)s')

logger = logging.getLogger("scraper_app")