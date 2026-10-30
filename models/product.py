from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field
from .store import StoreName


class ProductDeal(BaseModel):
    id: str = Field(description="Unikalny identyfikator oferty")
    leaflet_id: str
    store: StoreName
    name: str = Field(description="Pełna nazwa produktu, np. Masło Ekstra 82% Mlekovita")
    normalized_name: Optional[str] = Field(default=None, description="Znormalizowana nazwa do wyszukiwania, np. maslo ekstra mlekovita")
    category: Optional[str] = Field(default=None, description="Kategoria, np. nabiał, mięso, napoje, owoce i warzywa")
    brand: Optional[str] = None
    promo_price: float = Field(description="Aktualna promocyjna cena w PLN")
    regular_price: Optional[float] = Field(default=None, description="Cena regularna w PLN przed obniżką")
    discount_percent: Optional[float] = Field(default=None, description="Procent obniżki (np. 30 dla -30%)")
    unit: Optional[str] = Field(default="szt.", description="Jednostka: szt., kg, l, opak., puszka itp.")
    unit_price: Optional[float] = Field(default=None, description="Cena przeliczona na kg lub litr")
    conditions: Optional[str] = Field(default=None, description="Warunki promocji (np. 'z aplikacją', 'przy zakupie 2 sztuk')")
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    page_number: Optional[int] = None
    image_url: Optional[str] = None
    raw_text: Optional[str] = None


class BasketItemRequest(BaseModel):
    query: str
    quantity: float = 1.0
    unit: Optional[str] = None


class StoreBasketMatch(BaseModel):
    store: StoreName
    requested_query: str
    matched_deal: Optional[ProductDeal] = None
    calculated_price: float = 0.0
    found: bool = False
    note: Optional[str] = None


class StoreBasketSummary(BaseModel):
    store: StoreName
    total_cost: float
    items_found: int
    items_total: int
    matched_deals: List[StoreBasketMatch]
    savings_vs_regular: float = 0.0
    conditions_summary: List[str] = Field(default_factory=list)


class CustomerBasketComparison(BaseModel):
    items_requested: List[BasketItemRequest]
    best_store: Optional[StoreName] = None
    lowest_total: Optional[float] = None
    store_summaries: List[StoreBasketSummary]
    recommendation: str
