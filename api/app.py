from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from db.database import Database
from models import CustomerBasketComparison, ProductDeal, StoreName, STORE_METADATA
from agent.deal_hunter import DealHunterAgent
from scrapers.manager import ScraperManager

app = FastAPI(
    title="GazetkoAgent API",
    description="API inteligentnego asystenta promocji w polskich supermarketach (Biedronka, Lidl, Auchan)",
    version="1.0.0"
)

# Włączamy CORS, aby strona na home.pl mogła bez problemu łączyć się z API Maca mini
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
agent = DealHunterAgent(db=db)
scraper_manager = ScraperManager(db=db)

# Upewniamy się, że baza jest zainicjalizowana danymi
if db.get_stats()["deals_count"] == 0:
    scraper_manager.sync_all()


class BasketRequest(BaseModel):
    query: str
    stores: Optional[List[str]] = None


@app.get("/api/stats")
def get_stats():
    """Zwraca statystyki bazy danych i podsumowanie sklepów."""
    stats = db.get_stats()
    stores_info = []
    for s_name in [StoreName.BIEDRONKA, StoreName.LIDL, StoreName.AUCHAN]:
        meta = STORE_METADATA.get(s_name)
        count = stats["store_counts"].get(s_name.value, 0)
        stores_info.append({
            "name": s_name.value,
            "emoji": meta.logo_emoji if meta else "🏪",
            "loyalty_card": meta.loyalty_card_name if meta else None,
            "deals_count": count
        })
    return {
        "leaflets_count": stats["leaflets_count"],
        "deals_count": stats["deals_count"],
        "stores": stores_info
    }


@app.get("/api/suggestions")
def get_suggestions(q: str = Query(..., min_length=2)):
    """Zwraca podpowiedzi produktów do autouzupełniania podczas pisania."""
    suggestions = db.get_suggestions(q, limit=8)
    return {
        "query": q,
        "suggestions": suggestions
    }


@app.get("/api/search")
def search_deals(q: str = Query(..., min_length=2), store: Optional[str] = None):
    """Wyszukuje promocje dla podanego hasła (np. 'masło', 'kawa')."""
    target_store = None
    if store:
        for s in StoreName:
            if s.value.lower() == store.lower():
                target_store = s
                break

    deals = db.search_deals(q, store=target_store, limit=30)
    return {
        "query": q,
        "results_count": len(deals),
        "deals": [d.model_dump() for d in deals]
    }


@app.post("/api/basket", response_model=CustomerBasketComparison)
def compare_basket(request: BasketRequest):
    """Porównuje koszyk zakupowy we wszystkich sklepach i wybiera najtańszy."""
    items = agent.parse_customer_query_to_items(request.query)
    if not items:
        raise HTTPException(status_code=400, detail="Nie udało się rozpoznać produktów w podanym zapytaniu.")

    target_stores = None
    if request.stores:
        target_stores = []
        for s_str in request.stores:
            for s_enum in StoreName:
                if s_enum.value.lower() == s_str.lower():
                    target_stores.append(s_enum)
                    break

    return agent.compare_basket(items, stores=target_stores)


@app.post("/api/sync")
def sync_leaflets():
    """Wymusza odświeżenie bazy gazetek ze scraperów."""
    results = scraper_manager.sync_all()
    stats = db.get_stats()
    return {
        "status": "success",
        "synced": results,
        "total_deals": stats["deals_count"],
        "total_leaflets": stats["leaflets_count"]
    }


# Wbudowany frontend HTML serwowany bezpośrednio z Maca mini
@app.get("/", response_class=HTMLResponse)
def index_page():
    html_path = Path(__file__).resolve().parent.parent / "web" / "index.html"
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>GazetkoAgent API is running!</h1>"

