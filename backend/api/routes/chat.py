import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.auth_deps import get_current_user
from api.deps import get_chat_service, get_conversation_repo, get_case_repo
from api.schemas import (
    ChatResponse,
    ConversationItem,
    CreateConversationResponse,
    InterpretCaseRequest,
    InterpretCaseResponse,
    MessageItem,
    UserInput,
)
from db.models.user import User
from services.audit import log_audit
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
    if not conv or not conv.get("active"):
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if conv.get("user_id") != current_user.user_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    messages = conversation_repo.get_messages(conv["id"])
    return [
        MessageItem(
            role=m["role"],
            content=m["content"],
            created_at=m.get("created_at"),
            retrieval_result=m.get("retrieval_result"),
        )
        for m in messages
    ]


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    conversation_repo=Depends(get_conversation_repo),
) -> None:
    deleted = conversation_repo.deactivate(conversation_id, current_user.user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    log_audit(
        "chat.delete_conversation",
        user_id=current_user.user_id,
        username=current_user.username,
        resource_type="conversation",
        resource_id=conversation_id,
        success=True,
    )


@router.post("/conversations/", response_model=CreateConversationResponse)
async def create_conversation(
    current_user: User = Depends(get_current_user),
    conversation_repo=Depends(get_conversation_repo),
) -> CreateConversationResponse:
    conversation_id = str(uuid.uuid4())
    row = conversation_repo.create(conversation_id, user_id=current_user.user_id)
    log_audit(
        "chat.create_conversation",
        user_id=current_user.user_id,
        username=current_user.username,
        resource_type="conversation",
        resource_id=conversation_id,
        success=True,
    )
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

        log_audit(
            "chat.send_message",
            user_id=current_user.user_id,
            username=current_user.username,
            resource_type="conversation",
            resource_id=input.conversation_id,
            success=True
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


def _case_text_for_interpretation(case: dict) -> str:
    """Build a single text block from case fields for LLM interpretation."""
    parts = []
    if case.get("case_title"):
        parts.append(f"Title: {case['case_title']}")
    if case.get("legal_issue"):
        parts.append(f"Legal issue: {case['legal_issue']}")
    if case.get("interpretation_summary"):
        parts.append(f"Interpretation summary: {case['interpretation_summary']}")
    if case.get("outcome"):
        parts.append(f"Outcome: {case['outcome']}")
    if case.get("petitioner_claim"):
        parts.append(f"Petitioner's claim: {case['petitioner_claim']}")
    if case.get("respondent_argument"):
        parts.append(f"Respondent's argument: {case['respondent_argument']}")
    if case.get("full_text"):
        parts.append(f"Full text:\n{case['full_text']}")
    if case.get("principles_established"):
        principles = case["principles_established"]
        if isinstance(principles, list):
            parts.append("Principles: " + "; ".join(principles))
        else:
            parts.append(f"Principles: {principles}")
    return "\n\n".join(parts) if parts else ""


@router.post("/chat/interpret-case/", response_model=InterpretCaseResponse)
async def interpret_case(
    body: InterpretCaseRequest,
    current_user: User = Depends(get_current_user),
    case_repo=Depends(get_case_repo),
    chat_service=Depends(get_chat_service),
) -> InterpretCaseResponse:
    """Generate an interpretation of a case in light of the user query that triggered its retrieval."""
    case = case_repo.fetch_case_by_id(body.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    case_text = _case_text_for_interpretation(case)
    if not case_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Case has no text available for interpretation.",
        )
    try:
        interpretation = chat_service.generate_case_interpretation(
            case_text=case_text,
            user_query=body.user_query.strip(),
        )
        return InterpretCaseResponse(interpretation=interpretation)
    except Exception as e:
        logger.exception("Interpret case failed")
        raise HTTPException(status_code=500, detail=str(e))
