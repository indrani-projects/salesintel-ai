"""
Chat (grounded follow-up Q&A) API.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app import models
from app.db import get_session
from app.schemas import (
    BriefContent,
    ChatMessageRead,
    ChatRequest,
    ChatResponse,
)
from app.services import chat_service

router = APIRouter(tags=["chat"])


@router.post("/meetings/{meeting_id}/chat", response_model=ChatResponse)
def post_chat(
    meeting_id: int,
    body: ChatRequest,
    session: Session = Depends(get_session),
) -> ChatResponse:
    meeting = session.get(models.Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Chat grounds on the prospect facts; use the primary persona's brief, else
    # any ready brief for this meeting.
    briefs = list(
        session.exec(
            select(models.Brief).where(models.Brief.meeting_id == meeting_id)
        ).all()
    )
    ready = [b for b in briefs if b.status == "ready" and b.content_json]
    brief = next((b for b in ready if b.persona == meeting.persona), None)
    if brief is None:
        brief = ready[0] if ready else None
    if brief is None:
        raise HTTPException(status_code=409, detail="Brief is not ready")

    brief_content = BriefContent.model_validate_json(brief.content_json)

    history = list(
        session.exec(
            select(models.ChatMessage)
            .where(models.ChatMessage.meeting_id == meeting_id)
            .order_by(models.ChatMessage.created_at)
        ).all()
    )
    history_read: List[ChatMessageRead] = [
        ChatMessageRead.model_validate(m, from_attributes=True) for m in history
    ]

    # Persist the user's message.
    user_msg = models.ChatMessage(
        meeting_id=meeting_id, role="user", content=body.question
    )
    session.add(user_msg)
    session.commit()

    response = chat_service.answer_question(
        meeting.company_slug,
        brief_content,
        history_read,
        body.question,
    )

    # Persist the assistant's answer.
    assistant_msg = models.ChatMessage(
        meeting_id=meeting_id, role="assistant", content=response.answer_md
    )
    session.add(assistant_msg)
    session.commit()

    return response


@router.get("/meetings/{meeting_id}/chat", response_model=List[ChatMessageRead])
def get_chat(
    meeting_id: int, session: Session = Depends(get_session)
) -> List[models.ChatMessage]:
    return list(
        session.exec(
            select(models.ChatMessage)
            .where(models.ChatMessage.meeting_id == meeting_id)
            .order_by(models.ChatMessage.created_at)
        ).all()
    )
