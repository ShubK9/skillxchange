# backend/routes/chat.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from models import Message, User
from auth import get_current_user
from database import get_session

# This is the router name you tried to import
chat_router = APIRouter(prefix="/api/chat", tags=["chat"])

# GET chat history between current user and another user
@chat_router.get("/{receiver_id}/history")
async def get_chat_history(
    receiver_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    # Get messages in both directions
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