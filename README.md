# 🛒 GazetkoAgent - Inteligentny Asystent Zakupowy & Analizator Gazetek

Autonomiczny agent AI monitorujący i analizujący gazetki promocyjne najpopularniejszych sieci handlowych w Polsce (m.in. **Biedronka, Lidl, Auchan, Carrefour, Dino, Kaufland**). Agent umożliwia wyszukiwanie najlepszych okazji, porównywanie cen w oparciu o zapytania w języku naturalnym oraz optymalizację koszyka zakupowego klienta.

---

## 🌟 Kluczowe funkcjonalności

- **Automatyczny pobór gazetek**: Agregacja aktualnych gazetek promocyjnych (PDF / zdjęcia) z oficjalnych stron oraz serwisów promocyjnych.
- **Wizyjno-tekstowa ekstrakcja ofert (Multimodal OCR & Vision LLM)**:
  - Nazwa produktu i marka
  - Cena promocyjna oraz regularna / najniższa z 30 dni (Omnibus)
  - Warunki promocji (np. *„z aplikacją Moja Biedronka”*, *„2+1 gratis”*, *„kup 2 i zapłać mniej”*)
  - Okres obowiązywania oferty
- **Inteligentne wyszukiwanie & RAG**:
  - Wyszukiwanie semantyczne (np. „dobra kawa ziarnista”, „tanie masło”, „owoce na wagę”)
  - Porównywanie cen jednostkowych (za kg / l / szt.)
- **Rekomendacja i optymalizacja koszyka**:
  - Klient podaje listę zakupów -> Agent analizuje, w którym sklepie zakupy wyjdą najtaniej.
- **Interfejsy**:
  - Interfejs CLI / REST API / Czat interaktywny.

---

## 🏗️ Architektura projektu

```
├── scrapers/          # Moduły pobierające gazetki (Biedronka, Lidl, Auchan itp.)
├── extractor/         # Przetwarzanie PDF/obrazów i ekstrakcja danych przez Vision LLM
├── db/                # Baza danych ofert i indeks wektorowy
├── agent/             # Logika agenta AI, interpretacja zapytań użytkownika i scoring
├── api/               # Interfejs API (FastAPI)
├── cli/               # Narzędzie wiersza poleceń
├── data/              # Pobrane gazetki, cache i pliki tymczasowe (w .gitignore)
└── tests/             # Testy jednostkowe i integracyjne
```

---

## 🚀 Szybki start (wkrótce)

```bash
# Klonowanie repozytorium
git clone https://github.com/JakubMadejski/przegladanie_gazetek.git
cd przegladanie_gazetek

# Środowisko wirtualne
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📄 Licencja

Projekt rozwijany przez [JakubMadejski](https://github.com/JakubMadejski).

