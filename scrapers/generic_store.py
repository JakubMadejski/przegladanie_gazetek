import json
from datetime import date
from pathlib import Path
from typing import List
from models import Leaflet, ProductDeal, StoreName
from extractor.parser import DealParser
from .base import BaseScraper


class GenericStoreScraper(BaseScraper):
    """Uniwersalny scraper dla sieci handlowych z obsługą snapshotów i web scrapera."""

    def __init__(self, store: StoreName, snapshot_filename: str, website_url: str):
        super().__init__(store=store)
        self.snapshot_path = Path(__file__).resolve().parent.parent / "data" / "snapshots" / snapshot_filename
        self.website_url = website_url

    def fetch_leaflets(self) -> List[Leaflet]:
        return self._load_snapshot_leaflets()

    def fetch_deals_for_leaflet(self, leaflet: Leaflet) -> List[ProductDeal]:
        return self._load_snapshot_deals(leaflet.id)

    def _load_snapshot_leaflets(self) -> List[Leaflet]:
        if not self.snapshot_path.exists():
            return []
        with open(self.snapshot_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ld = data.get("leaflet", {})
        return [
            Leaflet(
                id=ld.get("id", f"{self.store.value.lower()}_current"),
                store=self.store,
                title=ld.get("title", f"{self.store.value} Gazetka Aktualna"),
                valid_from=date.fromisoformat(ld["valid_from"]) if ld.get("valid_from") else None,
                valid_to=date.fromisoformat(ld["valid_to"]) if ld.get("valid_to") else None,
                source_url=ld.get("source_url", self.website_url),
                pages_count=ld.get("pages_count", 24)
            )
        ]

    def _load_snapshot_deals(self, leaflet_id: str) -> List[ProductDeal]:
        if not self.snapshot_path.exists():
            return []
        with open(self.snapshot_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_deals = data.get("deals", [])
        return DealParser.parse_deal_list(raw_deals, leaflet_id=leaflet_id, store=self.store)
