import json
from typing import Any, Dict, List, Optional, Tuple

from groq import Groq
from loguru import logger


SYSTEM_PROMPT = """
You are a friendly assistant that can do small talk.

Your main purpose is to retrieve relevant legal case examples from the user's private case database.

Rules:
- If the user asks for precedents / similar cases / case examples OR pastes legal text, you MUST call the tool `search_cases`.
- If the user is doing small talk or general chat, do NOT call tools.
- When the tool returns, reply briefly (e.g. "Sure, here are the most matching cases I found based on the context you provided."). Do NOT list or repeat case details in your message—the actual list is sent to the user in the response body separately.
- Never invent case names, citations, or facts.
- If the tool returns zero results, say you couldn't find matches in the current database and ask the user to refine the text or add more cases.
- After showing results, you may ask ONE short follow-up question to narrow the search (jurisdiction/court/year/topic).
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_cases",
            "description": "Search the case database and return the most relevant case examples.",
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


class ChatService:

    def __init__(self, case_search_service):
        self._case_search_service = case_search_service

    def _get_client(self) -> Groq:
        from config import GROQ_API_KEY
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing.")
        return Groq(api_key=GROQ_API_KEY)

    def run_chat_turn(self, conversation_messages: List[Dict[str, Any]]) -> Tuple[str, Optional[List[Dict[str, Any]]]]:
        client = self._get_client()
        retrieval_result: Optional[List[Dict[str, Any]]] = None

        # First LLM call: check if tool should be called
        resp = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=conversation_messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.6,
            max_tokens=900,
            top_p=1,
            stream=False,
        )

        msg = resp.choices[0].message
        logger.info("First call response: %s", msg)

        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            logger.info("Executing tool calls")
            # Add assistant message with tool calls to conversation
            conversation_messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            })

            # Execute tool calls and add results to conversation
            for tc in tool_calls:
                if tc.function.name == "search_cases":
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        # Fallback if JSON parsing fails
                        args = {"query_text": tc.function.arguments or ""}

                    out = self._case_search_service.run_case_search(
                        query_text=args.get("query_text", ""),
                        top_k=int(args.get("top_k", 10)),
                    )
                    retrieval_result = out.get("retrieval_result", [])
                    content_for_model = json.dumps(out.get("tool_content", {"message": "Done.", "count": 0}))

                    conversation_messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": content_for_model,
                    })

            # Second LLM call: generate final response using tool results
            resp2 = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=conversation_messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.6,
                max_tokens=900,
                top_p=1,
                stream=False,
            )
            msg2 = resp2.choices[0].message.content or ""
            logger.info("Second call response: %s", msg2)
            return msg2, retrieval_result

        logger.info("No tool calls")
        return (msg.content or ""), None
