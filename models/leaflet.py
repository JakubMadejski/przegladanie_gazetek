from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field
from .store import StoreName


class Leaflet(BaseModel):
    id: str = Field(description="Unikalny identyfikator gazetki, np. biedronka_2026_w44")
    store: StoreName
    title: str
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    cover_image_url: Optional[str] = None
    source_url: str
    pdf_url: Optional[str] = None
    page_urls: List[str] = Field(default_factory=list)
    pages_count: int = 0
    scraped_at: Optional[str] = None
