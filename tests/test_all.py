import unittest
from pathlib import Path
from db.database import Database
from models import ProductDeal, StoreName
from extractor.normalizer import (
    strip_accents,
    parse_price,
    extract_unit_and_quantity,
    detect_category,
    detect_conditions
)
from agent.deal_hunter import DealHunterAgent
from scrapers.manager import ScraperManager


class TestNormalizer(unittest.TestCase):
    def test_strip_accents(self):
        self.assertEqual(strip_accents("Masło Ekstra Łagodne Żółte"), "maslo ekstra lagodne zolte")
        self.assertEqual(strip_accents("Świeży Kurczak"), "swiezy kurczak")

    def test_parse_price(self):
        self.assertEqual(parse_price("4,99 zł"), 4.99)
        self.assertEqual(parse_price("19.99"), 19.99)
        self.assertEqual(parse_price("  7,50 PLN  "), 7.50)
        self.assertIsNone(parse_price("invalid"))

    def test_extract_unit_and_quantity(self):
        self.assertEqual(extract_unit_and_quantity("Kawa ziarnista 1kg"), ("kg", 1.0))
        self.assertEqual(extract_unit_and_quantity("Masło 200g"), ("kg", 0.2))
        self.assertEqual(extract_unit_and_quantity("Mleko 1.5l"), ("l", 1.5))
        self.assertEqual(extract_unit_and_quantity("Jaja 10 sztuk"), ("szt.", 10.0))

    def test_detect_category(self):
        self.assertEqual(detect_category("Masło Ekstra 82%"), "Nabiał i jaja")
        self.assertEqual(detect_category("Filet z piersi kurczaka"), "Mięso i wędliny")
        self.assertEqual(detect_category("Banany luz"), "Owoce i warzywa")
        self.assertEqual(detect_category("Kawa ziarnista Lavazza"), "Napoje i kawa")

    def test_detect_conditions(self):
        text = "Cena 4.99 zł z aplikacją Moja Biedronka przy zakupie 2 sztuk"
        cond = detect_conditions(text)
        self.assertIn("Moja Biedronka", cond)
        self.assertIn("przy zakupie min. 2 sztuk", cond)


class TestDatabaseAndAgent(unittest.TestCase):
    def setUp(self):
        self.db_path = Path("/tmp/test_gazetki_run.db")
        if self.db_path.exists():
            self.db_path.unlink()
        self.db = Database(db_path=self.db_path)
        ScraperManager(db=self.db).sync_all()
        self.agent = DealHunterAgent(db=self.db)

    def tearDown(self):
        if self.db_path.exists():
            self.db_path.unlink()

    def test_database_stats(self):
        stats = self.db.get_stats()
        self.assertEqual(stats["leaflets_count"], 3)
        self.assertGreaterEqual(stats["deals_count"], 75)
        self.assertIn("Biedronka", stats["store_counts"])
        self.assertIn("Lidl", stats["store_counts"])
        self.assertIn("Auchan", stats["store_counts"])

    def test_vodka_and_alcohol_search(self):
        # Test wyszukiwania wódki z polskimi znakami i bez
        deals_wodka = self.db.search_deals("wódka")
        self.assertGreaterEqual(len(deals_wodka), 3)
        self.assertTrue(any("zubrowka" in d.name.lower() or "bocian" in d.name.lower() or "soplica" in d.name.lower() for d in deals_wodka))

        deals_bocian = self.db.search_deals("bocian")
        self.assertGreaterEqual(len(deals_bocian), 1)

    def test_suggestions_endpoint(self):
        suggs = self.db.get_suggestions("energetyk")
        self.assertGreaterEqual(len(suggs), 1)
        self.assertTrue(any("energet" in s["name"].lower() for s in suggs))

    def test_typo_tolerance_fuzzy_search(self):
        # Test literówek: 'enrgetyki' -> energetyki
        deals_typo1 = self.db.search_deals("enrgetyki")
        self.assertGreaterEqual(len(deals_typo1), 3)

        # Test literówki: 'msalo' -> masło
        deals_typo2 = self.db.search_deals("msalo")
        self.assertGreaterEqual(len(deals_typo2), 3)

        # Test koszyka z literówkami
        items = self.agent.parse_customer_query_to_items("2x msalo, enrgetyki, kruczak")
        comparison = self.agent.compare_basket(items)
        self.assertEqual(comparison.store_summaries[0].items_found, 3)

    def test_search_deals(self):
        deals_pl = self.db.search_deals("masło")
        self.assertGreaterEqual(len(deals_pl), 3)

        deals_no_pl = self.db.search_deals("maslo")
        self.assertEqual(len(deals_pl), len(deals_no_pl))

    def test_parse_customer_query(self):
        items = self.agent.parse_customer_query_to_items("Chcę kupić: 2x masło, 1kg kurczaka oraz kawę ziarnistą")
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0].query, "masło")
        self.assertEqual(items[0].quantity, 2.0)

    def test_compare_basket(self):
        items = self.agent.parse_customer_query_to_items("masło, mleko, banany")
        comparison = self.agent.compare_basket(items)
        self.assertIn(comparison.best_store, [StoreName.BIEDRONKA, StoreName.LIDL, StoreName.AUCHAN])
        self.assertGreater(comparison.lowest_total, 0)
        self.assertEqual(len(comparison.store_summaries), 3)
        self.assertIn("Najbardziej opłaca się", comparison.recommendation)

    def test_agent_single_item_prompt(self):
        response = self.agent.answer_customer_prompt("Ile kosztuje masło?")
        self.assertIn("Najtaniej", response)
        self.assertTrue("Lidl" in response or "Biedronka" in response or "Auchan" in response)

    def test_fastapi_endpoints(self):
        from fastapi.testclient import TestClient
        from api.app import app
        client = TestClient(app)
        
        # Test stats
        res = client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        self.assertIn("deals_count", res.json())

        # Test search
        res = client.get("/api/search?q=masło")
        self.assertEqual(res.status_code, 200)
        self.assertGreater(len(res.json()["deals"]), 0)

        # Test basket
        res = client.post("/api/basket", json={"query": "masło, mleko"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("best_store", res.json())

        # Test HTML frontend
        res = client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("GazetkoAgent", res.text)


if __name__ == "__main__":
    unittest.main()

