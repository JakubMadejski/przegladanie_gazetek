import re
import unicodedata
from typing import Optional, Tuple


def strip_accents(text: str) -> str:
    """Zamienia polskie znaki diakrytyczne na ich łacińskie odpowiedniki."""
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
    return ''.join(c for c in text if not unicodedata.combining(c))


def parse_price(price_str: str) -> Optional[float]:
    """Konwertuje napis cenowy np. '3,99', '19.99 zł', '4 99' na float."""
    if not price_str:
        return None
    cleaned = price_str.strip().lower()
    cleaned = cleaned.replace("zł", "").replace("zl", "").replace("pln", "").strip()
    # Zamiana przecinka na kropkę
    cleaned = cleaned.replace(",", ".")
    # Wyciągamy pierwszy wzorzec liczbowy typu 12.34 lub 12
    match = re.search(r"(\d+(?:\.\d{1,2})?)", cleaned)
    if match:
        try:
            return round(float(match.group(1)), 2)
        except ValueError:
            return None
    return None


def extract_unit_and_quantity(text: str) -> Tuple[str, float]:
    """Wyciąga jednostkę i ilość z nazwy produktu (np. '1kg', '500g', '1.5l', '10 szt')."""
    if not text:
        return ("szt.", 1.0)
    
    text_lower = text.lower()

    # Waga w kg lub g
    kg_match = re.search(r"(\d+(?:[.,]\d+)?)\s*kg", text_lower)
    if kg_match:
        qty = float(kg_match.group(1).replace(",", "."))
        return ("kg", qty)

    g_match = re.search(r"(\d+)\s*g\b", text_lower)
    if g_match:
        qty = float(g_match.group(1)) / 1000.0
        return ("kg", qty)

    # Objętość w l lub ml
    l_match = re.search(r"(\d+(?:[.,]\d+)?)\s*l\b", text_lower)
    if l_match:
        qty = float(l_match.group(1).replace(",", "."))
        return ("l", qty)

    ml_match = re.search(r"(\d+)\s*ml\b", text_lower)
    if ml_match:
        qty = float(ml_match.group(1)) / 1000.0
        return ("l", qty)

    # Sztuki / jaja
    szt_match = re.search(r"(\d+)\s*(?:szt|sztuk|jaj|opak)\b", text_lower)
    if szt_match:
        qty = float(szt_match.group(1))
        return ("szt.", qty)

    return ("szt.", 1.0)


def detect_category(name: str) -> str:
    """Automatyczne przypisanie kategorii produktu na podstawie słów kluczowych."""
    norm = strip_accents(name)

    categories = {
        "Nabiał i jaja": ["maslo", "mleko", "ser", "twarog", "jogurt", "smietana", "jaja", "jajka", "kefir", "maslanka"],
        "Mięso i wędliny": ["kurczak", "filet", "schab", "szynka", "kielbasa", "mieso", "parowki", "boczek", "karkowka", "mielone", "indyka", "wolowina"],
        "Owoce i warzywa": ["jablka", "banany", "cytryny", "pomidory", "ogorki", "ziemniaki", "cebula", "marchew", "papryka", "pomarancze", "winogrona", "mandarynki"],
        "Napoje i kawa": ["kawa", "herbata", "sok", "woda", "pepsi", "coca-cola", "cola", "napoj", "energetyk"],
        "Alkohole": ["wodka", "piwo", "wino", "whisky", "soplica", "zubrowka", "bocian", "wyborowa", "finlandia", "krupnik", "gin", "rum", "browar"],
        "Słodycze i przekąski": ["czekolada", "baton", "ciastka", "chipsy", "chrupki", "orzechy", "zelki", "wafel"],
        "Pieczywo": ["chleb", "bulka", "kajzerka", "bagietka", "rogal"],
        "Chemia i kosmetyki": ["proszek", "plyn", "kapsulki", "szampon", "mydlo", "papier", "zel", "pasta", "persil", "ariel"],
        "Podstawowe produkty": ["olej", "maka", "cukier", "ryz", "makaron", "kasza", "sol", "przecier"]
    }

    for cat, keywords in categories.items():
        if any(kw in norm for kw in keywords):
            return cat

    return "Inne"


def detect_conditions(text: str) -> Optional[str]:
    """Wykrywa warunki specjalne promocji (np. karta lojalnościowa, wielopaki)."""
    norm = strip_accents(text)
    conditions = []

    if "aplikacj" in norm or "karta" in norm or "moja biedronka" in norm or "lidl plus" in norm or "skarbonka" in norm or "zappka" in norm or "żappka" in norm or "kaufland" in norm or "carrefour" in norm:
        if "moja biedronka" in norm:
            conditions.append("z aplikacją Moja Biedronka")
        elif "lidl plus" in norm:
            conditions.append("z aplikacją Lidl Plus")
        elif "skarbonka" in norm:
            conditions.append("z kartą Skarbonka Auchan")
        elif "zappka" in norm or "żappka" in norm:
            conditions.append("z aplikacją żappka")
        elif "kaufland" in norm:
            conditions.append("z Kaufland Card")
        elif "carrefour" in norm:
            conditions.append("z aplikacją Mój Carrefour")
        else:
            conditions.append("wymagana aplikacja / karta lojalnościowa")

    if "1+1 gratis" in norm:
        conditions.append("1+1 gratis")
    elif "2+1 gratis" in norm:
        conditions.append("2+1 gratis")
    elif "drugi" in norm and ("taniej" in norm or "%" in norm):
        match = re.search(r"drugi\s+(\d+%)\s+taniej", norm)
        if match:
            conditions.append(f"drugi produkt {match.group(1)} taniej")
        else:
            conditions.append("drugi produkt taniej")
    elif "przy zakupie 2" in norm or "kup 2" in norm:
        conditions.append("przy zakupie min. 2 sztuk")
    elif "przy zakupie 3" in norm or "kup 3" in norm:
        conditions.append("przy zakupie min. 3 sztuk")

    if "limit" in norm:
        match = re.search(r"limit\s+(\d+\s*(?:szt|kg)?)", norm)
        if match:
            conditions.append(f"limit: {match.group(1)}")

    return ", ".join(conditions) if conditions else None

