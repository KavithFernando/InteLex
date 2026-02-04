"""
Chat route: POST /chat/ using schemas and services.chat.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from loguru import logger

from api.schemas import ChatResponse, UserInput
from services.chat import SYSTEM_PROMPT, run_chat_turn


router = APIRouter()

# ----------------------------
# Conversation store (in-memory)
# ----------------------------
class Conversation:
    def __init__(self) -> None:
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
# Endpoint
# ----------------------------
@router.post("/chat/", response_model=ChatResponse)
async def chat(input: UserInput) -> ChatResponse:
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

        response_text, retrieval_result = run_chat_turn(conversation.messages)

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
