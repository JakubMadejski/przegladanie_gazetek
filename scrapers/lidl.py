import json
from datetime import date
from pathlib import Path
from typing import List
import httpx
from bs4 import BeautifulSoup
from models import Leaflet, ProductDeal, StoreName
from extractor.parser import DealParser
from .base import BaseScraper

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "data" / "snapshots" / "lidl.json"


class LidlScraper(BaseScraper):
    def __init__(self):
        super().__init__(store=StoreName.LIDL)

    def fetch_leaflets(self) -> List[Leaflet]:
        """Próbuje pobrać gazetki online z Lidla, z fallbackiem do lokalnego snapshotu."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept-Language": "pl-PL,pl;q=0.9",
            }
            with httpx.Client(headers=headers, timeout=5.0) as client:
                r = client.get("https://www.lidl.pl")
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    leaflets = []
                    for idx, a in enumerate(soup.find_all("a", href=True)):
                        href = a["href"]
                        if "gazetk" in href.lower():
                            title = a.get_text(" ", strip=True) or f"Lidl Gazetka {idx+1}"
                            leaflets.append(
                                Leaflet(
                                    id=f"lidl_web_{idx+1}",
                                    store=self.store,
                                    title=title,
                                    source_url="https://www.lidl.pl" + href if href.startswith("/") else href,
                                    valid_from=date.today(),
                                    pages_count=30
                                )
                            )
                    if leaflets:
                        return leaflets[:3]
        except Exception:
            pass

        return self._load_snapshot_leaflets()

    def fetch_deals_for_leaflet(self, leaflet: Leaflet) -> List[ProductDeal]:
        return self._load_snapshot_deals(leaflet.id)

    def _load_snapshot_leaflets(self) -> List[Leaflet]:
        if not SNAPSHOT_PATH.exists():
            return []
        with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        ld = data.get("leaflet", {})
        return [
            Leaflet(
                id=ld["id"],
                store=self.store,
                title=ld["title"],
                valid_from=date.fromisoformat(ld["valid_from"]) if ld.get("valid_from") else None,
                valid_to=date.fromisoformat(ld["valid_to"]) if ld.get("valid_to") else None,
                source_url=ld["source_url"],
                pages_count=ld.get("pages_count", 0)
            )
        ]

    def _load_snapshot_deals(self, leaflet_id: str) -> List[ProductDeal]:
        if not SNAPSHOT_PATH.exists():
            return []
        with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_deals = data.get("deals", [])
        return DealParser.parse_deal_list(raw_deals, leaflet_id=leaflet_id, store=self.store)

