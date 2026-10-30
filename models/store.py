from enum import Enum
from pydantic import BaseModel
from typing import Optional


class StoreName(str, Enum):
    BIEDRONKA = "Biedronka"
    LIDL = "Lidl"
    AUCHAN = "Auchan"
    DINO = "Dino"
    CARREFOUR = "Carrefour"
    KAUFLAND = "Kaufland"
    OTHER = "Inny"


class StoreInfo(BaseModel):
    name: StoreName
    display_name: str
    logo_emoji: str
    loyalty_card_name: Optional[str] = None
    website: str


STORE_METADATA = {
    StoreName.BIEDRONKA: StoreInfo(
        name=StoreName.BIEDRONKA,
        display_name="Biedronka",
        logo_emoji="🐞",
        loyalty_card_name="Moja Biedronka",
        website="https://www.biedronka.pl"
    ),
    StoreName.LIDL: StoreInfo(
        name=StoreName.LIDL,
        display_name="Lidl",
        logo_emoji="🟡",
        loyalty_card_name="Lidl Plus",
        website="https://www.lidl.pl"
    ),
    StoreName.AUCHAN: StoreInfo(
        name=StoreName.AUCHAN,
        display_name="Auchan",
        logo_emoji="🐦",
        loyalty_card_name="Skarbonka",
        website="https://www.auchan.pl"
    ),
    StoreName.DINO: StoreInfo(
        name=StoreName.DINO,
        display_name="Dino",
        logo_emoji="🦖",
        loyalty_card_name=None,
        website="https://marketdino.pl"
    ),
    StoreName.CARREFOUR: StoreInfo(
        name=StoreName.CARREFOUR,
        display_name="Carrefour",
        logo_emoji="🟦",
        loyalty_card_name="Mój Carrefour",
        website="https://www.carrefour.pl"
    ),
    StoreName.KAUFLAND: StoreInfo(
        name=StoreName.KAUFLAND,
        display_name="Kaufland",
        logo_emoji="🔴",
        loyalty_card_name="Kaufland Card",
        website="https://www.kaufland.pl"
    ),
}
