from loguru import logger
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.chat import SYSTEM_PROMPT, query_groq_api_with_tools

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
    """Keep the system message + last N messages to avoid context blowing up."""
    if not messages:
        return [{"role": "system", "content": SYSTEM_PROMPT}]
    system = messages[:1]
    tail = messages[-keep_last:] if len(messages) > 1 else []
    return system + tail


# ----------------------------
# API endpoint (delegates to services.chat only; no direct DB or FAISS)
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

        conversation.messages.append({"role": "user", "content": user_text})
        conversation.messages = trim_history(conversation.messages)

        response_text, retrieval_result = query_groq_api_with_tools(conversation.messages)

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
