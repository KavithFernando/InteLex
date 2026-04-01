from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional

from openai import OpenAI


SYSTEM_PROMPT = """You extract information from court case documents into STRICT JSON.

Output shape:
- Return a single JSON object with exactly one top-level key: "frames".
- "frames" MUST be an array. Each element is one full "frame" object (see FRAME_SCHEMA below).
- **One frame per (case, clause) pair**: the same underlying case/document may appear in multiple frames; the "case" object MUST be identical across every frame for that document. Only vary per frame: "clause", and the clause-specific parts: "case_context", "reasoning", "outcome" (if the clause affects only part of the decision), "link_explanation", and "evidence".
- frame_id must be unique per frame (suffix with clause/article if needed).

Anti-hallucination:
- Use ONLY information supported by the provided case document text (or images). If something is not in the document, use null or [].
- Do NOT invent case names, dates, citations, precedents, or constitutional text.
- For `clause.text`, copy verbatim from OFFICIAL CONSTITUTION CLAUSE TEXT when provided; otherwise null.
- For `precedents_cited`, include only authorities explicitly named in the document.
- `link_explanation.relevance_level` must reflect how central the clause is to the court's reasoning: high (dispositive/central), medium (substantive but not sole basis), low (brief mention or peripheral).
- `link_explanation.match_type`: direct_interpretation vs application_only vs mentioned_only — be honest; do not default to direct_interpretation.

Rules:
- Output MUST be valid JSON (not markdown).
- Do not add top-level keys other than "frames". Each frame uses EXACTLY the FRAME_SCHEMA keys; do not add extra keys inside frames.
- If a field cannot be found, use null (or [] for list fields).
- evidence_excerpt may be a short paraphrase (1-3 sentences) but must be faithful to the document.
- Keep key_facts to 1-5 bullets.
- Enums (inside each frame):
  - outcome.disposition: dismissed | granted | allowed_in_part | other
  - link_explanation.relevance_level: high | medium | low
  - link_explanation.match_type: direct_interpretation | application_only | mentioned_only
  - evidence.evidence_location.field: full_text | interpretation_summary | principles_established (required; never null)
"""


DETECT_SYSTEM_PROMPT = """You identify which constitution clauses from a fixed whitelist appear in the case materials in a substantive way.

Return ONLY valid JSON: {"discussed": ["...", ...]}

Rules:
- "discussed" MUST be a strict subset of the ALLOWED list provided in the user message (exact string match).
- Include a clause ONLY IF the court meaningfully engages with it: the clause is raised as a specific right, argued by a party, interpreted by the court, applied to the facts, or forms part of the holding/reasoning.
- DO NOT include a clause merely because a party mentions it in passing, it appears in a list of rights without analysis, or the judgment says it is irrelevant/inapplicable — those do NOT count as discussed.
- DO NOT include a clause that is explicitly dismissed as "not applicable" or "not raised" without substantive treatment.
- If a clause is only cited to say "this case is NOT about X", it does NOT count.
- When uncertain, OMIT the clause (err on the side of exclusion).
- If NONE of the allowed clauses are meaningfully engaged with, return {"discussed": []}.
- Do NOT output clauses not in the allowed list.
"""


def _frame_schema_json() -> dict[str, Any]:
    return {
        "frame_id": "RQ1_EXAMPLE_001",
        "created_at": "YYYY-MM-DD",
        "annotator_id": "your_name_or_initials",
        "source": {"dataset": "casedata.json", "notes": "Manual RQ1 clause interpretation frame"},
        "case": {
            "case_id": "SC_FR_310_1997",
            "case_title": "Almeida v. Ceylon Fisheries Corporation and Others (1998)",
            "court_name": "Supreme Court of Sri Lanka",
            "decision_date": "1998-06-08",
            "source_citation": "Supreme Court of Sri Lanka, S.C. Application No. 310/97 (FR), decided on 8 June 1998",
        },
        "clause": {
            "article": "12(1)",
            "text": "All persons are equal before the law and are entitled to the equal protection of the law.",
        },
        "case_context": {
            "legal_issue": "What question was the court deciding in relation to this clause?",
            "petitioner_claim": "What did the petitioner/applicant argue (relevant to the clause)?",
            "respondent_argument": "What did the respondent/state argue (relevant to the clause)?",
            "key_facts": ["1-5 bullet facts that matter for applying/interpreting the clause"],
        },
        "reasoning": {
            "interpretation_summary": "In your own words, what did the court say the clause means / how it should be applied?",
            "application_to_facts": "How did the court connect the facts to the clause interpretation?",
            "principles_established": ["Optional: 1-5 bullets"],
            "precedents_cited": ["Optional: citations"],
        },
        "outcome": {
            "holding": "What did the court decide (in terms of the clause claim)?",
            "disposition": "dismissed",
            "remedy_or_orders": None,
        },
        "link_explanation": {
            "why_this_clause_matters": "1-3 sentences linking the clause to reasoning and outcome.",
            "relevance_level": "high",
            "match_type": "direct_interpretation",
        },
        "evidence": {
            "evidence_excerpt": "Short supporting paraphrase from the document.",
            "evidence_location": {"field": "full_text", "start_char": None, "end_char": None},
        },
    }


