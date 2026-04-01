from __future__ import annotations

import json
from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


Disposition = Literal["dismissed", "granted", "allowed_in_part", "other"]
RelevanceLevel = Literal["high", "medium", "low"]
MatchType = Literal["direct_interpretation", "application_only", "mentioned_only"]
EvidenceField = Literal["full_text", "interpretation_summary", "principles_established"]


class Source(BaseModel):
    dataset: str
    notes: str


class Case(BaseModel):
    case_id: str
    case_title: str
    court_name: Optional[str] = None
    decision_date: Optional[str] = None  # keep as string; PDFs are messy
    source_citation: Optional[str] = None


class Clause(BaseModel):
    article: Optional[str] = None
    text: Optional[str] = None


class CaseContext(BaseModel):
    legal_issue: Optional[str] = None
    petitioner_claim: Optional[str] = None
    respondent_argument: Optional[str] = None
    key_facts: list[str] = Field(default_factory=list)


class Reasoning(BaseModel):
    interpretation_summary: Optional[str] = None
    application_to_facts: Optional[str] = None
    principles_established: list[str] = Field(default_factory=list)
    precedents_cited: list[str] = Field(default_factory=list)


class Outcome(BaseModel):
    holding: Optional[str] = None
    disposition: Optional[Disposition] = None
    remedy_or_orders: Optional[str] = None

    @field_validator("holding", "remedy_or_orders", mode="before")
    @classmethod
    def _coerce_str_or_list(cls, v: object) -> object:
        """LLMs sometimes emit a list or dict instead of a string."""
        if v is None:
            return v
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            parts = [str(x).strip() for x in v if x is not None and str(x).strip()]
            return "\n".join(parts) if parts else None
        if isinstance(v, dict):
            if not v:
                return None
            lines: list[str] = []
            for k, val in v.items():
                if isinstance(val, (dict, list)):
                    lines.append(f"{k}: {json.dumps(val, ensure_ascii=False)}")
                else:
                    lines.append(f"{k}: {val}")
            return "\n".join(lines)
        return v


class LinkExplanation(BaseModel):
    why_this_clause_matters: Optional[str] = None
    relevance_level: Optional[RelevanceLevel] = None
    match_type: Optional[MatchType] = None


class EvidenceLocation(BaseModel):
    field: EvidenceField = "full_text"
    start_char: Optional[int] = None
    end_char: Optional[int] = None

    @field_validator("field", mode="before")
    @classmethod
    def _default_or_coerce_field(cls, v: object) -> object:
        allowed = ("full_text", "interpretation_summary", "principles_established")
        if v is None or (isinstance(v, str) and not str(v).strip()):
            return "full_text"
        if isinstance(v, str) and v.strip() in allowed:
            return v.strip()
        return "full_text"


class Evidence(BaseModel):
    evidence_excerpt: Optional[str] = None
    evidence_location: EvidenceLocation

    @model_validator(mode="before")
    @classmethod
    def _ensure_evidence_location(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        loc = data.get("evidence_location")
        if loc is None:
            data["evidence_location"] = {"field": "full_text", "start_char": None, "end_char": None}
        elif isinstance(loc, dict) and loc.get("field") is None:
            loc["field"] = "full_text"
        return data


class Frame(BaseModel):
    frame_id: str
    created_at: str = Field(default_factory=lambda: date.today().isoformat())
    annotator_id: str
    source: Source
    case: Case
    clause: Clause
    case_context: CaseContext
    reasoning: Reasoning
    outcome: Outcome
    link_explanation: LinkExplanation
    evidence: Evidence

