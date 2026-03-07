import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.auth_deps import get_current_user
from api.deps import get_chat_service, get_conversation_repo
from api.schemas import (
    ChatResponse,
    ConversationItem,
    CreateConversationResponse,
    MessageItem,
    UserInput,
)
from db.models.user import User
from services.chat import SYSTEM_PROMPT

router = APIRouter()

KEEP_LAST_MESSAGES = 10
MAX_TITLE_LENGTH = 50


def _generate_title_from_message(message: str) -> str:
    if not message:
        return "New Conversation"

    message = message.strip()

    if len(message) <= MAX_TITLE_LENGTH:
        return message

    truncated = message[:MAX_TITLE_LENGTH]
    last_space = truncated.rfind(" ")

    if last_space > MAX_TITLE_LENGTH * 0.5:
        truncated = truncated[:last_space]

    return truncated + "..."


def _build_messages_for_llm(db_messages: List[Dict[str, Any]], user_text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in db_messages:
        out.append({"role": m["role"], "content": m["content"]})
    out.append({"role": "user", "content": user_text})
    if len(out) > 1 + KEEP_LAST_MESSAGES:
        out = [out[0]] + out[-(KEEP_LAST_MESSAGES):]
    return out


@router.get("/conversations/", response_model=list[ConversationItem])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    conversation_repo=Depends(get_conversation_repo),
) -> list[ConversationItem]:
    rows = conversation_repo.list_by_user(current_user.user_id)
    return [ConversationItem(**r) for r in rows]


@router.get("/conversations/{conversation_id}/messages/", response_model=list[MessageItem])
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    conversation_repo=Depends(get_conversation_repo),
) -> list[MessageItem]:
    conv = conversation_repo.get_by_conversation_id(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if conv.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    messages = conversation_repo.get_messages(conv["id"])
    return [
        MessageItem(
            role=m["role"],
            content=m["content"],
            retrieval_result=m.get("retrieval_result"),
        )
        for m in messages
    ]


@router.post("/conversations/", response_model=CreateConversationResponse)
async def create_conversation(
    current_user: User = Depends(get_current_user),
    conversation_repo=Depends(get_conversation_repo),
) -> CreateConversationResponse:
    conversation_id = str(uuid.uuid4())
    row = conversation_repo.create(conversation_id, user_id=current_user.user_id)
    return CreateConversationResponse(
        conversation_id=row["conversation_id"],
        created_at=row.get("created_at"),
    )


@router.post("/chat/", response_model=ChatResponse)
async def chat(
    input: UserInput,
    current_user: User = Depends(get_current_user),
    conversation_repo=Depends(get_conversation_repo),
    chat_service=Depends(get_chat_service),
) -> ChatResponse:
    conv = conversation_repo.get_or_create(input.conversation_id, user_id=current_user.user_id)

    if conv.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

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

        if not conv.get("title") and len(db_messages) == 0:
            title = _generate_title_from_message(user_text)
            conversation_repo.update_title(internal_id, title)

        messages_for_llm = _build_messages_for_llm(db_messages, user_text)

        response_text, retrieval_result = chat_service.run_chat_turn(messages_for_llm)

        conversation_repo.add_message(internal_id, "user", user_text)
        conversation_repo.add_message(
            internal_id,
            "assistant",
            response_text,
            retrieval_result=retrieval_result if retrieval_result else None,
        )

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