@dataclass
class OpenAIConfig:
    api_key: str
    model: str
    vision_model: str


def load_openai_config() -> OpenAIConfig:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Put it in .env or your environment.")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
    vision_model = os.getenv("OPENAI_VISION_MODEL", model).strip()
    return OpenAIConfig(api_key=api_key, model=model, vision_model=vision_model)


def _call_json_only(
    client: OpenAI,
    *,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.0,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model,
        "input": messages,
        "text": {"format": {"type": "json_object"}},
        "temperature": temperature,
    }
    try:
        resp = client.responses.create(**kwargs)
    except TypeError:
        kwargs.pop("temperature", None)
        resp = client.responses.create(**kwargs)
    raw = resp.output_text
    return json.loads(raw)


def _clause_instruction(clauses: Optional[list[str]]) -> str:
    if clauses:
        return (
            "CLAUSE_SELECTION (priority whitelist): Use ONLY clause/article references from the listed set below. "
            "Discard all non-listed references even if discussed (e.g., Article 126, 121). "
            "Create a frame ONLY for listed clauses that the court MATERIALLY engages with: argued by a party, "
            "interpreted, applied to facts, or relied on in the holding/reasoning. "
            "Do NOT create a frame for a clause that is mentioned only in passing, cited to say it does not apply, "
            "dismissed as irrelevant, or raised without substantive treatment. "
            "If none of the listed clauses are materially engaged with, return {\"frames\": []}.\n"
            "Allowed clauses:\n"
            + "\n".join(f"- {c}" for c in clauses)
        )
    return (
        "CLAUSE_SELECTION (no fixed list): Produce one frame per distinct constitutional/legal clause "
        "that the court materially interprets, applies, or relies on for the decision (not mere passing mention). "
        "If none qualify, return {\"frames\": []}."
    )


def _parse_frames_response(obj: dict[str, Any]) -> list[dict[str, Any]]:
    if "frames" in obj:
        frames = obj["frames"]
        if not isinstance(frames, list):
            raise ValueError('"frames" must be an array')
        return [f for f in frames if isinstance(f, dict)]
    if "case" in obj and "clause" in obj:
        return [obj]
    raise ValueError('Expected top-level "frames" array or a single frame object')


