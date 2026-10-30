from typing import Dict, List, Optional
from db.database import Database
from models import Leaflet, ProductDeal, StoreName
from .base import BaseScraper
from .biedronka import BiedronkaScraper
from .lidl import LidlScraper
from .auchan import AuchanScraper
from .generic_store import GenericStoreScraper


class ScraperManager:
    """Zarządza pobieraniem gazetek i synchronizacją bazy danych ze wszystkich sklepów."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()
        self.scrapers: Dict[StoreName, BaseScraper] = {
            StoreName.BIEDRONKA: BiedronkaScraper(),
            StoreName.LIDL: LidlScraper(),
            StoreName.AUCHAN: AuchanScraper(),
            StoreName.ZABKA: GenericStoreScraper(StoreName.ZABKA, "zabka.json", "https://www.zabka.pl"),
            StoreName.DINO: GenericStoreScraper(StoreName.DINO, "dino.json", "https://marketdino.pl"),
            StoreName.KAUFLAND: GenericStoreScraper(StoreName.KAUFLAND, "kaufland.json", "https://www.kaufland.pl"),
            StoreName.CARREFOUR: GenericStoreScraper(StoreName.CARREFOUR, "carrefour.json", "https://www.carrefour.pl"),
        }

    def sync_store(self, store: StoreName) -> Dict[str, int]:
        scraper = self.scrapers.get(store)
        if not scraper:
            raise ValueError(f"Brak scrapera dla sklepu {store}")

        leaflets, deals = scraper.sync_all()

        for l in leaflets:
            self.db.save_leaflet(l)

        self.db.save_deals(deals)

        return {
            "leaflets": len(leaflets),
            "deals": len(deals)
        }

    def sync_all(self) -> Dict[str, Dict[str, int]]:
        results = {}
        for store in self.scrapers.keys():
            results[store.value] = self.sync_store(store)
        return results
