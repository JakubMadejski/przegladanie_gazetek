from typing import List, Set
from .normalizer import strip_accents

# Słownik synonimów, powiązanych marek i pojęć handlowych w polskich sklepach
SYNONYM_GROUPS = {
    "energetyk": ["energetyczn", "energetyk", "monster", "red bull", "tiger", "black", "bepower", "kong strong"],
    "energetyki": ["energetyczn", "energetyk", "monster", "red bull", "tiger", "black", "bepower", "kong strong"],
    "energy": ["energetyczn", "energetyk", "monster", "red bull", "tiger", "black"],
    "monster": ["monster", "energetyczn"],
    "redbull": ["red bull", "energetyczn"],
    "tiger": ["tiger", "energetyczn"],
    "piwo": ["piwo", "zywiec", "tyskie", "browar", "jasne pelne"],
    "piwa": ["piwo", "zywiec", "tyskie", "browar", "jasne pelne"],
    "chipsy": ["chipsy", "czipsy", "lays", "crunchips", "chrupki"],
    "czipsy": ["chipsy", "czipsy", "lays", "crunchips", "chrupki"],
    "chrupki": ["chipsy", "czipsy", "lays", "crunchips", "chrupki"],
    "parowki": ["parowki", "berlinki", "morliny"],
    "parowka": ["parowki", "berlinki", "morliny"],
    "jajka": ["jaja", "jajka", "chowaniec", "nioska"],
    "jaja": ["jaja", "jajka", "chowaniec", "nioska"],
    "maslo": ["maslo", "mlekovita", "pilos"],
    "mleko": ["mleko", "laciate", "pilos"],
    "kurczak": ["kurczak", "filet", "piers", "rzeznik", "kraina mies"],
    "filet": ["filet", "kurczak", "piers"],
    "schab": ["schab", "wieprzowina", "kraina mies", "rzeznik"],
    "kawa": ["kawa", "lavazza", "jacobs", "tchibo"],
    "papier": ["papier", "velvet", "floralys", "regina"],
    "proszek": ["proszek", "kapsulki", "ariel", "persil"],
    "pranie": ["proszek", "kapsulki", "ariel", "persil"],
    "kapsulki": ["kapsulki", "ariel", "persil", "pranie"],
    "cola": ["coca-cola", "cola", "pepsi"],
    "woda": ["woda", "zywiec zdroj", "saguaro", "cisowianka"],
    "pomidory": ["pomidor", "pomidory", "malinowe"],
    "pomidor": ["pomidor", "pomidory", "malinowe"],
    "jablka": ["jablka", "jablko", "szampion", "ligol", "jonagold"],
    "jablko": ["jablka", "jablko", "szampion", "ligol", "jonagold"],
    "banany": ["banan", "banany"],
    "banan": ["banan", "banany"],
    "ser": ["ser", "gouda", "swiatowid", "pilos"],
    "czekolada": ["czekolada", "milka", "fin carre"],
    "slodycze": ["czekolada", "milka", "baton", "ciastka", "chipsy"]
}

# Końcówki fleksyjne w języku polskim do prostego rdzeniowania (stemmingu)
POLISH_SUFFIXES = [
    "ami", "ach", "ego", "emu", "ych", "ich",
    "owie", "om", "em", "ie", "owi", "ow", "ow",
    "ka", "ki", "ce", "ku", "ek",
    "y", "i", "e", "a", "u", "ą"
]


def stem_polish_word(word: str) -> str:
    """Upraszcza polskie słowo odcinając typowe końcówki deklinacyjne/liczby mnogiej."""
    norm = strip_accents(word)
    if len(norm) <= 3:
        return norm
    for suffix in POLISH_SUFFIXES:
        if norm.endswith(suffix) and len(norm) - len(suffix) >= 3:
            return norm[:-len(suffix)]
    return norm


def expand_search_terms(query: str) -> List[str]:
    """Zwraca listę słów kluczowych i synonimów dla zapytania (np. 'energetyki' -> monster, red bull...)."""
    norm = strip_accents(query)
    tokens = [t for t in norm.split() if len(t) > 1]
    
    expanded: Set[str] = set(tokens)

    # 1. Sprawdzamy bezpośrednie synonimy całego zapytania
    if norm in SYNONYM_GROUPS:
        for syn in SYNONYM_GROUPS[norm]:
            expanded.add(syn)

    # 2. Sprawdzamy per token
    for tok in tokens:
        if tok in SYNONYM_GROUPS:
            for syn in SYNONYM_GROUPS[tok]:
                expanded.add(syn)
        
        # Sprawdzamy po rdzeniu słowa
        stem = stem_polish_word(tok)
        expanded.add(stem)
        for key, syns in SYNONYM_GROUPS.items():
            if stem == stem_polish_word(key):
                for syn in syns:
                    expanded.add(syn)

    return list(expanded)