def detect_discussed_clauses(
    *,
    cfg: OpenAIConfig,
    pdf_filename: str,
    full_text: str,
    allowed_keys: list[str],
    constitution_block: str,
) -> list[str]:
    """Returns a subset of allowed_keys that the model believes are genuinely discussed."""
    if not allowed_keys:
        return []
    client = OpenAI(api_key=cfg.api_key)
    user_text = (
        f"pdf_filename: {pdf_filename}\n\n"
        f"ALLOWED (you may output only these exact strings):\n{json.dumps(allowed_keys, ensure_ascii=False)}\n\n"
        f"{constitution_block}\n\n"
        "CASE_DOCUMENT_TEXT:\n"
        + full_text[:120_000]
    )
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": DETECT_SYSTEM_PROMPT},
        {"role": "user", "content": [{"type": "input_text", "text": user_text}]},
    ]
    try:
        raw = _call_json_only(client, model=cfg.model, messages=messages, temperature=0.0)
    except Exception:
        raw = _call_json_only(client, model=cfg.model, messages=messages, temperature=0.0)
    discussed = raw.get("discussed")
    if not isinstance(discussed, list):
        return []
    allow = set(allowed_keys)
    out: list[str] = []
    seen: set[str] = set()
    for x in discussed:
        if not isinstance(x, str):
            continue
        s = x.strip()
        if s in allow and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def detect_discussed_clauses_from_images(
    *,
    cfg: OpenAIConfig,
    pdf_filename: str,
    page_png_b64: list[str],
    allowed_keys: list[str],
    constitution_block: str,
) -> list[str]:
    """Same as detect_discussed_clauses but uses page images (scanned PDFs)."""
    if not allowed_keys:
        return []
    client = OpenAI(api_key=cfg.api_key)
    header = (
        f"pdf_filename: {pdf_filename}\n\n"
        f"ALLOWED (you may output only these exact strings):\n{json.dumps(allowed_keys, ensure_ascii=False)}\n\n"
        f"{constitution_block}\n\n"
        "The case document follows as page images."
    )
    content: list[dict[str, Any]] = [{"type": "input_text", "text": header}]
    for b64 in page_png_b64:
        content.append({"type": "input_image", "image_url": f"data:image/png;base64,{b64}"})
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": DETECT_SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]
    raw = _call_json_only(client, model=cfg.vision_model, messages=messages, temperature=0.0)
    discussed = raw.get("discussed")
    if not isinstance(discussed, list):
        return []
    allow = set(allowed_keys)
    out: list[str] = []
    seen: set[str] = set()
    for x in discussed:
        if not isinstance(x, str):
            continue
        s = x.strip()
        if s in allow and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def extract_frames_from_text(
    *,
    cfg: OpenAIConfig,
    frame_id_prefix: str,
    annotator_id: str,
    dataset_name: str,
    notes: str,
    pdf_filename: str,
    full_text: str,
    clauses: Optional[list[str]] = None,
    constitution_block: str = "",
) -> list[dict[str, Any]]:
    client = OpenAI(api_key=cfg.api_key)
    schema = _frame_schema_json()
    wrapper = {"frames": [schema]}

    extra = ""
    if constitution_block:
        extra = constitution_block + "\n\n"

    user_prompt = {
        "type": "input_text",
        "text": (
            "Fill frames using the provided case document text.\n\n"
            f"frame_id prefix (make each frame_id unique, e.g. {frame_id_prefix}_C01): {frame_id_prefix}\n"
            f"annotator_id: {annotator_id}\n"
            f"source.dataset: {dataset_name}\n"
            f"source.notes: {notes}\n"
            f"pdf_filename: {pdf_filename}\n\n"
            + extra
            + _clause_instruction(clauses)
            + "\n\n"
            "OUTPUT: {\"frames\": [ FRAME_SCHEMA, ... ]} where each array element matches FRAME_SCHEMA "
            "(same keys/nesting as this example object):\n"
            + json.dumps(schema, ensure_ascii=False, indent=2)
            + "\n\n"
            "CASE_DOCUMENT_TEXT:\n"
            + full_text[:180_000]
        ),
    }

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [user_prompt]},
    ]

    try:
        raw = _call_json_only(client, model=cfg.model, messages=messages, temperature=0.0)
        return _parse_frames_response(raw)
    except Exception as e:
        repair = {
            "type": "input_text",
            "text": (
                "Your previous output was invalid or failed to parse. "
                'Return ONLY valid JSON: {"frames": [ ... ]} with each element matching FRAME_SCHEMA. '
                "No other top-level keys.\n"
                f"Error: {type(e).__name__}: {e}\n\n"
                f"Example wrapper (structure only): {json.dumps(wrapper, ensure_ascii=False)}"
            ),
        }
        messages.append({"role": "user", "content": [repair]})
        raw = _call_json_only(client, model=cfg.model, messages=messages, temperature=0.0)
        return _parse_frames_response(raw)


def extract_frames_from_images(
    *,
    cfg: OpenAIConfig,
    frame_id_prefix: str,
    annotator_id: str,
    dataset_name: str,
    notes: str,
    pdf_filename: str,
    page_png_b64: list[str],
    clauses: Optional[list[str]] = None,
    constitution_block: str = "",
) -> list[dict[str, Any]]:
    client = OpenAI(api_key=cfg.api_key)
    schema = _frame_schema_json()
    wrapper = {"frames": [schema]}

    extra = ""
    if constitution_block:
        extra = constitution_block + "\n\n"

    content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": (
                "Fill frames using the provided case document pages (images).\n\n"
                f"frame_id prefix (make each frame_id unique): {frame_id_prefix}\n"
                f"annotator_id: {annotator_id}\n"
                f"source.dataset: {dataset_name}\n"
                f"source.notes: {notes}\n"
                f"pdf_filename: {pdf_filename}\n\n"
                + extra
                + _clause_instruction(clauses)
                + "\n\n"
                "OUTPUT: {\"frames\": [ FRAME_SCHEMA, ... ]} where each array element matches:\n"
                + json.dumps(schema, ensure_ascii=False, indent=2)
            ),
        }
    ]

    for b64 in page_png_b64:
        content.append({"type": "input_image", "image_url": f"data:image/png;base64,{b64}"})

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]

    try:
        raw = _call_json_only(client, model=cfg.vision_model, messages=messages, temperature=0.0)
        return _parse_frames_response(raw)
    except Exception as e:
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            'Return ONLY valid JSON: {"frames": [ ... ]} with each element matching FRAME_SCHEMA. '
                            f"Error: {type(e).__name__}: {e}\n"
                            f"Example wrapper: {json.dumps(wrapper, ensure_ascii=False)}"
                        ),
                    }
                ],
            }
        )
        raw = _call_json_only(client, model=cfg.vision_model, messages=messages, temperature=0.0)
        return _parse_frames_response(raw)
