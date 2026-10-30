import difflib
from typing import Dict, Iterable, List, Optional, Set, Tuple
from .normalizer import strip_accents


def damerau_levenshtein_distance(s1: str, s2: str) -> int:
    """Oblicza odległość Damerau-Levenshteina (uwzględnia zamiany sąsiednich liter, usunięcia, wstawienia)."""
    d: Dict[Tuple[int, int], int] = {}
    len1 = len(s1)
    len2 = len(s2)

    for i in range(-1, len1 + 1):
        d[(i, -1)] = i + 1
    for j in range(-1, len2 + 1):
        d[(-1, j)] = j + 1

    for i in range(len1):
        for j in range(len2):
            cost = 0 if s1[i] == s2[j] else 1
            d[(i, j)] = min(
                d[(i - 1, j)] + 1,        # usunięcie
                d[(i, j - 1)] + 1,        # wstawienie
                d[(i - 1, j - 1)] + cost   # zamiana
            )
            if i > 0 and j > 0 and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                d[(i, j)] = min(d[(i, j)], d[(i - 2, j - 2)] + cost)  # transpozycja sąsiednich liter

    return d[(len1 - 1, len2 - 1)]


def find_best_typo_match(word: str, candidates: Iterable[str]) -> Optional[str]:
    """Znajduje najlepiej pasujące słowo z listy kandydatów przy literówkach."""
    norm_word = strip_accents(word)
    if len(norm_word) < 3:
        return None

    # Dopuszczalny próg błędów w zależności od długości słowa
    max_dist = 1 if len(norm_word) <= 5 else 2

    best_match = None
    min_dist = max_dist + 1

    for cand in candidates:
        norm_cand = strip_accents(cand)
        # Szybkie odrzucenie jeśli różnica długości jest zbyt duża
        if abs(len(norm_word) - len(norm_cand)) > max_dist:
            continue

        dist = damerau_levenshtein_distance(norm_word, norm_cand)
        if dist <= max_dist and dist < min_dist:
            min_dist = dist
            best_match = cand

    # Fallback: difflib przy dłuższych słowach
    if not best_match and len(norm_word) >= 5:
        close = difflib.get_close_matches(norm_word, list(candidates), n=1, cutoff=0.68)
        if close:
            best_match = close[0]

    return best_match


def correct_query_typos(query: str, vocabulary: Iterable[str]) -> Tuple[str, bool]:
    """Poprawia literówki w całym zapytaniu na podstawie dostępnego słownika."""
    norm_query = strip_accents(query)
    words = norm_query.split()
    corrected_words = []
    has_corrections = False

    cand_list = set(vocabulary)

    for w in words:
        if len(w) <= 2:
            corrected_words.append(w)
            continue

        # Jeśli słowo już idealnie pasuje
        if w in cand_list:
            corrected_words.append(w)
            continue

        # Szukamy korekty
        match = find_best_typo_match(w, cand_list)
        if match and match != w:
            corrected_words.append(match)
            has_corrections = True
        else:
            corrected_words.append(w)

    return " ".join(corrected_words), has_corrections
