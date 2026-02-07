"""
Chat routes: create conversation, POST /chat/. Conversations and messages are persisted in the DB.
"""
import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from loguru import logger

from api.schemas import (
    ChatResponse,
    ConversationItem,
    CreateConversationResponse,
    MessageItem,
    UserInput,
)
from db.repositories import conversation_repo
from services.chat import SYSTEM_PROMPT, run_chat_turn

router = APIRouter()


@router.get("/conversations/", response_model=list[ConversationItem])
async def list_conversations() -> list[ConversationItem]:
    """List all conversations, newest first."""
    rows = conversation_repo.list_all()
    return [ConversationItem(**r) for r in rows]


@router.get("/conversations/{conversation_id}/messages/", response_model=list[MessageItem])
async def get_conversation_messages(conversation_id: str) -> list[MessageItem]:
    """Get message history for a conversation (user and assistant only)."""
    messages = conversation_repo.get_messages_by_conversation_id(conversation_id)
    return [MessageItem(role=m["role"], content=m["content"]) for m in messages]


@router.post("/conversations/", response_model=CreateConversationResponse)
async def create_conversation() -> CreateConversationResponse:
    """Create a new conversation. Returns conversation_id to use in POST /chat/."""
    conversation_id = str(uuid.uuid4())
    row = conversation_repo.create(conversation_id, user_id=None)
    return CreateConversationResponse(
        conversation_id=row["conversation_id"],
        created_at=row.get("created_at"),
    )

KEEP_LAST_MESSAGES = 10


def _build_messages_for_llm(db_messages: List[Dict[str, Any]], user_text: str) -> List[Dict[str, Any]]:
    """Build message list for Groq: system + (trimmed) history + current user message."""
    out: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in db_messages:
        out.append({"role": m["role"], "content": m["content"]})
    out.append({"role": "user", "content": user_text})
    # Trim to system + last N exchanges to avoid context overflow
    if len(out) > 1 + KEEP_LAST_MESSAGES:
        out = [out[0]] + out[-(KEEP_LAST_MESSAGES):]
    return out


@router.post("/chat/", response_model=ChatResponse)
async def chat(input: UserInput) -> ChatResponse:
    conv = conversation_repo.get_or_create(input.conversation_id, user_id=None)

    if not conv.get("active"):
        raise HTTPException(
            status_code=400,
            detail="The chat session has ended. Please start a new session.",
        )

    try:
        user_text = (input.message or "").strip()
        if not user_text:
            raise HTTPException(status_code=400, detail="Empty message.")

        internal_id = conv["id"]
        db_messages = conversation_repo.get_messages(internal_id)
        messages_for_llm = _build_messages_for_llm(db_messages, user_text)

        response_text, retrieval_result = run_chat_turn(messages_for_llm)

        conversation_repo.add_message(internal_id, "user", user_text)
        conversation_repo.add_message(internal_id, "assistant", response_text)

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
