# backend/routes/chat.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from models import Message, User
from auth import get_current_user
from database import get_session

router = APIRouter(prefix="/api/chat")   # ← THIS IS THE KEY

@router.get("/{receiver_id}/history")
async def get_chat_history(
    receiver_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    stmt = select(Message).where(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == receiver_id)) |
        ((Message.sender_id == receiver_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.created_at)
    
    messages = db.exec(stmt).all()
    
    return [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "text": m.text,
            "timestamp": m.created_at.isoformat()
        }
        for m in messages
    ]