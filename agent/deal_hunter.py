import re
from typing import Dict, List, Optional, Tuple
from db.database import Database, normalize_polish_text
from models import (
    BasketItemRequest,
    CustomerBasketComparison,
    ProductDeal,
    StoreBasketMatch,
    StoreBasketSummary,
    StoreName,
    STORE_METADATA
)


class DealHunterAgent:
    """Inteligentny agent zakupowy analizujący oferty promocyjne i optymalizujący koszyk klienta."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    def parse_customer_query_to_items(self, query: str) -> List[BasketItemRequest]:
        """Ekstrahuje listę produktów i ilości ze swobodnego tekstu użytkownika."""
        cleaned = query.lower()

        # Usuwamy interpunkcję na końcach zdań (?, !, .)
        cleaned = re.sub(r"[?!.]+$", "", cleaned)

        # Usuwamy popularne wstępy pytające
        prefixes = [
            "chce kupic", "chcę kupić", "szukam", "gdzie najtaniej kupie",
            "gdzie najtaniej kupię", "porownaj", "porównaj", "ile kosztuje",
            "jaka jest cena", "lista zakupow", "lista zakupów", "koszyk"
        ]
        for p in prefixes:
            if cleaned.startswith(p):
                cleaned = cleaned[len(p):].strip()
                break

        # Usuwamy ewentualny dwukropek na początku
        cleaned = cleaned.lstrip(" :-\t")

        # Dzielimy po przecinkach, 'i', 'oraz', nowej linii
        raw_parts = re.split(r"[,;\n]|\s+oraz\s+|\s+i\s+", cleaned)
        items = []

        for part in raw_parts:
            # Czyszczenie znaków interpunkcyjnych
            part = part.strip(" :-\t?!.")
            if not part:
                continue

            qty = 1.0
            unit = None

            # Wzorce: 2x, 2 x
            match_x = re.match(r"^(\d+(?:[.,]\d+)?)\s*x\s*(.+)$", part)
            if match_x:
                qty = float(match_x.group(1).replace(",", "."))
                part = match_x.group(2).strip()

            # Wzorce: 2 kg, 500 g, 2 l
            match_unit = re.match(r"^(\d+(?:[.,]\d+)?)\s*(kg|g|l|ml|szt|sztuk|opak)\s+(?:z\s+)?(.+)$", part)
            if match_unit:
                qty = float(match_unit.group(1).replace(",", "."))
                unit = match_unit.group(2)
                part = match_unit.group(3).strip()

            # Wzorce: 2 masła
            match_num = re.match(r"^(\d+)\s+(.+)$", part)
            if match_num and not unit:
                qty = float(match_num.group(1))
                part = match_num.group(2).strip()

            part = part.strip(" :-\t?!.")
            if part:
                items.append(BasketItemRequest(query=part, quantity=qty, unit=unit))

        return items

    def search_single_product(self, product_query: str, store: Optional[StoreName] = None) -> List[ProductDeal]:
        """Szuka ofert dla pojedynczego produktu w jednym lub wszystkich sklepach."""
        return self.db.search_deals(product_query, store=store, limit=10)

    def find_best_deal_for_store(self, item: BasketItemRequest, store: StoreName) -> StoreBasketMatch:
        """Znajduje najlepszą ofertę na dany produkt w konkretnym sklepie."""
        deals = self.db.search_deals(item.query, store=store, limit=5)
        if not deals:
            # Próba wyszukiwania po pojedynczych słowach kluczowych
            words = item.query.split()
            for w in words:
                if len(w) > 3:
                    sub_deals = self.db.search_deals(w, store=store, limit=3)
                    if sub_deals:
                        deals = sub_deals
                        break

        if not deals:
            return StoreBasketMatch(
                store=store,
                requested_query=item.query,
                matched_deal=None,
                calculated_price=0.0,
                found=False,
                note="Brak oferty w aktualnej gazetce"
            )

        best_deal = deals[0]
        # Obliczenie ceny dla zadanej ilości
        calc_price = round(best_deal.promo_price * item.quantity, 2)

        return StoreBasketMatch(
            store=store,
            requested_query=item.query,
            matched_deal=best_deal,
            calculated_price=calc_price,
            found=True,
            note=best_deal.conditions
        )

    def compare_basket(self, items: List[BasketItemRequest], stores: Optional[List[StoreName]] = None) -> CustomerBasketComparison:
        """Porównuje łączny koszt koszyka zakupowego we wszystkich sklepach."""
        if stores is None:
            stores = [StoreName.BIEDRONKA, StoreName.LIDL, StoreName.AUCHAN]

        store_summaries = []

        for store in stores:
            matched_deals: List[StoreBasketMatch] = []
            total_cost = 0.0
            savings_vs_reg = 0.0
            conditions_set = set()

            for item in items:
                match = self.find_best_deal_for_store(item, store)
                matched_deals.append(match)
                if match.found and match.matched_deal:
                    total_cost += match.calculated_price
                    if match.matched_deal.regular_price:
                        reg_total = match.matched_deal.regular_price * item.quantity
                        savings_vs_reg += max(0.0, reg_total - match.calculated_price)
                    if match.matched_deal.conditions:
                        conditions_set.add(f"{match.matched_deal.name}: {match.matched_deal.conditions}")

            items_found = sum(1 for m in matched_deals if m.found)

            store_summaries.append(
                StoreBasketSummary(
                    store=store,
                    total_cost=round(total_cost, 2),
                    items_found=items_found,
                    items_total=len(items),
                    matched_deals=matched_deals,
                    savings_vs_regular=round(savings_vs_reg, 2),
                    conditions_summary=list(conditions_set)
                )
            )

        # Wybór najlepszego sklepu (najniższy koszt spośród sklepów z kompletem produktów)
        eligible_stores = [s for s in store_summaries if s.items_found == len(items)]
        if not eligible_stores:
            # Jeśli żaden sklep nie ma 100%, bierzemy ten z największą liczbą znalezionych pozycji
            store_summaries.sort(key=lambda s: (-s.items_found, s.total_cost))
            best_store_summary = store_summaries[0] if store_summaries else None
        else:
            eligible_stores.sort(key=lambda s: s.total_cost)
            best_store_summary = eligible_stores[0]

        best_store_name = best_store_summary.store if best_store_summary else None
        lowest_total = best_store_summary.total_cost if best_store_summary else 0.0

        # Generowanie rekomendacji tekstowej
        if best_store_summary and len(store_summaries) > 1:
            sorted_all = sorted(store_summaries, key=lambda s: s.total_cost)
            runner_up = sorted_all[1] if len(sorted_all) > 1 else None
            diff = round(runner_up.total_cost - best_store_summary.total_cost, 2) if runner_up else 0.0
            
            store_meta = STORE_METADATA.get(best_store_name)
            emoji = store_meta.logo_emoji if store_meta else "🛒"

            rec_parts = [
                f"{emoji} **Najbardziej opłaca się zrobić zakupy w sieci {best_store_name.value}!**",
                f"Łączny koszt Twojego koszyka wyniesie: **{lowest_total:.2f} zł** (oszczędzasz ok. {best_store_summary.savings_vs_regular:.2f} zł w stosunku do cen regularnych)."
            ]
            if runner_up and diff > 0:
                rec_parts.append(f"W {runner_up.store.value} ten sam koszyk kosztowałby **{runner_up.total_cost:.2f} zł** (o {diff:.2f} zł drożej).")

            if best_store_summary.conditions_summary:
                rec_parts.append("\n⚠️ **Pamiętaj o warunkach promocyjnych:**")
                for c in best_store_summary.conditions_summary[:3]:
                    rec_parts.append(f"  • {c}")

            recommendation = "\n".join(rec_parts)
        else:
            recommendation = "Brak wystarczających danych do pełnego porównania koszyka."

        return CustomerBasketComparison(
            items_requested=items,
            best_store=best_store_name,
            lowest_total=lowest_total,
            store_summaries=store_summaries,
            recommendation=recommendation
        )

    def answer_customer_prompt(self, prompt: str) -> str:
        """Główny punkt wejściowy agenta: przyjmuje dowolny prompt klienta i odpowiada."""
        items = self.parse_customer_query_to_items(prompt)
        
        if not items:
            return "Nie rozpoznałem produktów w Twoim zapytaniu. Podaj np.: 'masło, jaja, kawa ziarnista i filet z kurczaka'."

        # Jeśli zapytanie dotyczy pojedynczego produktu (np. "ile kosztuje masło")
        if len(items) == 1 and items[0].quantity == 1.0:
            item = items[0]
            deals = self.search_single_product(item.query)
            if not deals:
                return f"Niestety nie znalazłem żadnych aktualnych promocji na produkt: **{item.query}**."

            lines = [f"🔍 **Aktualne promocje na: {item.query.capitalize()}**\n"]
            for d in deals:
                meta = STORE_METADATA.get(d.store)
                emoji = meta.logo_emoji if meta else "🏪"
                reg_info = f" (zamiast {d.regular_price:.2f} zł, -{d.discount_percent:.0f}%)" if d.regular_price else ""
                cond_info = f" | ⚠️ *{d.conditions}*" if d.conditions else ""
                lines.append(f"{emoji} **{d.store.value}**: **{d.promo_price:.2f} zł**{reg_info} – {d.name}{cond_info}")

            # Wybór najtańszego
            cheapest = deals[0]
            lines.append(f"\n🏆 **Najtaniej:** **{cheapest.store.value}** ({cheapest.promo_price:.2f} zł)")
            return "\n".join(lines)

        # Jeśli to koszyk wielu produktów
        comparison = self.compare_basket(items)
        return comparison.recommendation
