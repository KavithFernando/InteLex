import json
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI
from loguru import logger

# Number of top frames whose full details are fetched from DB and fed to the synthesis LLM.
SYNTHESIS_FRAME_COUNT = 3

SYSTEM_PROMPT = """You are a friendly legal research assistant for InteLex, a Sri Lankan constitutional law case database.

Your main purpose is to retrieve relevant legal case examples from the user's private case database.

Rules:
- If the user asks for precedents / similar cases / case examples OR pastes legal text, you MUST call the tool `search_cases`.
- If the user is doing small talk or general chat, do NOT call tools.
- Never invent case names, citations, or facts.
- If the tool returns zero results, say you couldn't find matches in the current database and ask the user to refine the query.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_cases",
            "description": "Search the case database and return the most relevant interpretation frames (constitution-clause scoped hits), ranked globally.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query_text": {
                        "type": "string",
                        "description": "Legal text or legal query from the user."
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return.",
                        "default": 10
                    }
                },
                "required": ["query_text"]
            }
        }
    }
]


def _build_frame_context(frame: Dict[str, Any], rank: int) -> str:
    """Format a single FrameDetail dict into a readable block for the synthesis prompt."""
    lines = [f"--- Case {rank}: {frame.get('case_title') or frame.get('case_id')} ---"]
    if frame.get("article"):
        sub = f" ({frame['subclause']})" if frame.get("subclause") else ""
        lines.append(f"Constitution Clause: Article {frame['article']}{sub}")
    if frame.get("clause_text"):
        lines.append(f"Clause Text: {frame['clause_text']}")
    if frame.get("legal_issue"):
        lines.append(f"Legal Issue: {frame['legal_issue']}")
    if frame.get("petitioner_claim"):
        lines.append(f"Petitioner's Claim: {frame['petitioner_claim']}")
    if frame.get("respondent_argument"):
        lines.append(f"Respondent's Argument: {frame['respondent_argument']}")
    if frame.get("key_facts"):
        lines.append("Key Facts:\n" + "\n".join(f"  - {f}" for f in frame["key_facts"]))
    if frame.get("interpretation_summary"):
        lines.append(f"Court's Reasoning: {frame['interpretation_summary']}")
    if frame.get("outcome"):
        lines.append(f"Outcome: {frame['outcome']}")
    if frame.get("principles_established"):
        lines.append("Principles Established:\n" + "\n".join(f"  - {p}" for p in frame["principles_established"]))
    if frame.get("precedents_cited"):
        lines.append("Precedents Cited: " + "; ".join(frame["precedents_cited"]))
    if frame.get("decision_date"):
        lines.append(f"Decision Date: {frame['decision_date']}")
    return "\n".join(lines)


def _build_synthesis_prompt(user_query: str, frame_blocks: List[str]) -> str:
    n = len(frame_blocks)
    cases_text = "\n\n".join(frame_blocks)
    return f"""You are a legal research assistant specialising in Sri Lankan constitutional law.

The user asked:
\"\"\"{user_query}\"\"\"

The database retrieved the {n} most relevant interpretation frame(s) from the case corpus. Each frame represents how a specific case applied a specific constitutional clause.

{cases_text}

---

IMPORTANT RULES:
- Base your analysis STRICTLY on the case information provided above.
- Do NOT cite, invent, or infer cases, principles, or legal rules not explicitly mentioned in the frames above.
- If the retrieved cases do not fully answer the question, say so clearly rather than filling gaps with general knowledge.
- Address the reader directly as "you" (e.g. "Your question concerns…"). Never refer to "the user".

HOW TO STRUCTURE YOUR RESPONSE — follow this pattern of thinking, not a rigid template:
- Open by identifying the constitutional clause or legal principle that is at the heart of the user's question.
- Explain how courts have generally understood and applied that principle, using the retrieved cases as illustrations — not as items to summarise one by one.
- Weave the cases in as examples that show different factual scenarios, different outcomes, or evolving interpretations of the same principle. A case should appear in your prose because it illuminates a point, not because it is next on a list.
- If two cases applied the same clause differently, explain the distinction through the principle ("the court drew the line differently when… as seen in X, compared to Y where…").
- Close by stating what this body of case law collectively tells the reader about their specific question, or honestly acknowledge what the retrieved cases leave unanswered.

