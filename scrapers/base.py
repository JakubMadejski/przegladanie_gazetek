from abc import ABC, abstractmethod
from typing import List, Tuple
from models import Leaflet, ProductDeal, StoreName


class BaseScraper(ABC):
    """Bazowa klasa dla wszystkich scraperów gazetek i ofert sklepowych."""

    def __init__(self, store: StoreName):
        self.store = store

    @abstractmethod
    def fetch_leaflets(self) -> List[Leaflet]:
        """Pobiera listę aktualnych gazetek dla danego sklepu."""
        pass

    @abstractmethod
    def fetch_deals_for_leaflet(self, leaflet: Leaflet) -> List[ProductDeal]:
        """Ekstrahuje produkty i promocje z konkretnej gazetki."""
        pass

    def sync_all(self) -> Tuple[List[Leaflet], List[ProductDeal]]:
        """Pobiera wszystkie gazetki i promocje dla sklepu."""
        leaflets = self.fetch_leaflets()
        all_deals = []
        for l in leaflets:
            deals = self.fetch_deals_for_leaflet(l)
            all_deals.extend(deals)
        return leaflets, all_deals
