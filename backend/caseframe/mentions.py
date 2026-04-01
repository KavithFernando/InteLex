"""
Heuristic detection of whether a constitution clause key is plausibly cited in judgment text.
Used to skip impossible extractions and as a post-check on model output.
"""

from __future__ import annotations

import re
from typing import Pattern


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower())


def _article_num_from_key(key: str) -> str | None:
    """Leading article number / label, e.g. '12(1)' -> '12', '14A(2)' -> '14A'."""
    m = re.match(r"^(\d+A?)", key.strip())
    return m.group(1) if m else None


def _patterns_for_key(key: str) -> list[Pattern[str]]:
    """
    Build regex patterns that match typical Sri Lankan citation forms.
    Order: more specific first.
    """
    k = key.strip()
    pats: list[str] = []

    # Full key e.g. 12(1), 14(1)(a), 14A(1) — escape for regex safety
    esc = re.escape(k)
    pats.append(rf"(?<![0-9A-Za-z]){esc}(?![0-9A-Za-z])")
    pats.append(rf"article\s+{esc}")
    pats.append(rf"articles\s+{esc}")
    pats.append(rf"art\.\s*{esc}")

    # Article number only: Article 12, Art. 12 — risk of false positive for "12" in other contexts
    base = _article_num_from_key(k)
    if base:
        b = re.escape(base)
        pats.append(rf"\barticle\s+{b}\b")
        pats.append(rf"\barticles\s+{b}\b")
        pats.append(rf"\bart\.\s*{b}\b")

    return [re.compile(p, re.IGNORECASE) for p in pats]


def plausibly_mentioned_in_text(key: str, text: str) -> bool:
    """True if any pattern matches (cheap pre-filter)."""
    if not text or not key:
        return False
    n = _norm(text)
    for rx in _patterns_for_key(key):
        if rx.search(n):
            return True
    return False


def excerpt_anchored_in_text(excerpt: str | None, text: str, min_len: int = 12) -> bool:
    """Require a non-trivial substring of excerpt to appear in source (anti-hallucination)."""
    if not excerpt or len(excerpt.strip()) < min_len:
        return False
    ex = excerpt.strip()
    # Try normalized containment
    if ex.lower() in _norm(text):
        return True
    # First 40 chars sliding
    chunk = ex[:80].strip()
    if len(chunk) >= min_len and chunk.lower() in _norm(text):
        return True
    return False
