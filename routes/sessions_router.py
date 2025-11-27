# routes/sessions_router.py   ← add these two endpoints
from models import User, Session as VideoSession
from routes.auth import get_current_user   # ← or wherever your dependency lives
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session as DBSession, select
from database import get_db
from models import User, Session as VideoSession
from datetime import datetime
import uuid

sessions_router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# ← you probably already have this somewhere
# from routes.auth import get_current_user   # <-- make sure this import exists

@sessions_router.post("/request")
async def request_session(
    teacher_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),   # ← renamed to avoid conflict
):
    learner_id = current_user.id

    # Prevent requesting session with yourself
    if learner_id == teacher_id:
        raise HTTPException(status_code=400, detail="Cannot request session with yourself")

    # Create pending session
    session = VideoSession(
        title=f"Live session – {current_user.name}",
        teacher_id=teacher_id,
        learner_id=learner_id,
        scheduled_at=datetime.utcnow(),
        duration_minutes=30,
        status="pending_request",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Unique room name (you can store it in DB later if you want)
    room_name = f"skillxchange_{session.id}_{uuid.uuid4().hex[:10]}"

    return {
        "success": True,
        "session_id": session.id,
        "room_name": room_name,
        "message": "Request sent! Waiting for teacher…"
    }


@sessions_router.post("/accept/{session_id}")
async def accept_session(
    session_id: int,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = db.get(VideoSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the teacher can accept")
    if session.status != "pending_request":
        raise HTTPException(status_code=400, detail="Session already handled")

    session.status = "active"
    db.add(session)
    db.commit()

    room_name = f"skillxchange_{session.id}_{uuid.uuid4().hex[:10]}"

    return {
        "success": True,
        "room_name": room_name,
        "redirect": f"/room/{room_name}"
    }