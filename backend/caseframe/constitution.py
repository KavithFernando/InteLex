"""
Load constitution/articles.json and map whitelist keys (e.g. "12(1)", "14A(1)(a)")
to official clause text for prompts and validation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# User-facing aliases -> canonical key in KEY_TO_TEXT (same official text repeated is OK).
ALIASES: dict[str, str] = {
    "15(5)(a)": "15(5)",
    "15(5)(b)": "15(5)",
    "14A(1)(a)": "14A(1)",
    "14A(1)(b)": "14A(1)",
    "14A(1)(c)": "14A(1)",
    "14A(1)(d)": "14A(1)",
}


def _canonical_key(article: str, clause: str | None) -> str:
    """Build display key from JSON article + clause fields."""
    if clause is None:
        return article
    clause = str(clause).strip()
    # e.g. 1_a -> (1)(a) for Art. 14
    m = re.fullmatch(r"(\d+)_([a-z])", clause)
    if m:
        return f"{article}({m.group(1)})({m.group(2)})"
    m = re.fullmatch(r"(\d+)", clause)
    if m:
        return f"{article}({clause})"
    # e.g. 2_proviso_1 — keep machine-readable but stable
    return f"{article}({clause})"


def load_articles_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if "articles" not in data:
        raise ValueError(f"Invalid constitution file {path}: missing 'articles'")
    return data


def build_clause_text_map(data: dict[str, Any]) -> dict[str, str]:
    """article+clause entries -> canonical_key -> text (last wins if duplicate)."""
    out: dict[str, str] = {}
    for block in data.get("articles", []):
        article = str(block.get("article", "")).strip()
        if not article:
            continue
        for row in block.get("clauses", []):
            if not isinstance(row, dict):
                continue
            ck = row.get("canonical_key")
            if ck:
                key = str(ck).strip()
            else:
                key = _canonical_key(article, row.get("clause"))
            text = (row.get("text") or "").strip()
            if key and text:
                out[key] = text
    # Apply aliases pointing to same text as target key
    for alias, target in ALIASES.items():
        if target in out:
            out[alias] = out[target]
    return out


def normalize_model_article(raw: str | None, key_to_text: dict[str, str]) -> str | None:
    """Map model output (may include extra words) to a canonical key."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if s in key_to_text:
        return s
    r = resolve_whitelist_key(s, key_to_text)
    if r:
        return r
    # Strip common prefixes e.g. "Article 12(1)"
    s2 = re.sub(r"^(article|articles|art\.?)\s+", "", s, flags=re.IGNORECASE).strip()
    if s2 != s:
        return resolve_whitelist_key(s2, key_to_text) or (
            s2 if s2 in key_to_text else None
        )
    return None


def resolve_whitelist_key(raw: str, key_to_text: dict[str, str]) -> str | None:
    """Normalize user/CLI key to a key present in key_to_text."""
    s = raw.strip()
    if not s:
        return None
    if s in key_to_text:
        return s
    if s in ALIASES and ALIASES[s] in key_to_text:
        return ALIASES[s]
    # Try alias lookup with same text
    if s in ALIASES:
        t = ALIASES[s]
        if t in key_to_text:
            return t
    return None


def resolve_whitelist(
    whitelist: list[str],
    key_to_text: dict[str, str],
) -> tuple[list[str], list[str]]:
    """
    Returns (resolved_canonical_keys, unknown_strings).
    Dedupes while preserving order.
    """
    seen: set[str] = set()
    resolved: list[str] = []
    unknown: list[str] = []
    for w in whitelist:
        r = resolve_whitelist_key(w, key_to_text)
        if r is None:
            unknown.append(w.strip())
            continue
        if r not in seen:
            seen.add(r)
            resolved.append(r)
    return resolved, unknown


def format_constitution_block(keys: list[str], key_to_text: dict[str, str]) -> str:
    """Prompt block: official text for listed keys only."""
    lines: list[str] = []
    for k in keys:
        t = key_to_text.get(k, "")
        lines.append(f"- **{k}**: {t}")
    return "OFFICIAL CONSTITUTION CLAUSE TEXT (use for `clause.text` verbatim; do not paraphrase):\n" + "\n".join(lines)
