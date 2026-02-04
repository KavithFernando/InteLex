import os
import sys
import json
from loguru import logger
from typing import List, Dict, Any, Tuple, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from groq import Groq
import mysql.connector

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("API key for Groq is missing.")

client = Groq(api_key=GROQ_API_KEY)

# DB config for fetching full case records (same as scripts)
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# Import retrieval from scripts (FAISS + MySQL chunk/header fetch)
# Ensure backend dir is on path so "scripts" resolves whether run from backend/ or repo root
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
from scripts.search_cases import search_cases as search_cases_retrieval

# ----------------------------
# FastAPI app
# ----------------------------
app = FastAPI(title="Legal Assistant (Groq + Retrieval)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Prompt + Tool schema
# ----------------------------
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


# ----------------------------
# Lightweight retrieval summaries (case_id, title, date, clauses) for response body
# Full case fetch is left for a separate "get case by id" API when user clicks.
# ----------------------------
def fetch_retrieval_summaries(case_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch case_id, case_title, decision_date, and clauses for the given case_ids.
    Returns list in same order as case_ids; each item has clauses as list of {article, text}.
    """
    if not case_ids:
        return []

    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    placeholders = ",".join(["%s"] * len(case_ids))

    cur.execute(
        f"""
        SELECT case_id, case_title, decision_date 
        FROM cases
        WHERE case_id IN ({placeholders})
        """,
        case_ids,
    )
    case_rows = {r["case_id"]: dict(r) for r in cur.fetchall()}

    cur.execute(
        f"""
        SELECT cc.case_id, cl.article, cl.text
        FROM case_clauses cc
        JOIN clauses cl ON cl.clause_id = cc.clause_id
        WHERE cc.case_id IN ({placeholders})
        """,
        case_ids,
    )
    clauses_by_case: Dict[str, List[Dict[str, Any]]] = {cid: [] for cid in case_ids}
    for r in cur.fetchall():
        clauses_by_case.setdefault(r["case_id"], []).append(
            {"article": r["article"], "text": r["text"]}
        )

    cur.close()
    conn.close()

    out = []
    for cid in case_ids:
        row = case_rows.get(cid)
        if not row:
            continue
        d = {
            "case_id": cid,
            "case_title": row.get("case_title"),
            "decision_date": str(row["decision_date"]) if row.get("decision_date") else None,
            "clauses": clauses_by_case.get(cid, []),
        }
        out.append(d)
    return out


# ----------------------------
# Request/Response models
# ----------------------------
class UserInput(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: str = Field(..., min_length=1)

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    retrieval_result: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top cases: case_id, case_title, decision_date, clauses. Full case via separate API when user clicks.",
    )


# ----------------------------
# Conversation store (in-memory)
# ----------------------------
class Conversation:
    def __init__(self):
        self.messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
        self.active: bool = True

conversations: Dict[str, Conversation] = {}


def get_or_create_conversation(conversation_id: str) -> Conversation:
    if conversation_id not in conversations:
        logger.info("Making new conversation")
        conversations[conversation_id] = Conversation()
    logger.info("Retrieving conversation")
    return conversations[conversation_id]


def trim_history(messages: List[Dict[str, Any]], keep_last: int = 10) -> List[Dict[str, Any]]:
    """
    Keep the system message + last N messages to avoid context blowing up.
    """
    if not messages:
        return [{"role": "system", "content": SYSTEM_PROMPT}]
    system = messages[:1]
    tail = messages[-keep_last:] if len(messages) > 1 else []
    return system + tail

# ----------------------------
# Tool implementation: retrieval + lightweight summaries (for response body only)
# Second Groq call gets only a short message; retrieval_result goes in API response.
# ----------------------------
def search_cases(query_text: str, top_k: int = 10) -> Dict[str, Any]:
    """
    Runs script search_cases (FAISS + MySQL). Builds retrieval_result (case_id, title, date, clauses)
    for response body. Returns tool_content (short message for second Groq call) and retrieval_result.
    """
    retrieval = search_cases_retrieval(
        query_text=query_text,
        top_cases=top_k,
        chunk_recall=None,
        top_chunks_per_case=3,
    )
    results = retrieval.get("results", [])

    case_ids = [r["case_id"] for r in results]
    summaries = fetch_retrieval_summaries(case_ids)

    # Preserve order and add score from search results
    score_by_id = {r["case_id"]: r["score"] for r in results}
    retrieval_result = [
        {**s, "score": score_by_id.get(s["case_id"])}
        for s in summaries
    ]

    count = len(retrieval_result)
    tool_content = {
        "message": f"Found {count} matching case(s) based on the context provided. The list is attached in the response body for the user.",
        "count": count,
    }

    return {"tool_content": tool_content, "retrieval_result": retrieval_result}


# ----------------------------
# Groq call with tool loop (NO streaming)
# ----------------------------
def query_groq_api_with_tools(conversation_messages: List[Dict[str, Any]]) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Tool calling loop. Second Groq call receives only a short tool message (no long payload).
    Returns (response_text, retrieval_result). retrieval_result is the list for the API response body.
    """
    retrieval_result: Optional[List[Dict[str, Any]]] = None

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

        for tc in tool_calls:
            if tc.function.name == "search_cases":
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {"query_text": tc.function.arguments or ""}

                out = search_cases(
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

# ----------------------------
# API endpoint
# ----------------------------
@app.post("/chat/", response_model=ChatResponse)
async def chat(input: UserInput):
    conversation = get_or_create_conversation(input.conversation_id)

    if not conversation.active:
        raise HTTPException(
            status_code=400,
            detail="The chat session has ended. Please start a new session."
        )

    try:
        user_text = (input.message or "").strip()
        if not user_text:
            raise HTTPException(status_code=400, detail="Empty message.")

        # Lock role to user (do NOT trust client-supplied roles)
        conversation.messages.append({"role": "user", "content": user_text})
        conversation.messages = trim_history(conversation.messages)

        # Ask model (and allow it to call tools)
        response_text, retrieval_result = query_groq_api_with_tools(conversation.messages)

        # Save assistant response
        conversation.messages.append({"role": "assistant", "content": response_text})
        conversation.messages = trim_history(conversation.messages)

        return ChatResponse(
            response=response_text,
            conversation_id=input.conversation_id,
            retrieval_result=retrieval_result or [],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected server error")
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------
# Local run
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
