# 🛒 GazetkoAgent - Inteligentny Asystent Zakupowy & Analizator Gazetek

Autonomiczny agent AI analizujący gazetki promocyjne najpopularniejszych sieci handlowych w Polsce (**Biedronka**, **Lidl**, **Auchan** i kolejne). Agent potrafi interpretować zapytania w języku naturalnym, porównywać ceny pojedynczych produktów oraz optymalizować całe koszyki zakupowe, uwzględniając warunki specjalne (np. karty lojalnościowe, wielopaki, limity).

---

## 🌟 Kluczowe funkcjonalności prototypu

1. **Baza Danych & Inteligentne Wyszukiwanie (SQLite + FTS5)**:
   - Pełna obsługa języka polskiego i normalizacja znaków diakrytycznych (`masło` = `maslo`).
   - Wyszukiwanie pełnotekstowe po nazwach, markach, kategoriach i warunkach promocji.
2. **Ekstraktor Ofert & Normalizator Cen**:
   - Przeliczanie cen jednostkowych (za kg / litr / sztukę).
   - Wykrywanie i analiza haczyków/warunków promocji (*„z aplikacją Moja Biedronka”*, *„karta Lidl Plus”*, *„drugi 50% taniej”*, *„limit 3 kg”*).
   - Automatyczna kategoryzacja produktów (nabiał, mięso, owoce/warzywa, kawa itp.).
3. **Mózg Agenta Zakupowego (`DealHunterAgent`)**:
   - Rozpoznawanie intencji użytkownika z dowolnego tekstu (np. *„Gdzie najtaniej kupię masło, banany i filet z kurczaka?”*).
   - Ekstrakcja produktów, ilości i wag (*„2x masło”*, *„1kg kurczaka”*).
   - Symulacja koszyka: wylicza łączny koszt w każdym sklepie, porównuje różnice i wskazuje zwycięzcę z wyliczonymi oszczędnościami.
4. **Interaktywny interfejs CLI (`rich`)**:
   - Tryb konwersacyjny, wyszukiwarka tabelaryczna i natychmiastowe porównywanie koszyków.

---

## 🚀 Jak uruchomić prototyp

### 1. Środowisko wirtualne i zależności
```bash
# Aktywacja środowiska
source .venv/bin/activate

# Instalacja zależności (jeśli potrzebne)
pip install -r requirements.txt
```

### 2. Przykłady użycia CLI

#### 🔍 Wyszukanie promocji na pojedynczy produkt
```bash
python -m cli.main search "kawa ziarnista"
python -m cli.main search "masło"
```

#### 🧺 Porównanie koszyka zakupowego
```bash
python -m cli.main basket "2x masło, 1kg kurczaka, kawa, mleko, banany"
```

#### 💬 Swobodne zapytanie w języku naturalnym
```bash
python -m cli.main "Gdzie najtaniej kupię schab, olej i 10 jajek?"
```

#### 🤖 Tryb interaktywnego czatu
```bash
python -m cli.main chat
```

#### 🔄 Synchronizacja danych i gazetek
```bash
python -m cli.main sync
```

---

## 🧪 Testy

Projekt posiada pełny zestaw testów jednostkowych i integracyjnych uruchamianych jednym poleceniem:
```bash
python -m unittest tests/test_all.py -v
```

---

## 🏗️ Architektura projektu

```
├── agent/                 # Logika asystenta AI i optymalizacja koszyka
│   └── deal_hunter.py     # DealHunterAgent (NLP, matching, scoring)
├── cli/                   # Narzędzie wiersza poleceń z kolorowym interfejsem rich
│   └── main.py            # Punkty wejścia CLI (search, basket, chat, sync)
├── db/                    # Warstwa danych i SQLite
│   └── database.py        # FTS5, indeksy, normalizacja tekstu polskiego
├── extractor/             # Silnik parsowania i normalizacji ofert
│   ├── normalizer.py      # Wykrywanie cen, gramatur, kategorii, warunków
│   └── parser.py          # Konwersja surowych danych do ProductDeal
├── models/                # Modele domenowe Pydantic
│   ├── store.py           # Sieci sklepów i metadane
│   ├── leaflet.py         # Gazetki promocyjne
│   └── product.py         # Oferty, koszyk, dopasowania
├── scrapers/              # Moduły pobierające gazetki
│   ├── base.py            # Interfejs BaseScraper
│   ├── biedronka.py       # Scraper Biedronki
│   ├── lidl.py            # Scraper Lidla
│   ├── auchan.py          # Scraper Auchan
│   └── manager.py         # Koordynator synchronizacji
├── data/                  # Magazyn danych (baza sqlite, snapshoty JSON)
└── tests/                 # Automatyczne testy integracyjne
```

---

## 💡 Ścieżka komercjalizacji (Następne kroki)

1. **Aplikacja mobilna / PWA / Bot Telegram & WhatsApp**:
   - Użytkownik wkleja listę zakupów lub wysyła notatkę głosową przed wyjściem do sklepu.
2. **Konta użytkowników i personalizacja**:
   - Zaznaczanie posiadanych kart lojalnościowych (*„mam tylko aplikację Moja Biedronka”* -> agent filtruje promocje dostępne tylko dla niego).
   - Preferowane sklepy w okolicy (geolokalizacja).
3. **Monetyzacja & Partnerstwa**:
   - Afiliacja i cashback z sieciami handlowymi.
   - Płatna subskrypcja Pro (alerty o ulubionych produktach, np. *„Twoja ulubiona kawa Lavazza jest w promocji -40% od jutra”*).
   - API B2B dla serwisów z przepisami kulinarnymi (np. *„Kup składniki do tego przepisu za 24 zł w Lidlu”*).
