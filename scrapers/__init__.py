from .base import BaseScraper
from .biedronka import BiedronkaScraper
from .lidl import LidlScraper
from .auchan import AuchanScraper
from .manager import ScraperManager

__all__ = [
    "BaseScraper",
    "BiedronkaScraper",
    "LidlScraper",
    "AuchanScraper",
    "ScraperManager"
]

