import uuid
from datetime import date
from typing import Dict, List, Optional
from models import ProductDeal, StoreName
from .normalizer import (
    strip_accents,
    parse_price,
    extract_unit_and_quantity,
    detect_category,
    detect_conditions
)


class DealParser:
    """Parsuje surowe opisy produktów z gazetek do obiektów ProductDeal."""

    @staticmethod
    def parse_raw_deal(
        raw_data: Dict,
        leaflet_id: str,
        store: StoreName,
        default_valid_from: Optional[date] = None,
        default_valid_to: Optional[date] = None
    ) -> Optional[ProductDeal]:
        name = raw_data.get("name", "").strip()
        if not name:
            return None

        promo_price = raw_data.get("promo_price")
        if isinstance(promo_price, str):
            promo_price = parse_price(promo_price)
        if promo_price is None or promo_price <= 0:
            return None

        regular_price = raw_data.get("regular_price")
        if isinstance(regular_price, str):
            regular_price = parse_price(regular_price)

        discount_percent = raw_data.get("discount_percent")
        if discount_percent is None and regular_price and regular_price > promo_price:
            discount_percent = round(((regular_price - promo_price) / regular_price) * 100, 1)

        raw_text = raw_data.get("raw_text", f"{name} {promo_price} zł {raw_data.get('conditions', '')}")
        conditions = raw_data.get("conditions") or detect_conditions(raw_text)

        unit, qty = extract_unit_and_quantity(name + " " + raw_data.get("unit_info", ""))
        unit_price = raw_data.get("unit_price")
        if unit_price is None and qty > 0 and unit in ["kg", "l"]:
            unit_price = round(promo_price / qty, 2)

        category = raw_data.get("category") or detect_category(name)

        deal_id = raw_data.get("id") or f"{store.value.lower()}_{uuid.uuid4().hex[:8]}"

        return ProductDeal(
            id=deal_id,
            leaflet_id=leaflet_id,
            store=store,
            name=name,
            normalized_name=strip_accents(name),
            category=category,
            brand=raw_data.get("brand"),
            promo_price=promo_price,
            regular_price=regular_price,
            discount_percent=discount_percent,
            unit=unit,
            unit_price=unit_price,
            conditions=conditions,
            valid_from=raw_data.get("valid_from") or default_valid_from,
            valid_to=raw_data.get("valid_to") or default_valid_to,
            page_number=raw_data.get("page_number", 1),
            image_url=raw_data.get("image_url"),
            raw_text=raw_text
        )

    @classmethod
    def parse_deal_list(
        cls,
        raw_list: List[Dict],
        leaflet_id: str,
        store: StoreName,
        default_valid_from: Optional[date] = None,
        default_valid_to: Optional[date] = None
    ) -> List[ProductDeal]:
        deals = []
        for raw in raw_list:
            deal = cls.parse_raw_deal(
                raw,
                leaflet_id=leaflet_id,
                store=store,
                default_valid_from=default_valid_from,
                default_valid_to=default_valid_to
            )
            if deal:
                deals.append(deal)
        return deals

