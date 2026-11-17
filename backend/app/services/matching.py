"""Similarity scoring for lost and found item reports.

The engine compares two reports field by field. Text fields are normalised,
lightly stemmed and mapped onto small product/colour taxonomies so that
"Iqoo z10" and "Phone" can be recognised as the same kind of object even
though they share no words. Each field score blends token overlap, character
n-grams and fuzzy token matching, then the field scores are combined with
weights and a small, bounded bonus for corroborating evidence.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from difflib import SequenceMatcher
from typing import Any

# Relative importance of each field when comparing two reports.
FIELD_WEIGHTS = {
    "item_name": 0.32,
    "description": 0.15,
    "category": 0.12,
    "color": 0.14,
    "location_text": 0.14,
    "brand": 0.08,
    "date": 0.05,
}

FIELD_LABELS = {
    "item_name": "item name",
    "description": "description",
    "category": "category",
    "color": "color",
    "brand": "brand",
    "location_text": "location",
    "date": "date",
}

# Multi-word phrases are replaced before tokenisation so "water bottle" and
# "id card" do not lose their meaning.
PHRASE_SYNONYMS = {
    "cell phone": "phone",
    "mobile phone": "phone",
    "smart phone": "phone",
    "water bottle": "bottle",
    "water flask": "bottle",
    "id card": "id",
    "identity card": "id",
    "power bank": "powerbank",
    "air pods": "earphones",
    "ear buds": "earphones",
    "ear phones": "earphones",
    "head phones": "headphones",
    "key chain": "keychain",
    "charging cable": "cable",
    "usb cable": "cable",
    "pen drive": "pendrive",
    "flash drive": "pendrive",
    "usb drive": "pendrive",
    "thumb drive": "pendrive",
    "memory card": "memorycard",
    "hard disk": "harddisk",
    "bluetooth speaker": "speaker",
    "tiffin box": "lunchbox",
    "lunch box": "lunchbox",
    "note book": "notebook",
    "lap top": "laptop",
    "bus stop": "bus stand",
    "busstop": "bus stand",
    "computer lab": "lab",
    "science lab": "lab",
    "exam hall": "examhall",
    "food court": "canteen",
    "american tourister": "americantourister",
}

# Single-word spelling variants mapped to one canonical word.
SYNONYMS = {
    "mobile": "phone",
    "mobiles": "phone",
    "cellphone": "phone",
    "cellphones": "phone",
    "smartphone": "phone",
    "smartphones": "phone",
    "phones": "phone",
    "telephone": "phone",
    "notebooks": "notebook",
    "notepad": "notebook",
    "purse": "wallet",
    "wallets": "wallet",
    "billfold": "wallet",
    "backpack": "bag",
    "bagpack": "bag",
    "rucksack": "bag",
    "handbag": "bag",
    "bags": "bag",
    "earbud": "earphones",
    "earbuds": "earphones",
    "earphone": "earphones",
    "airpods": "earphones",
    "airpod": "earphones",
    "headphone": "headphones",
    "headset": "headphones",
    "spectacles": "glasses",
    "eyeglasses": "glasses",
    "sunglass": "sunglasses",
    "flask": "bottle",
    "waterbottle": "bottle",
    "bottles": "bottle",
    "sipper": "bottle",
    "tumbler": "bottle",
    "cycle": "bicycle",
    "bike": "bicycle",
    "bicycles": "bicycle",
    "idcard": "id",
    "identitycard": "id",
    "aadhaar": "aadhar",
    "licence": "license",
    "keychain": "keychain",
    "keys": "key",
    "adaptor": "adapter",
    "powerbank": "powerbank",
    "powerbanks": "powerbank",
    "laptops": "laptop",
    "tiffin": "lunchbox",
    "smartwatch": "watch",
    "watches": "watch",
    "shoes": "shoe",
    "sneakers": "sneaker",
    "boots": "boot",
    "slippers": "slipper",
    "sandals": "sandal",
    "chappal": "slipper",
    "chappals": "slipper",
    "flipflop": "slipper",
    "flipflops": "slipper",
    "trousers": "trouser",
    "glasses": "glasses",
    "spectacle": "glasses",
    "pendrive": "pendrive",
    "pendrives": "pendrive",
    "flashdrive": "pendrive",
    "thumbdrive": "pendrive",
    "usbdrive": "pendrive",
    "memorystick": "pendrive",
    "harddisk": "harddisk",
    "memorycard": "memorycard",
    "speakers": "speaker",
    "soundbar": "speaker",
    "documents": "document",
    "docs": "document",
    "certificates": "certificate",
    "marksheets": "marksheet",
    "colour": "color",
    "colours": "color",
    "gray": "grey",
    "blk": "black",
    "wht": "white",
    "blu": "blue",
    "grn": "green",
    "rd": "red",
    "choclate": "chocolate",
    "chocolates": "chocolate",
}

# Tokens that carry little matching signal on their own.
STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "of",
    "with",
    "without",
    "for",
    "from",
    "by",
    "in",
    "on",
    "at",
    "to",
    "into",
    "near",
    "around",
    "beside",
    "behind",
    "inside",
    "outside",
    "my",
    "our",
    "your",
    "his",
    "her",
    "their",
    "its",
    "it",
    "this",
    "that",
    "these",
    "those",
    "i",
    "we",
    "he",
    "she",
    "they",
    "me",
    "us",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "have",
    "has",
    "had",
    "when",
    "while",
    "then",
    "than",
    "so",
    "very",
    "some",
    "any",
    "all",
    "please",
    "help",
    "lost",
    "lose",
    "losing",
    "found",
    "find",
    "finding",
    "missing",
    "item",
    "thing",
    "object",
    "someone",
    "somebody",
    "somewhere",
    "anywhere",
}

_WORD_RE = re.compile(r"[^a-z0-9\s]+")
_CAMEL_RE = re.compile(r"(?<=[a-z])(?=\d)|(?<=\d)(?=[a-z])")
_NO_STEM = {
    "glasses",
    "canvas",
    "campus",
    "status",
    "series",
    "species",
    "news",
    "shorts",
    "jeans",
}

# Product taxonomies. Two reports whose item/category words land in the same
# group are treated as the same kind of object even if the wording differs.
CONCEPT_GROUPS = {
    "phone": {
        "phone",
        "iphone",
        "android",
        "samsung",
        "galaxy",
        "redmi",
        "realme",
        "oppo",
        "vivo",
        "oneplus",
        "poco",
        "nothing",
        "motorola",
        "moto",
        "nokia",
        "pixel",
        "honor",
        "infinix",
        "tecno",
        "lava",
        "micromax",
        "iqoo",
    },
    "laptop": {
        "laptop",
        "macbook",
        "dell",
        "lenovo",
        "thinkpad",
        "ideapad",
        "asus",
        "vivobook",
        "acer",
        "aspire",
        "hp",
        "pavilion",
        "inspiron",
        "victus",
        "omen",
        "chromebook",
        "ultrabook",
    },
    "tablet": {"tablet", "ipad", "tab"},
    "earphones": {
        "earphones",
        "headphones",
        "airpods",
        "buds",
        "headset",
        "earbud",
    },
    "speaker": {"speaker", "soundbar"},
    "watch": {"watch", "smartwatch", "fitbit", "fireboltt", "smartband", "fitnessband"},
    "wallet": {"wallet", "purse", "billfold"},
    "bag": {
        "bag",
        "backpack",
        "rucksack",
        "handbag",
        "sling",
        "trolley",
        "luggage",
        "suitcase",
    },
    "bottle": {"bottle", "flask", "sipper", "tumbler"},
    "key": {"key", "keychain"},
    "glasses": {"glasses", "spectacles", "sunglasses", "goggles"},
    "id": {
        "id",
        "aadhar",
        "pan",
        "license",
        "passport",
        "card",
        "identity",
        "document",
        "certificate",
        "marksheet",
    },
    "book": {"book", "notebook", "diary", "register", "novel", "textbook"},
    "charger": {"charger", "adapter", "cable", "powerbank"},
    "storage": {
        "pendrive",
        "usb",
        "flashdrive",
        "harddisk",
        "memorycard",
        "sd",
        "drive",
    },
    "mouse": {"mouse"},
    "keyboard": {"keyboard"},
    "umbrella": {"umbrella"},
    "calculator": {"calculator"},
    "lunchbox": {"lunchbox", "tiffin"},
    "pen": {"pen", "ballpoint", "gelpen"},
    "pencil": {"pencil", "mechanicalpencil"},
    "stationery": {"eraser", "sharpener", "scale", "ruler", "geometrybox"},
    "upperwear": {
        "shirt",
        "tshirt",
        "tee",
        "top",
        "blouse",
        "hoodie",
        "sweater",
        "sweatshirt",
        "jacket",
        "blazer",
        "coat",
        "uniform",
    },
    "lowerwear": {"trouser", "pant", "jeans", "shorts", "skirt"},
    "footwear": {"shoe", "sandal", "slipper", "sneaker", "boot"},
    "headwear": {"cap", "hat"},
    "jewellery": {
        "ring",
        "chain",
        "bracelet",
        "earring",
        "necklace",
        "anklet",
        "pendant",
    },
}

TOKEN_TO_CONCEPT: dict[str, str] = {}
for _concept, _words in CONCEPT_GROUPS.items():
    for _word in _words:
        TOKEN_TO_CONCEPT.setdefault(_word, _concept)

# Brand names map to a canonical brand so "iPhone" and "Apple" match.
BRAND_ALIASES = {
    "iphone": "apple",
    "ipad": "apple",
    "macbook": "apple",
    "galaxy": "samsung",
    "redmi": "xiaomi",
    "poco": "xiaomi",
    "mi": "xiaomi",
    "oneplus": "oneplus",
    "iqoo": "iqoo",
    "vivo": "vivo",
    "oppo": "oppo",
    "realme": "realme",
    "samsung": "samsung",
    "nothing": "nothing",
    "motorola": "motorola",
    "moto": "motorola",
    "nokia": "nokia",
    "pixel": "google",
    "honor": "honor",
    "infinix": "infinix",
    "tecno": "tecno",
    "lava": "lava",
    "micromax": "micromax",
    "dell": "dell",
    "lenovo": "lenovo",
    "thinkpad": "lenovo",
    "ideapad": "lenovo",
    "asus": "asus",
    "vivobook": "asus",
    "acer": "acer",
    "aspire": "acer",
    "hp": "hp",
    "pavilion": "hp",
    "inspiron": "dell",
    "victus": "hp",
    "omen": "hp",
    "boat": "boat",
    "noise": "noise",
    "fireboltt": "fireboltt",
    "fitbit": "fitbit",
    "apple": "apple",
    "casio": "casio",
    "fastrack": "fastrack",
    "titan": "titan",
    "sonata": "sonata",
    "milton": "milton",
    "cello": "cello",
    "borosil": "borosil",
    "sandisk": "sandisk",
    "sony": "sony",
    "jbl": "jbl",
    "bose": "bose",
    "boult": "boult",
    "msi": "msi",
    "gigabyte": "gigabyte",
    "zebronics": "zebronics",
    "philips": "philips",
    "skybags": "skybags",
    "wildcraft": "wildcraft",
    "americantourister": "american tourister",
}

# Colour families let "navy" match "blue" and "ivory" match "white".
COLOR_FAMILIES = {
    "black": {"black", "charcoal", "jet", "onyx", "ebony"},
    "white": {"white", "ivory", "cream", "offwhite", "pearl"},
    "grey": {"grey", "gray", "silver", "ash", "graphite"},
    "blue": {"blue", "navy", "cyan", "teal", "turquoise", "skyblue", "darkblue", "lightblue"},
    "red": {"red", "maroon", "crimson", "scarlet", "burgundy", "wine", "rose"},
    "green": {"green", "olive", "mint", "emerald", "lime", "sage"},
    "yellow": {"yellow", "gold", "golden", "mustard", "amber"},
    "orange": {"orange", "peach", "coral"},
    "pink": {"pink", "magenta", "fuchsia"},
    "purple": {"purple", "violet", "lavender", "indigo"},
    "brown": {"brown", "tan", "beige", "khaki", "coffee", "chocolate"},
    "transparent": {"transparent", "clear", "colourless", "colorless"},
}

COLOR_ALIASES = {
    **{word: family for family, words in COLOR_FAMILIES.items() for word in words},
    "offwhite": "white",
    "skyblue": "blue",
    "darkblue": "blue",
    "lightblue": "blue",
    "multicolor": "multicolor",
    "multicolour": "multicolor",
    "rainbow": "multicolor",
}

RELATED_COLORS = {
    frozenset({"black", "grey"}): 0.55,
    frozenset({"white", "grey"}): 0.6,
    frozenset({"white", "transparent"}): 0.55,
    frozenset({"red", "pink"}): 0.6,
    frozenset({"red", "orange"}): 0.55,
    frozenset({"yellow", "orange"}): 0.6,
    frozenset({"yellow", "brown"}): 0.55,
    frozenset({"blue", "purple"}): 0.5,
    frozenset({"green", "blue"}): 0.45,
    frozenset({"brown", "grey"}): 0.45,
}

GENERIC_ITEM_WORDS = {
    word for words in CONCEPT_GROUPS.values() for word in words
} | {
    "plastic",
    "steel",
    "metal",
    "glass",
    "leather",
    "cotton",
    "wooden",
    "water",
    "reading",
    "school",
    "college",
} | {word for words in COLOR_FAMILIES.values() for word in words}

# Category labels that carry almost no identity on their own. They are ignored
# when comparing categories so "Accessories" vs "Other" does not drag a strong
# item match down.
GENERIC_CATEGORIES = {
    "accessories",
    "accessory",
    "other",
    "others",
    "misc",
    "miscellaneous",
    "general",
    "personal",
    "item",
    "items",
}

# Campus locations are often described with different words ("canteen" vs
# "cafeteria", "bus stop" vs "bus stand"). Matching places earn a floor so a
# strong item pair is not punished for using the local name.
LOCATION_GROUPS = {
    "canteen": {"canteen", "cafeteria", "cafe", "mess", "foodcourt"},
    "library": {"library", "lib"},
    "hostel": {"hostel", "room", "block", "warden"},
    "lab": {"lab", "laboratory", "computerlab"},
    "examhall": {"examhall", "hall"},
    "ground": {"ground", "playground", "sports", "stadium", "court"},
    "busstand": {"busstand", "bus", "stop"},
    "parking": {"parking", "parkinglot", "bikeparking", "carparking"},
    "gate": {"gate", "entrance"},
    "classroom": {"classroom", "class"},
}

TOKEN_TO_LOCATION: dict[str, str] = {}
for _location, _words in LOCATION_GROUPS.items():
    for _word in _words:
        TOKEN_TO_LOCATION.setdefault(_word, _location)


def _stem(token: str) -> str:
    """Very light plural stemming that leaves short words alone."""

    if token in _NO_STEM or len(token) <= 3:
        return token

    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"

    if token.endswith(("ches", "shes", "sses", "xes", "zes")):
        return token[:-2]

    if token.endswith("s") and not token.endswith(("ss", "us", "is", "os", "as")):
        return token[:-1]

    return token


def _canonical_token(token: str) -> str:
    token = SYNONYMS.get(token, token)
    token = _stem(token)
    return SYNONYMS.get(token, token)


def _prepare(value: Any) -> tuple[list[str], str]:
    """Return content tokens and a normalised text string for a field."""

    text = unicodedata.normalize("NFKC", str(value or "")).casefold()

    for phrase, replacement in PHRASE_SYNONYMS.items():
        text = re.sub(rf"\b{re.escape(phrase)}\b", replacement, text)

    text = _WORD_RE.sub(" ", text)
    text = _CAMEL_RE.sub(" ", text)

    tokens: list[str] = []

    for raw_token in text.split():
        token = _canonical_token(raw_token)

        if not token or token in STOPWORDS:
            continue

        tokens.append(token)

    return tokens, " ".join(tokens)


def _char_ngrams(text: str, size: int) -> set[str]:
    padded = f" {text} "
    return {padded[index : index + size] for index in range(len(padded) - size + 1)}


def _char_similarity(text_a: str, text_b: str) -> float:
    """Dice similarity over bigrams and trigrams."""

    if not text_a or not text_b:
        return 0.0

    grams_a = _char_ngrams(text_a, 2) | _char_ngrams(text_a, 3)
    grams_b = _char_ngrams(text_b, 2) | _char_ngrams(text_b, 3)
    total = len(grams_a) + len(grams_b)

    return 2 * len(grams_a & grams_b) / total if total else 0.0


def _token_coverage(tokens_a: set[str], tokens_b: set[str]) -> float:
    """How much of the smaller token set is covered by the larger one.

    Exact tokens count fully; near-spelling variants (typos, abbreviations)
    count when they are close enough. This keeps "blue bottle" and
    "bottle blue plastic" strongly related without rewarding unrelated words.
    """

    if not tokens_a or not tokens_b:
        return 0.0

    if len(tokens_a) > len(tokens_b):
        tokens_a, tokens_b = tokens_b, tokens_a

    total = 0.0

    for token in tokens_a:
        if token in tokens_b:
            total += 1.0
            continue

        if len(token) < 4:
            continue

        best = 0.0

        for other in tokens_b:
            if len(other) < 4:
                continue

            ratio = SequenceMatcher(None, token, other).ratio()

            if ratio >= 0.78:
                best = max(best, ratio)

        total += best

    return total / len(tokens_a)


def _fuzzy_token_similarity(tokens_a: set[str], tokens_b: set[str]) -> float:
    """Average best spelling similarity for tokens in the smaller set."""

    if not tokens_a or not tokens_b:
        return 0.0

    if len(tokens_a) > len(tokens_b):
        tokens_a, tokens_b = tokens_b, tokens_a

    scores = []

    for token in tokens_a:
        best = 0.0

        for other in tokens_b:
            if len(token) < 4 and len(other) < 4:
                continue

            ratio = SequenceMatcher(None, token, other).ratio()

            if ratio >= 0.78:
                best = max(best, ratio)

        scores.append(best)

    return sum(scores) / len(scores) if scores else 0.0


def _text_similarity(
    value_a: Any,
    value_b: Any,
    *,
    containment_cap: float = 0.95,
) -> float | None:
    """Blend token, character and fuzzy similarity for two text fields."""

    tokens_a, text_a = _prepare(value_a)
    tokens_b, text_b = _prepare(value_b)

    if not tokens_a and not tokens_b:
        return None

    if not tokens_a or not tokens_b:
        return 0.0

    if text_a == text_b:
        return 1.0

    set_a, set_b = set(tokens_a), set(tokens_b)
    shared = set_a & set_b
    dice = 2 * len(shared) / (len(set_a) + len(set_b))
    containment = len(shared) / min(len(set_a), len(set_b)) * containment_cap
    jaccard = len(shared) / len(set_a | set_b)
    fuzzy_score = _fuzzy_token_similarity(set_a, set_b)
    coverage = _token_coverage(set_a, set_b) * containment_cap

    # Character n-grams and whole-string edits absorb typos and phrasing
    # differences. When there are no shared content tokens we still allow a
    # reduced contribution so related reports described differently can match,
    # but keep it conservative to avoid inventing similarity from noise.
    char_raw = _char_similarity(text_a, text_b)
    sequence_raw = SequenceMatcher(None, text_a, text_b).ratio()
    if shared:
        char_score = char_raw
        sequence_score = sequence_raw * 0.95
    else:
        char_score = char_raw * 0.45
        sequence_score = sequence_raw * 0.4

    return min(
        max(
            dice,
            containment,
            jaccard,
            char_score,
            sequence_score,
            fuzzy_score,
            coverage,
        ),
        1.0,
    )


def _concepts(tokens: list[str]) -> set[str]:
    return {
        TOKEN_TO_CONCEPT[token]
        for token in tokens
        if token in TOKEN_TO_CONCEPT
    }


def _brands_from_tokens(tokens: list[str]) -> set[str]:
    return {
        BRAND_ALIASES[token]
        for token in tokens
        if token in BRAND_ALIASES
    }


def _report_brand_tokens(report: dict[str, Any]) -> set[str]:
    brands = _brands_from_tokens(_prepare(report.get("brand"))[0])
    brands |= _brands_from_tokens(_prepare(report.get("item_name"))[0])
    return brands


def _item_similarity(
    report_a: dict[str, Any],
    report_b: dict[str, Any],
) -> float | None:
    tokens_a, _ = _prepare(report_a.get("item_name"))
    tokens_b, _ = _prepare(report_b.get("item_name"))

    if not tokens_a and not tokens_b:
        return None
    if not tokens_a or not tokens_b:
        return 0.0

    score = _text_similarity(
        report_a.get("item_name"),
        report_b.get("item_name"),
        containment_cap=0.98,
    ) or 0.0

    concepts_a = _concepts(tokens_a)
    concepts_b = _concepts(tokens_b)
    shared_concepts = concepts_a & concepts_b

    brand_a = _brands_from_tokens(tokens_a)
    brand_b = _brands_from_tokens(tokens_b)

    def is_generic(tokens: list[str]) -> bool:
        return (
            0 < len(tokens) <= 2
            and all(token in GENERIC_ITEM_WORDS for token in tokens)
            and not _brands_from_tokens(tokens)
        )

    generic_a = is_generic(tokens_a)
    generic_b = is_generic(tokens_b)

    if shared_concepts:
        score = max(score, 0.70)

        if generic_a or generic_b:
            # One report only says "Phone"; the other has the model. Treat the
            # generic title as compatible with a specific item of that family.
            if brand_a and brand_b and (brand_a & brand_b):
                score = max(score, 0.96)
            else:
                score = max(score, 0.92 if (brand_a or brand_b) else 0.86)
        else:
            if brand_a and brand_b and (brand_a & brand_b):
                score = max(score, 0.90)
            elif brand_a or brand_b:
                score = max(score, 0.82)
            else:
                score = max(score, 0.78)

    if brand_a and brand_b:
        if brand_a & brand_b:
            score = max(score, 0.9)
        else:
            # Two clearly different brands should not look like the same item.
            score = min(max(score, 0.5), 0.6)

    numbers_a = {token for token in tokens_a if token.isdigit()}
    numbers_b = {token for token in tokens_b if token.isdigit()}

    if numbers_a and numbers_b:
        if numbers_a & numbers_b:
            score = max(score, 0.88)
        else:
            score = min(score, 0.75)

    return min(score, 1.0)


def _category_similarity(
    report_a: dict[str, Any],
    report_b: dict[str, Any],
) -> float | None:
    tokens_a, _ = _prepare(report_a.get("category"))
    tokens_b, _ = _prepare(report_b.get("category"))

    if not tokens_a and not tokens_b:
        return None

    if _concepts(tokens_a) & _concepts(tokens_b):
        return 1.0

    generic_a = bool(tokens_a) and all(
        token in GENERIC_CATEGORIES for token in tokens_a
    )
    generic_b = bool(tokens_b) and all(
        token in GENERIC_CATEGORIES for token in tokens_b
    )

    # "Accessories" or "Other" says nothing about the item. Ignoring the field
    # lets the item, colour and location evidence decide the score.
    if generic_a and generic_b:
        return None

    if generic_a or generic_b:
        return 0.45

    return _text_similarity(
        report_a.get("category"),
        report_b.get("category"),
        containment_cap=0.95,
    )


def _color_families(value: Any) -> set[str]:
    families = set()

    for token in _prepare(value)[0]:
        family = COLOR_ALIASES.get(token)

        if family:
            families.add(family)

    return families


def _color_similarity(
    report_a: dict[str, Any],
    report_b: dict[str, Any],
) -> float | None:
    value_a = report_a.get("color")
    value_b = report_b.get("color")

    if not str(value_a or "").strip() and not str(value_b or "").strip():
        return None

    families_a = _color_families(value_a)
    families_b = _color_families(value_b)

    if families_a and families_b:
        if families_a == families_b:
            return 1.0

        if "multicolor" in families_a or "multicolor" in families_b:
            return 0.6

        best = 0.0

        for family_a in families_a:
            for family_b in families_b:
                if family_a == family_b:
                    best = max(best, 1.0)
                else:
                    best = max(
                        best,
                        RELATED_COLORS.get(frozenset({family_a, family_b}), 0.05),
                    )

        return best

    return _text_similarity(value_a, value_b, containment_cap=0.9)


def _brand_similarity(
    report_a: dict[str, Any],
    report_b: dict[str, Any],
) -> float | None:
    brands_a = _report_brand_tokens(report_a)
    brands_b = _report_brand_tokens(report_b)

    if not brands_a or not brands_b:
        return None

    if brands_a & brands_b:
        return 1.0

    return 0.0


def _location_concepts(value: Any) -> set[str]:
    """Small set of campus place families used to bridge local wording."""

    return {
        TOKEN_TO_LOCATION[token]
        for token in _prepare(value)[0]
        if token in TOKEN_TO_LOCATION
    }


def _location_similarity(
    report_a: dict[str, Any],
    report_b: dict[str, Any],
) -> float | None:
    value_a = report_a.get("location_text")
    value_b = report_b.get("location_text")

    score = _text_similarity(value_a, value_b, containment_cap=0.95)

    if _location_concepts(value_a) & _location_concepts(value_b):
        # "Cafeteria" and "canteen" are the same place even if the text shares
        # no words, so give a strong floor to the match.
        score = max(score or 0.0, 0.88)

    return score


def _parse_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    if not value:
        return None

    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def _date_similarity(
    report_a: dict[str, Any],
    report_b: dict[str, Any],
) -> float | None:
    date_a = _parse_date(report_a.get("event_date") or report_a.get("date"))
    date_b = _parse_date(report_b.get("event_date") or report_b.get("date"))

    if not date_a or not date_b:
        return None

    days = abs((date_a - date_b).days)

    if days <= 1:
        return 1.0
    if days <= 3:
        return 0.95
    if days <= 7:
        return 0.85
    if days <= 14:
        return 0.7
    if days <= 30:
        return 0.5
    if days <= 60:
        return 0.3
    return 0.15


def _field_similarities(
    lost_report: dict[str, Any],
    found_report: dict[str, Any],
) -> dict[str, float]:
    return {
        "item_name": _item_similarity(lost_report, found_report),
        "description": _text_similarity(
            lost_report.get("description"),
            found_report.get("description"),
            containment_cap=0.85,
        ),
        "category": _category_similarity(lost_report, found_report),
        "color": _color_similarity(lost_report, found_report),
        "brand": _brand_similarity(lost_report, found_report),
        "location_text": _location_similarity(lost_report, found_report),
        "date": _date_similarity(lost_report, found_report),
    }


def _evidence_bonus(fields: dict[str, float]) -> float:
    """Reward several independent fields pointing at the same pair.

    A weighted average can look lukewarm even when most fields agree. The
    bonus is capped so a single loose field cannot lift an unrelated pair over
    the match threshold.
    """

    item = fields.get("item_name") or 0
    category = fields.get("category") or 0
    color = fields.get("color") or 0
    location = fields.get("location_text") or 0
    brand = fields.get("brand") or 0
    event_date = fields.get("date") or 0
    description = fields.get("description") or 0

    supporting = 0

    if item >= 0.7:
        supporting += 1
    if category >= 0.8:
        supporting += 1
    if color >= 0.75:
        supporting += 1
    if location >= 0.55:
        supporting += 1
    if brand >= 0.85:
        supporting += 1
    if event_date >= 0.7:
        supporting += 1
    if description >= 0.55:
        supporting += 1

    bonus = 0.0

    if supporting >= 2:
        bonus += supporting * 1.6

    # Strong core identity (same kind of item/category/brand) with at least one
    # corroborating detail deserves a meaningful lift even when wording differs.
    if item >= 0.8 and category >= 0.8 and (color >= 0.7 or location >= 0.45 or brand >= 0.85):
        bonus += 3.0

    if item >= 0.75 and location >= 0.7 and (color >= 0.6 or event_date >= 0.55):
        bonus += 2.0

    if description >= 0.7 and item >= 0.7:
        bonus += 1.0

    return min(bonus, 10.0)


def score_reports(
    lost_report: dict[str, Any],
    found_report: dict[str, Any],
) -> dict[str, Any]:
    """Score two reports and explain which fields contributed."""

    similarities = _field_similarities(lost_report, found_report)

    fields: dict[str, float] = {}
    weighted_total = 0.0
    weight_used = 0.0

    for field, weight in FIELD_WEIGHTS.items():
        similarity = similarities.get(field)

        if similarity is None:
            continue

        fields[field] = round(similarity * 100, 1)
        weighted_total += similarity * weight
        weight_used += weight

    raw_score = weighted_total / weight_used * 100 if weight_used else 0.0
    score = min(raw_score + _evidence_bonus(similarities), 100.0)

    core = similarities.get("item_name") or 0.0
    category = similarities.get("category") or 0.0
    color = similarities.get("color") or 0.0
    location = similarities.get("location_text") or 0.0
    brand = similarities.get("brand") or 0.0
    event_date = similarities.get("date") or 0.0

    color_mismatch = (
        color <= 0.1
        and bool(str(lost_report.get("color") or "").strip())
        and bool(str(found_report.get("color") or "").strip())
    )

    # When the same kind of item is confirmed by category/brand and at least
    # one more detail, a plain weighted average can still look lukewarm. Lift
    # clear pairs into high-confidence territory. Conflicting colours block
    # the lift because they are strong evidence of two different items.
    if not color_mismatch:
        if core >= 0.86 and (category >= 0.8 or brand >= 0.85) and (
            color >= 0.6
            or location >= 0.6
            or event_date >= 0.7
            or brand >= 0.85
        ):
            score = max(score, 85.0)

        if core >= 0.92 and (category >= 0.8 or brand >= 0.85) and (
            (color >= 0.75 and location >= 0.6)
            or (brand >= 0.85 and (color >= 0.6 or location >= 0.6))
        ):
            score = max(score, 92.0)

    item_concepts_lost = _concepts(_prepare(lost_report.get("item_name"))[0])
    item_concepts_found = _concepts(_prepare(found_report.get("item_name"))[0])

    if (
        item_concepts_lost
        and item_concepts_found
        and not (item_concepts_lost & item_concepts_found)
    ):
        # A bottle is not a phone, no matter how close the dates or campuses are.
        score = min(score, 18.0)
    else:
        brands_lost = _report_brand_tokens(lost_report)
        brands_found = _report_brand_tokens(found_report)

        if brands_lost and brands_found and not (brands_lost & brands_found):
            # Different makes of the same product family are still different
            # items; keep them below the contact unlock threshold.
            score = min(score, 65.0)
        else:
            tokens_lost = _prepare(lost_report.get("item_name"))[0]
            tokens_found = _prepare(found_report.get("item_name"))[0]
            numbers_lost = {token for token in tokens_lost if token.isdigit()}
            numbers_found = {token for token in tokens_found if token.isdigit()}

            if (
                brands_lost
                and brands_found
                and numbers_lost
                and numbers_found
                and not (numbers_lost & numbers_found)
            ):
                # Same brand but explicitly different model numbers (iPhone 13
                # vs iPhone 17) should stay just below the contact unlock.
                score = min(score, 69.0)
            elif color_mismatch:
                # Two clearly different colours are strong evidence of two
                # different items; keep the pair visible but below unlock.
                score = min(score, 64.0)

    reasons = [
        FIELD_LABELS[field]
        for field, _ in sorted(
            FIELD_WEIGHTS.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        if fields.get(field, 0) >= 60
    ]

    return {
        "score": round(score, 1),
        "fields": fields,
        "reasons": reasons,
    }


def calculate_similarity(
    lost_report: dict[str, Any],
    found_report: dict[str, Any],
) -> float:
    """Backwards-compatible helper that returns only the score."""

    return score_reports(lost_report, found_report)["score"]
