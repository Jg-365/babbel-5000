import re
from collections import Counter
from typing import Iterable

SUPPORTED_LANGS = ["de", "en", "es", "pt"]


def detect_language(data: Iterable[int]) -> str:
    sample = bytes(data)
    letters = sample.decode(errors="ignore")
    lang_scores = {
        "de": len(re.findall(r"[äöüß]", letters.lower())) + letters.lower().count("der"),
        "es": len(re.findall(r"[áéíóúñ]", letters.lower())) + letters.lower().count("que"),
        "pt": len(re.findall(r"[ãõáéíóúç]", letters.lower())) + letters.lower().count(" que"),
        "en": len(re.findall(r"[a-z]", letters.lower())),
    }
    selected = max(lang_scores, key=lang_scores.get)
    if lang_scores[selected] == 0:
        selected = "en"
    return selected


def normalize_lang(lang: str) -> str:
    if lang in SUPPORTED_LANGS:
        return lang
    lang = lang.lower()
    if lang.startswith("en"):
        return "en"
    if lang.startswith("de"):
        return "de"
    if lang.startswith("es"):
        return "es"
    if lang.startswith("pt"):
        return "pt"
    return "en"


def majority_vote_lang(langs: Iterable[str]) -> str:
    filtered = [normalize_lang(lang) for lang in langs if lang]
    if not filtered:
        return "en"
    counter = Counter(filtered)
    return counter.most_common(1)[0][0]
