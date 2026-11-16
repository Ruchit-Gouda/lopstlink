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
    "item_name": 0.30,
    "description": 0.16,
    "category": 0.14,
    "color": 0.14,
    "location_text": 0.13,
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
    "tiffin box": "lunchbox",
    "lunch box": "lunchbox",
    "note book": "notebook",
    "lap top": "laptop",
    "bus stop": "bus stand",
    "busstop": "bus stand",
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
    "laptops": "laptop",
    "tiffin": "lunchbox",
    "smartwatch": "watch",
    "watches": "watch",
    "shoes": "shoe",
    "slippers": "slipper",
    "sandals": "sandal",
    "trousers": "trouser",
    "glasses": "glasses",
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
_NO_STEM = {"glasses", "canvas", "campus", "status", "series", "species", "news"}

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
    "earphones": {"earphones", "headphones", "airpods", "buds", "headset"},
    "watch": {"watch", "fitbit", "fireboltt", "boat", "noise"},
    "wallet": {"wallet", "purse", "billfold"},
    "bag": {"bag", "backpack", "rucksack", "handbag", "sling", "trolley"},
    "bottle": {"bottle", "flask", "sipper", "tumbler"},
    "key": {"key", "keychain"},
    "glasses": {"glasses", "spectacles", "sunglasses", "goggles"},
    "id": {"id", "aadhar", "pan", "license", "passport", "card", "identity"},
    "book": {"book", "notebook", "diary", "register", "novel", "textbook"},
    "charger": {"charger", "adapter", "cable", "powerbank"},
    "umbrella": {"umbrella"},
    "calculator": {"calculator"},
    "lunchbox": {"lunchbox", "tiffin"},
    "stationery": {"pen", "pencil", "eraser", "sharpener", "scale", "ruler"},
    "clothing": {
        "shirt",
        "tshirt",
        "jacket",
        "hoodie",
        "sweater",
        "jeans",
        "trouser",
        "pant",
        "cap",
        "hat",
        "shoe",
        "sandal",
        "slipper",
    },
    "jewellery": {"ring", "chain", "bracelet", "earring", "necklace"},
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
    """Jaccard similarity over bigrams and trigrams."""

    if not text_a or not text_b:
        return 0.0

    grams_a = _char_ngrams(text_a, 2) | _char_ngrams(text_a, 3)
    grams_b = _char_ngrams(text_b, 2) | _char_ngrams(text_b, 3)
    union = grams_a | grams_b

    return len(grams_a & grams_b) / len(union) if union else 0.0


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

            if ratio >= 0.82:
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

    # Character n-grams and whole-string edits are meant to absorb typos in
    # otherwise related text. Applying them to two unrelated sentences ("cut
    # my hairs" vs "moodbidri bus stand") invents similarity out of noise.
    if shared:
        char_score = _char_similarity(text_a, text_b)
        sequence_score = SequenceMatcher(None, text_a, text_b).ratio() * 0.95
    else:
        char_score = 0.0
        sequence_score = 0.0

    return min(
        max(dice, containment, jaccard, char_score, sequence_score, fuzzy_score),
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
        score = max(score, 0.58)

        if generic_a or generic_b:
            # One report only says "Phone"; the other has the model. Treat the
            # generic title as compatible with a specific item of that family.
            score = max(score, 0.86 if (brand_a or brand_b) else 0.78)
        else:
            score = max(score, 0.68)

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
        return 0.9
    if days <= 7:
        return 0.75
    if days <= 14:
        return 0.55
    if days <= 30:
        return 0.3
    return 0.1


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
        "location_text": _text_similarity(
            lost_report.get("location_text"),
            found_report.get("location_text"),
            containment_cap=0.95,
        ),
        "date": _date_similarity(lost_report, found_report),
    }


def _evidence_bonus(fields: dict[str, float]) -> float:
    """Reward several independent fields pointing at the same pair.

    A weighted average of six fields can look lukewarm even when most of them
    agree. The bonus is deliberately small and capped so a single loose field
    cannot lift an unrelated pair over the match threshold.
    """

    supporting = 0

    if (fields.get("item_name") or 0) >= 0.75:
        supporting += 1
    if (fields.get("category") or 0) >= 0.85:
        supporting += 1
    if (fields.get("color") or 0) >= 0.8:
        supporting += 1
    if (fields.get("location_text") or 0) >= 0.6:
        supporting += 1
    if (fields.get("brand") or 0) >= 0.85:
        supporting += 1
    if (fields.get("date") or 0) >= 0.75:
        supporting += 1

    if supporting < 2:
        return 0.0

    return min(supporting * 1.4, 6.0)


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
            elif (
                (similarities.get("color") or 0) <= 0.1
                and (similarities.get("location_text") or 0) < 0.4
                and str(lost_report.get("color") or "").strip()
                and str(found_report.get("color") or "").strip()
            ):
                # Two different colours at two different places are conflicting
                # evidence; keep the pair visible but well below contact unlock.
                score = min(score, 58.0)

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
