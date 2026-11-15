"""Similarity scoring for lost and found item reports.

The score is a weighted average of per-field text similarity. Each field is
compared with both word-level TF-IDF (captures shared words) and character
n-gram TF-IDF (tolerates typos and small spelling differences).
"""

from __future__ import annotations

import re
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Relative importance of each field when comparing two reports.
FIELD_WEIGHTS = {
    "item_name": 0.30,
    "description": 0.20,
    "category": 0.15,
    "color": 0.15,
    "brand": 0.10,
    "location_text": 0.10,
}

FIELD_LABELS = {
    "item_name": "item name",
    "description": "description",
    "category": "category",
    "color": "color",
    "brand": "brand",
    "location_text": "location",
}

# Common alternative spellings mapped to one canonical word.
SYNONYMS = {
    "mobile": "phone",
    "mobiles": "phone",
    "cellphone": "phone",
    "cellphones": "phone",
    "smartphone": "phone",
    "smartphones": "phone",
    "notebook": "laptop",
    "notebooks": "laptop",
    "purse": "wallet",
    "billfold": "wallet",
    "backpack": "bag",
    "rucksack": "bag",
    "handbag": "bag",
    "earbud": "earphones",
    "earbuds": "earphones",
    "earphone": "earphones",
    "headphone": "headphones",
    "airpods": "earphones",
    "spectacles": "glasses",
    "eyeglasses": "glasses",
    "flask": "bottle",
    "waterbottle": "bottle",
    "cycle": "bicycle",
    "bike": "bicycle",
    "idcard": "id",
    "identitycard": "id",
}

_WORD_RE = re.compile(r"[^a-z0-9\s]+")


def _normalize(value: Any) -> str:
    """Lowercase, strip punctuation and apply the synonym map."""

    text = _WORD_RE.sub(" ", str(value or "").lower())
    return " ".join(SYNONYMS.get(word, word) for word in text.split())


def _cosine(text_a: str, text_b: str, analyzer: str, ngram_range: tuple) -> float:
    fill = None if analyzer == "char_wb" else "english"

    try:
        matrix = TfidfVectorizer(
            analyzer=analyzer,
            ngram_range=ngram_range,
            stop_words=fill,
            sublinear_tf=True,
        ).fit_transform([text_a, text_b])
    except ValueError:
        # Raised when every token is a stop word or the vocabulary is empty.
        return 0.0

    return float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])


def _field_similarity(value_a: Any, value_b: Any) -> float | None:
    """Return a 0-1 similarity, or None when both fields are empty."""

    text_a = _normalize(value_a)
    text_b = _normalize(value_b)

    if not text_a and not text_b:
        return None

    if not text_a or not text_b:
        return 0.0

    if text_a == text_b:
        return 1.0

    word_score = _cosine(text_a, text_b, analyzer="word", ngram_range=(1, 2))
    char_score = _cosine(text_a, text_b, analyzer="char_wb", ngram_range=(2, 4))
    score = (word_score + char_score) / 2

    # "bottle" vs "blue bottle" is a strong signal even when TF-IDF is harsh.
    tokens_a = set(text_a.split())
    tokens_b = set(text_b.split())

    if tokens_a and tokens_b:
        if tokens_a <= tokens_b or tokens_b <= tokens_a:
            score = max(score, 0.9)
        else:
            # Dice coefficient rewards shared words regardless of word order.
            shared = len(tokens_a & tokens_b)
            score = max(score, 2 * shared / (len(tokens_a) + len(tokens_b)))

    return min(score, 1.0)


def score_reports(
    lost_report: dict[str, Any],
    found_report: dict[str, Any],
) -> dict[str, Any]:
    """Score two reports and explain which fields contributed."""

    fields: dict[str, float] = {}
    weighted_total = 0.0
    weight_used = 0.0

    for field, weight in FIELD_WEIGHTS.items():
        similarity = _field_similarity(
            lost_report.get(field),
            found_report.get(field),
        )

        if similarity is None:
            continue

        fields[field] = round(similarity * 100, 1)
        weighted_total += similarity * weight
        weight_used += weight

    score = round(weighted_total / weight_used * 100, 1) if weight_used else 0.0

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
        "score": score,
        "fields": fields,
        "reasons": reasons,
    }


def calculate_similarity(
    lost_report: dict[str, Any],
    found_report: dict[str, Any],
) -> float:
    """Backwards-compatible helper that returns only the score."""

    return score_reports(lost_report, found_report)["score"]