Write in a clear, professional tone — flowing paragraphs, no bullet lists, no headings."""


class ChatService:

    def __init__(self, case_search_service, case_repo=None):
        self._case_search_service = case_search_service
        self._case_repo = case_repo

    def _get_client(self) -> OpenAI:
        from config import OPENAI_API_KEY, OPENAI_TOOL_MODEL, OPENAI_SYNTHESIS_MODEL
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing.")
        self._tool_model = OPENAI_TOOL_MODEL
        self._synthesis_model = OPENAI_SYNTHESIS_MODEL
        return OpenAI(api_key=OPENAI_API_KEY)

    def _fetch_frame_details(self, retrieval_result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fetch full FrameDetail for the top SYNTHESIS_FRAME_COUNT results that have a frame id."""
        if not self._case_repo:
            return []
        details = []
        for row in retrieval_result[:SYNTHESIS_FRAME_COUNT]:
            fid = row.get("interpretation_frame_id")
            if fid is None:
                continue
            try:
                detail = self._case_repo.fetch_frame_by_id(int(fid))
                if detail:
                    details.append(detail)
            except Exception as e:
                logger.warning("Failed to fetch frame %s for synthesis: %s", fid, e)
        return details

    def run_chat_turn(self, conversation_messages: List[Dict[str, Any]]) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
        client = self._get_client()
        retrieval_result: Optional[List[Dict[str, Any]]] = None

        # First call: let the model decide whether to call search_cases
        resp = client.chat.completions.create(
            model=self._tool_model,
            messages=conversation_messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.3,
            max_tokens=200,
        )

        msg = resp.choices[0].message
        logger.info("First call finish_reason: %s", resp.choices[0].finish_reason)

        tool_calls = getattr(msg, "tool_calls", None)
        if not tool_calls:
            logger.info("No tool call — returning direct reply")
            return (msg.content or ""), None

        logger.info("Tool call triggered")

        # Extract the user's query text from the tool call for synthesis
        user_query_for_synthesis = ""
        for tc in tool_calls:
            if tc.function.name == "search_cases":
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                user_query_for_synthesis = args.get("query_text", "")

                out = self._case_search_service.run_case_search(
                    query_text=user_query_for_synthesis,
                    top_k=int(args.get("top_k", 10)),
                )
                retrieval_result = out.get("retrieval_result", [])

        if not retrieval_result:
            return "I couldn't find any matching cases in the database for your query. Try rephrasing or narrowing the legal question.", []

        # Fetch full frame details for synthesis
        frame_details = self._fetch_frame_details(retrieval_result)

        if not frame_details:
            # Fallback: no DB details available, return a plain count message
            count = len(retrieval_result)
            return f"I found {count} relevant interpretation frame(s) in the database. Click any card below to explore the details.", retrieval_result

        # Build the synthesis
        frame_blocks = [_build_frame_context(fd, i + 1) for i, fd in enumerate(frame_details)]
        synthesis_prompt = _build_synthesis_prompt(user_query_for_synthesis, frame_blocks)

        synthesis_resp = client.chat.completions.create(
            model=self._synthesis_model,
            messages=[{"role": "user", "content": synthesis_prompt}],
            temperature=0.2,
            max_tokens=1200,
        )
        synthesis = (synthesis_resp.choices[0].message.content or "").strip()
        logger.info("Synthesis complete (%d chars)", len(synthesis))

        return synthesis, retrieval_result

    def generate_case_interpretation(self, case_text: str, user_query: str) -> str:
        """Generate an interpretation of a specific case frame in light of the user's query."""
        client = self._get_client()
        prompt = f"""You are a legal assistant. The reader asked a question or provided context, and the system retrieved this legal case as relevant. Write an interpretation that directly addresses what they asked. The case details (title, parties, outcome) are already shown elsewhere — do NOT repeat a summary of the case.

What the reader asked or provided:
---
{user_query}
---

Relevant case text:
---
{case_text[:12000]}
---

Write a clear, concise interpretation (a few paragraphs) that:
1. Explains how this case relates to or answers what the reader asked — address the reader as "you" (e.g. "Your question about…", "For you, the important point is…"). Never refer to "the user".
2. Highlights the key legal principles and facts from the case that are most relevant to what they asked.
3. Keeps a professional but direct tone.

Do not invent facts. Use only the case text above."""

        resp = client.chat.completions.create(
            model=self._synthesis_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )
        return (resp.choices[0].message.content or "").strip()
