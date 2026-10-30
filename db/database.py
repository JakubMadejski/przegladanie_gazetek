import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Generator, List, Optional, Tuple
from models import Leaflet, ProductDeal, StoreName

from extractor.synonyms import expand_search_terms, stem_polish_word

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "gazetki.db"


def normalize_polish_text(text: str) -> str:
    """Usuwa polskie znaki diakrytyczne i normalizuje tekst do prostego wyszukiwania."""
    if not text:
        return ""
    text = text.lower().strip()
    replacements = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
        'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z'
    }
    for pl, lat in replacements.items():
        text = text.replace(pl, lat)
    text = unicodedata.normalize('NFKD', text)
    cleaned = ''.join(c for c in text if not unicodedata.combining(c))
    cleaned = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in cleaned)
    return ' '.join(cleaned.split())


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._connection() as conn:
            cur = conn.cursor()
            
            # Tabela gazetek
            cur.execute("""
                CREATE TABLE IF NOT EXISTS leaflets (
                    id TEXT PRIMARY KEY,
                    store TEXT NOT NULL,
                    title TEXT NOT NULL,
                    valid_from TEXT,
                    valid_to TEXT,
                    cover_image_url TEXT,
                    source_url TEXT NOT NULL,
                    pdf_url TEXT,
                    pages_count INTEGER DEFAULT 0,
                    scraped_at TEXT
                )
            """)

            # Tabela promocji / produktów
            cur.execute("""
                CREATE TABLE IF NOT EXISTS product_deals (
                    id TEXT PRIMARY KEY,
                    leaflet_id TEXT NOT NULL,
                    store TEXT NOT NULL,
                    name TEXT NOT NULL,
                    normalized_name TEXT NOT NULL,
                    category TEXT,
                    brand TEXT,
                    promo_price REAL NOT NULL,
                    regular_price REAL,
                    discount_percent REAL,
                    unit TEXT,
                    unit_price REAL,
                    conditions TEXT,
                    valid_from TEXT,
                    valid_to TEXT,
                    page_number INTEGER,
                    image_url TEXT,
                    raw_text TEXT,
                    FOREIGN KEY (leaflet_id) REFERENCES leaflets(id) ON DELETE CASCADE
                )
            """)

            cur.execute("CREATE INDEX IF NOT EXISTS idx_deals_store ON product_deals(store)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_deals_normalized ON product_deals(normalized_name)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_deals_promo_price ON product_deals(promo_price)")

            cur.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS deals_fts USING fts5(
                    id UNINDEXED,
                    store,
                    name,
                    normalized_name,
                    category,
                    conditions,
                    tokenize='unicode61'
                )
            """)

    def save_leaflet(self, leaflet: Leaflet):
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT OR REPLACE INTO leaflets (
                    id, store, title, valid_from, valid_to, cover_image_url,
                    source_url, pdf_url, pages_count, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                leaflet.id,
                leaflet.store.value,
                leaflet.title,
                leaflet.valid_from.isoformat() if leaflet.valid_from else None,
                leaflet.valid_to.isoformat() if leaflet.valid_to else None,
                leaflet.cover_image_url,
                leaflet.source_url,
                leaflet.pdf_url,
                leaflet.pages_count,
                leaflet.scraped_at
            ))

    def save_deals(self, deals: List[ProductDeal]):
        if not deals:
            return

        with self._connection() as conn:
            cur = conn.cursor()
            for deal in deals:
                norm_name = deal.normalized_name or normalize_polish_text(deal.name)
                cur.execute("""
                    INSERT OR REPLACE INTO product_deals (
                        id, leaflet_id, store, name, normalized_name, category,
                        brand, promo_price, regular_price, discount_percent,
                        unit, unit_price, conditions, valid_from, valid_to,
                        page_number, image_url, raw_text
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    deal.id,
                    deal.leaflet_id,
                    deal.store.value,
                    deal.name,
                    norm_name,
                    deal.category,
                    deal.brand,
                    deal.promo_price,
                    deal.regular_price,
                    deal.discount_percent,
                    deal.unit,
                    deal.unit_price,
                    deal.conditions,
                    deal.valid_from.isoformat() if deal.valid_from else None,
                    deal.valid_to.isoformat() if deal.valid_to else None,
                    deal.page_number,
                    deal.image_url,
                    deal.raw_text
                ))

                cur.execute("DELETE FROM deals_fts WHERE id = ?", (deal.id,))
                cur.execute("""
                    INSERT INTO deals_fts (id, store, name, normalized_name, category, conditions)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    deal.id,
                    deal.store.value,
                    deal.name,
                    norm_name,
                    deal.category or "",
                    deal.conditions or ""
                ))

    def search_deals(self, query: str, store: Optional[StoreName] = None, limit: int = 20) -> List[ProductDeal]:
        norm_query = normalize_polish_text(query)
        words = [w for w in norm_query.split() if len(w) > 1]
        if not words:
            return []

        expanded_terms = expand_search_terms(norm_query)

        with self._connection() as conn:
            cur = conn.cursor()
            
            # 1. Dokładne dopasowanie wszystkich słów z zapytania
            conditions = []
            params = []
            for w in words:
                conditions.append("normalized_name LIKE ?")
                params.append(f"%{w}%")

            where_clause = " AND ".join(conditions)
            if store:
                where_clause += " AND store = ?"
                params.append(store.value)

            sql = f"""
                SELECT * FROM product_deals 
                WHERE {where_clause}
                ORDER BY promo_price ASC
                LIMIT ?
            """
            params.append(limit)
            cur.execute(sql, params)
            rows = cur.fetchall()

            if rows:
                return [self._row_to_deal(r) for r in rows]

            # 2. Jeśli brak wyników, szukamy po synonimach i rdzeniach słów (np. energetyki -> monster, red bull)
            syn_conditions = []
            syn_params = []
            for term in expanded_terms:
                syn_conditions.append("normalized_name LIKE ?")
                syn_params.append(f"%{term}%")

            if syn_conditions:
                syn_where = " OR ".join(syn_conditions)
                if store:
                    syn_where = f"({syn_where}) AND store = ?"
                    syn_params.append(store.value)
                syn_params.append(limit)
                cur.execute(f"SELECT * FROM product_deals WHERE {syn_where} ORDER BY promo_price ASC LIMIT ?", syn_params)
                rows = cur.fetchall()

            return [self._row_to_deal(r) for r in rows]

    def get_suggestions(self, prefix: str, limit: int = 8) -> List[dict]:
        """Zwraca inteligentne podpowiedzi produktów dla autouzupełniania (uwzględnia synonimy i odmiany)."""
        norm = normalize_polish_text(prefix)
        if len(norm) < 2:
            return []

        expanded = expand_search_terms(norm)
        # Dodajemy też obcięty rdzeń (np. energetyk -> energet)
        if norm.startswith("energet"):
            expanded.append("energet")

        with self._connection() as conn:
            cur = conn.cursor()

            conditions = []
            params = []
            for term in expanded:
                conditions.append("normalized_name LIKE ?")
                params.append(f"%{term}%")

            where_clause = " OR ".join(conditions)
            sql = f"""
                SELECT DISTINCT name, store, promo_price, category
                FROM product_deals
                WHERE {where_clause}
                ORDER BY promo_price ASC
                LIMIT ?
            """
            params.append(limit)
            cur.execute(sql, params)
            
            suggestions = []
            seen = set()
            for r in cur.fetchall():
                name = r["name"]
                if name not in seen:
                    seen.add(name)
                    suggestions.append({
                        "name": name,
                        "store": r["store"],
                        "price": r["promo_price"],
                        "category": r["category"]
                    })
            return suggestions

    def get_deals_by_store(self, store: StoreName, limit: int = 50) -> List[ProductDeal]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM product_deals WHERE store = ? ORDER BY promo_price ASC LIMIT ?
            """, (store.value, limit))
            return [self._row_to_deal(r) for r in cur.fetchall()]

    def get_all_deals(self, limit: int = 500) -> List[ProductDeal]:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM product_deals ORDER BY store, promo_price ASC LIMIT ?", (limit,))
            return [self._row_to_deal(r) for r in cur.fetchall()]

    def get_stats(self) -> dict:
        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM leaflets")
            leaflets_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM product_deals")
            deals_count = cur.fetchone()[0]

            cur.execute("SELECT store, COUNT(*) FROM product_deals GROUP BY store")
            store_counts = dict(cur.fetchall())

            return {
                "leaflets_count": leaflets_count,
                "deals_count": deals_count,
                "store_counts": store_counts
            }

    def _row_to_deal(self, r: sqlite3.Row) -> ProductDeal:
        def parse_date(d_str):
            if not d_str:
                return None
            try:
                return date.fromisoformat(d_str)
            except Exception:
                return None

        return ProductDeal(
            id=r["id"],
            leaflet_id=r["leaflet_id"],
            store=StoreName(r["store"]) if r["store"] in [s.value for s in StoreName] else StoreName.OTHER,
            name=r["name"],
            normalized_name=r["normalized_name"],
            category=r["category"],
            brand=r["brand"],
            promo_price=r["promo_price"],
            regular_price=r["regular_price"],
            discount_percent=r["discount_percent"],
            unit=r["unit"],
            unit_price=r["unit_price"],
            conditions=r["conditions"],
            valid_from=parse_date(r["valid_from"]),
            valid_to=parse_date(r["valid_to"]),
            page_number=r["page_number"],
            image_url=r["image_url"],
            raw_text=r["raw_text"],
        )
