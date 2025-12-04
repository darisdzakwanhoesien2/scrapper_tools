# core/scheduler.py
import threading
import time
from config.settings import SETTINGS
from services.dataset_service import DatasetService
from typing import Optional

_scheduler_thread = None
_stop_event = threading.Event()


class Scheduler:
    def __init__(self, dataset_service: DatasetService, interval: Optional[int] = None):
        self.ds = dataset_service
        self.interval = interval or SETTINGS["refresh_interval_sec"]

    def _run_loop(self):
        while not _stop_event.is_set():
            # Example: iterate over saved targets in processed/dataset_targets.json
            targets = self.ds.get_targets()
            for t in targets:
                try:
                    self.ds.scrape_and_merge(t)
                except Exception:
                    # continue on error
                    pass
            time.sleep(self.interval)

    def start(self):
        global _scheduler_thread
        if _scheduler_thread and _scheduler_thread.is_alive():
            return
        _stop_event.clear()
        _scheduler_thread = threading.Thread(target=self._run_loop, daemon=True)
        _scheduler_thread.start()

    @staticmethod
    def stop():
        _stop_event.set()