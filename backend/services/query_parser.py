"""
Query parsing: extract constitutional article references from user queries.

Uses a fast regex path first. Falls back to OPENAI_TOOL_MODEL for ambiguous phrasings.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Optional

from config.settings import OPENAI_TOOL_MODEL


@dataclass
class ParsedQuery:
    article: Optional[str] # "12(2)" or None
    article_base: Optional[str] # "12" or None
    query_type: str # "clause_first" or "fact_pattern"


_FAST_REGEX = re.compile(
    r"\b(?:article|art\.?)\s*(\d+[A-Z]?)" # article number
    r"(?:\s*[\(\[]\s*(\d+)\s*[\)\]]" # optional outer clause e.g. (1)
    r"(?:\s*[\(\[]\s*([a-z])\s*[\)\]])?)?", # optional inner clause e.g. (a)
    re.IGNORECASE,
)


def _build_article_list() -> str:
    """Load articles.json and return a formatted identifier → description list for the LLM prompt."""
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "articles.json",
    )
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        lines = []
        for art in data.get("articles", []):
            art_num = art["article"]
            for cl in art.get("clauses", []):
                clause = cl.get("clause") or ""
                # Take only the first sentence/line and cap at 90 chars
                summary = cl.get("text", "").split("\n")[0].rstrip()
                if len(summary) > 90:
                    summary = summary[:87] + "..."
                identifier = f"{art_num}{clause}" if clause else art_num
                lines.append(f"  {identifier} — {summary}")
        return "\n".join(lines)
    except Exception:
        return "  10, 11, 12(1), 12(2), 13(1), 13(2), 14(1)(a), 17 (and others)"


# Built once at import time — referenced in the LLM fallback prompt
_ARTICLE_LIST = _build_article_list()


def _regex_parse(query: str) -> ParsedQuery | None:
    """Fast path: extract article ref with regex. Returns None if no confident match."""
    m = _FAST_REGEX.search(query)
    if not m:
        return None
    art_num = m.group(1).upper()
    clause1 = m.group(2)
    clause2 = m.group(3)

    if clause1 and clause2:
        article = f"{art_num}({clause1})({clause2})"
    elif clause1:
        article = f"{art_num}({clause1})"
    else:
        article = art_num

    return ParsedQuery(
        article=article,
        article_base=art_num,
        query_type="clause_first",
    )


def parse_query(query: str, client) -> ParsedQuery:
    """
    Parse a user query to extract constitutional article references.

    Fast regex path first. Falls back to LLM for ambiguous phrasings.
    If client is None, returns a safe fact_pattern fallback (never raises).

    Args:
        query: Raw user input string.
        client: LLM instance, or None.

    Returns:
        ParsedQuery dataclass.
    """
    result = _regex_parse(query)
    if result is not None:
        return result

    if client is None:
        return ParsedQuery(article=None, article_base=None, query_type="fact_pattern")

    prompt = (
        "You are a query classifier for a Sri Lankan constitutional law database.\n\n"
        "The following article/clause identifiers exist in the database (identifier — clause text):\n"
        f"{_ARTICLE_LIST}\n\n"
        "Given the user query below, identify:\n"
        "1. The single most relevant identifier from the list above that the query refers to. "
        "Use the exact identifier string as shown (e.g. \"12(2)\", \"14(1)(a)\", \"17\"). "
        "Return null if the query does not reference any specific article.\n"
        "2. The base article number only (e.g. \"12\" from \"12(2)\"). Return null if no article.\n"
        "3. query_type: \"clause_first\" if a specific article is identified, "
        "\"fact_pattern\" if the query is about a general legal situation with no specific article.\n\n"
        "Return ONLY a valid JSON object:\n"
        '{"article": "<identifier>" | null, "article_base": "<number>" | null, '
        '"query_type": "clause_first" | "fact_pattern"}\n\n'
        f"User query: {query}"
    )

    try:
        response = client.chat.completions.create(
            model=OPENAI_TOOL_MODEL,
            max_tokens=80,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        data = json.loads(response.choices[0].message.content or "{}")
        return ParsedQuery(
            article=data.get("article"),
            article_base=data.get("article_base"),
            query_type=data.get("query_type", "fact_pattern"),
        )
    except Exception:
        # Never break the main chat flow due to a parse failure
        return ParsedQuery(article=None, article_base=None, query_type="fact_pattern")
