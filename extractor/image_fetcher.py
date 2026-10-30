import re
from typing import Dict, Optional
from .normalizer import strip_accents

# Baza sprawdzonych, darmowych zdjęć produktów z Open Food Facts i otwartych zasobów
PRODUCT_IMAGE_CATALOG: Dict[str, str] = {
    # Energetyki
    "monster": "https://images.openfoodfacts.org/images/products/506/033/750/0394/front_pl.12.400.jpg",
    "red bull": "https://images.openfoodfacts.org/images/products/9002490100070/front_pl.32.400.jpg",
    "tiger": "https://images.openfoodfacts.org/images/products/5900334000325/front_pl.14.400.jpg",
    "black": "https://images.openfoodfacts.org/images/products/5900334000455/front_pl.12.400.jpg",
    "bepower": "https://images.openfoodfacts.org/images/products/5900334000325/front_pl.14.400.jpg",
    "kong strong": "https://images.openfoodfacts.org/images/products/20268593/front_pl.12.400.jpg",
    "level up": "https://images.openfoodfacts.org/images/products/5900334000325/front_pl.14.400.jpg",

    # Wódki & Alkohole
    "zubrowka": "https://images.openfoodfacts.org/images/products/5900343003058/front_pl.7.400.jpg",
    "bocian": "https://images.openfoodfacts.org/images/products/5901583060015/front_pl.6.400.jpg",
    "soplica": "https://images.openfoodfacts.org/images/products/5900343001016/front_pl.8.400.jpg",
    "krupnik": "https://images.openfoodfacts.org/images/products/5900443000049/front_pl.6.400.jpg",
    "wyborowa": "https://images.openfoodfacts.org/images/products/5900343003058/front_pl.7.400.jpg",
    "finlandia": "https://images.openfoodfacts.org/images/products/081128001026/front_pl.8.400.jpg",
    "zywiec": "https://images.openfoodfacts.org/images/products/5901359041019/front_pl.12.400.jpg",
    "tyskie": "https://images.openfoodfacts.org/images/products/5900707000013/front_pl.10.400.jpg",

    # Nabiał i jaja
    "maslo": "https://images.openfoodfacts.org/images/products/5900512300109/front_pl.3.400.jpg",
    "mleko": "https://images.openfoodfacts.org/images/products/5900820000013/front_pl.20.400.jpg",
    "jaja": "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=300&auto=format&fit=crop&q=80",
    "jajka": "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=300&auto=format&fit=crop&q=80",
    "gouda": "https://images.openfoodfacts.org/images/products/5900512100013/front_pl.4.400.jpg",
    "ser": "https://images.openfoodfacts.org/images/products/5900512100013/front_pl.4.400.jpg",

    # Mięso
    "kurczak": "https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=300&auto=format&fit=crop&q=80",
    "filet": "https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=300&auto=format&fit=crop&q=80",
    "schab": "https://images.unsplash.com/photo-1607623814075-e51df1bdc82f?w=300&auto=format&fit=crop&q=80",
    "parowki": "https://images.openfoodfacts.org/images/products/5900751000113/front_pl.5.400.jpg",
    "berlinki": "https://images.openfoodfacts.org/images/products/5900751000113/front_pl.5.400.jpg",
    "hot dog": "https://images.unsplash.com/photo-1619740455993-9e612b1af08a?w=300&auto=format&fit=crop&q=80",

    # Kawa i napoje
    "kawa": "https://images.openfoodfacts.org/images/products/8000070014702/front_pl.5.400.jpg",
    "lavazza": "https://images.openfoodfacts.org/images/products/8000070014702/front_pl.5.400.jpg",
    "jacobs": "https://images.openfoodfacts.org/images/products/8711000508752/front_pl.6.400.jpg",
    "cola": "https://images.openfoodfacts.org/images/products/5449000000996/front_pl.12.400.jpg",
    "coca-cola": "https://images.openfoodfacts.org/images/products/5449000000996/front_pl.12.400.jpg",
    "woda": "https://images.openfoodfacts.org/images/products/5900247000014/front_pl.4.400.jpg",

    # Owoce i warzywa
    "banan": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=300&auto=format&fit=crop&q=80",
    "banany": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=300&auto=format&fit=crop&q=80",
    "jablka": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&auto=format&fit=crop&q=80",
    "pomidor": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=300&auto=format&fit=crop&q=80",
    "pomidory": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=300&auto=format&fit=crop&q=80",

    # Przekąski i chemia
    "chipsy": "https://images.openfoodfacts.org/images/products/5900259099419/front_pl.15.400.jpg",
    "lays": "https://images.openfoodfacts.org/images/products/5900259099419/front_pl.15.400.jpg",
    "czekolada": "https://images.openfoodfacts.org/images/products/7622210286148/front_pl.14.400.jpg",
    "milka": "https://images.openfoodfacts.org/images/products/7622210286148/front_pl.14.400.jpg",
    "olej": "https://images.openfoodfacts.org/images/products/5900703000018/front_pl.5.400.jpg",
    "kujawski": "https://images.openfoodfacts.org/images/products/5900703000018/front_pl.5.400.jpg",
    "papier": "https://images.unsplash.com/photo-1584556812952-905ffd0c611a?w=300&auto=format&fit=crop&q=80",
    "ariel": "https://images.openfoodfacts.org/images/products/8001090442345/front_pl.6.400.jpg",
    "kapsulki": "https://images.openfoodfacts.org/images/products/8001090442345/front_pl.6.400.jpg",
}

DEFAULT_CATEGORY_FALLBACK = {
    "Napoje i kawa": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=300&auto=format&fit=crop&q=80",
    "Alkohole": "https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?w=300&auto=format&fit=crop&q=80",
    "Nabiał i jaja": "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=300&auto=format&fit=crop&q=80",
    "Mięso i wędliny": "https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=300&auto=format&fit=crop&q=80",
    "Owoce i warzywa": "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=300&auto=format&fit=crop&q=80",
    "Słodycze i przekąski": "https://images.unsplash.com/photo-1582293041079-7814c2f12063?w=300&auto=format&fit=crop&q=80",
    "Chemia i kosmetyki": "https://images.unsplash.com/photo-1584556812952-905ffd0c611a?w=300&auto=format&fit=crop&q=80",
    "Podstawowe produkty": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&auto=format&fit=crop&q=80"
}


def get_product_image_url(product_name: str, category: Optional[str] = None) -> str:
    """Zwraca bezpośredni URL do darmowego zdjęcia produktu na podstawie nazwy lub kategorii."""
    norm = strip_accents(product_name)

    # 1. Sprawdzamy słowa kluczowe w nazwie produktu
    for keyword, url in PRODUCT_IMAGE_CATALOG.items():
        if keyword in norm:
            return url

    # 2. Sprawdzamy poszczególne słowa
    tokens = [t for t in norm.split() if len(t) > 2]
    for tok in tokens:
        if tok in PRODUCT_IMAGE_CATALOG:
            return PRODUCT_IMAGE_CATALOG[tok]

    # 3. Fallback na kategorię
    if category and category in DEFAULT_CATEGORY_FALLBACK:
        return DEFAULT_CATEGORY_FALLBACK[category]

    return "https://images.unsplash.com/photo-1542838132-92c53300491e?w=300&auto=format&fit=crop&q=80"

