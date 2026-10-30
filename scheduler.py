import time
import datetime
import logging
from pathlib import Path
from scrapers.manager import ScraperManager
from db.database import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).resolve().parent / "scheduler.log", encoding="utf-8")
    ]
)

TARGET_HOUR = 6  # 06:00 rano
TARGET_MINUTE = 0


def run_sync_job():
    logging.info(" Rozpoczynam poranną synchronizację gazetek promocyjnych...")
    try:
        db = Database()
        sm = ScraperManager(db=db)
        results = sm.sync_all()
        for store, stats in results.items():
            logging.info(f"[{store}] Pobrano {stats['leaflets']} gazetek, zaktualizowano {stats['deals']} promocji.")
        total_stats = db.get_stats()
        logging.info(f"Synchronizacja zakończona pomyślnie. Baza zawiera łącznie {total_stats['deals_count']} aktywnych ofert.")
    except Exception as e:
        logging.error(f"Błąd podczas synchronizacji gazetek: {e}", exc_info=True)


def schedule_loop():
    logging.info(f"⏰ GazetkoAgent Scheduler uruchomiony na Macu mini. Synchronizacja zaplanowana na codzień o {TARGET_HOUR:02d}:{TARGET_MINUTE:02d}.")
    
    # Wykonaj pierwszą synchronizację od razu przy starcie
    run_sync_job()

    while True:
        now = datetime.datetime.now()
        # Wyliczamy czas do najbliższej 06:00
        target = now.replace(hour=TARGET_HOUR, minute=TARGET_MINUTE, second=0, microsecond=0)
        if now >= target:
            target += datetime.timedelta(days=1)
        
        sleep_seconds = (target - now).total_seconds()
        logging.info(f"Następne odświeżenie bazy za {sleep_seconds / 3600:.1f} godzin ({target.strftime('%Y-%m-%d %H:%M:%S')}).")
        
        time.sleep(sleep_seconds)
        run_sync_job()


if __name__ == "__main__":
    schedule_loop()

