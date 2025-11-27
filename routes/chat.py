# backend/routes/chat.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from models import Message, User
from auth import get_current_user
from database import get_session


# This is the router name exported in routes/__init__.py
chat_router = APIRouter(prefix="/api/chat", tags=["chat"])


# GET chat history between current user and another user
@chat_router.get("/{receiver_id}/history")
async def get_chat_history(
    receiver_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    # Fetch messages in both directions, newest first
    stmt = select(Message).where(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at.asc())

    messages = db.exec(stmt).all()

    return [
        {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "text": msg.text,
            "timestamp": msg.created_at.isoformat(),
        }
        for msg in messages
    ]


# POST: Send a new message (you will need this soon for real-time)
@chat_router.post("/send")
async def send_message(
    receiver_id: int,
    text: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    new_message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        text=text.strip()
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    return {
        "id": new_message.id,
        "sender_id": new_message.sender_id,
        "receiver_id": new_message.receiver_id,
        "text": new_message.text,
        "timestamp": new_message.created_at.isoformat(),
    }