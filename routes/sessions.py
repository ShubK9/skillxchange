# backend/routes/sessions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Annotated
from datetime import datetime

from database import get_session
from models import Session as SessionModel, User
from auth import get_current_user

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# ───────────────────────────────────────────────
# Count pending session requests — for notification bell
# ───────────────────────────────────────────────
@router.get("/pending-count")
def pending_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session)
):
    count = db.exec(
        select(SessionModel).where(
            SessionModel.teacher_id == current_user.id,
            SessionModel.status == "pending_request"
        )
    ).count()
    return {"count": count}


# ───────────────────────────────────────────────
# Get full list of requests for PendingRequests.jsx
# ───────────────────────────────────────────────
@router.get("/pending")
def get_pending(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session)
):
    sessions = db.exec(
        select(SessionModel).where(
            SessionModel.teacher_id == current_user.id,
            SessionModel.status == "pending_request"
        )
    ).all()

    # Get learner names & avatars
    learner_ids = {s.learner_id for s in sessions}
    learners = db.exec(select(User).where(User.id.in_(learner_ids))).all()
    learner_map = {u.id: u for u in learners}

    result = []
    for s in sessions:
        learner = learner_map.get(s.learner_id)
        result.append({
            "id": s.id,
            "room_name": s.room_name or f"skillxchange_{s.id}",
            "topic": s.topic,
            "start_time": s.start_time,
            "learner": {
                "id": learner.id,
                "name": learner.name,
                "profilePic": learner.avatar if hasattr(learner, "avatar") else None,
            }
        })

    return result


# ───────────────────────────────────────────────
# Accept a session request — create room & start call
# ───────────────────────────────────────────────
@router.post("/accept/{session_id}")
def accept_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session)
):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    if session.teacher_id != current_user.id:
        raise HTTPException(403, "Not allowed")

    session.status = "active"
    if not session.room_name:
        session.room_name = f"skillxchange_{session.id}"

    db.add(session)
    db.commit()
    db.refresh(session)

    return {"room_name": session.room_name}


# ───────────────────────────────────────────────
# Decline a request
# ───────────────────────────────────────────────
@router.delete("/decline/{session_id}")
def decline_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session)
):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    if session.teacher_id != current_user.id:
        raise HTTPException(403, "Not allowed")

    db.delete(session)
    db.commit()
    return {"message": "Session declined"}


# ───────────────────────────────────────────────
# Get session by ID (used in VideoCall.jsx before websocket)
# ───────────────────────────────────────────────
@router.get("/{session_id}")
def get_session_info(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session)
):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {
        "id": session.id,
        "roomName": session.room_name or f"skillxchange_{session.id}",
        "status": session.status,
        "topic": session.topic
    }


# ───────────────────────────────────────────────
# End call (triggered when clicking end button)
# ───────────────────────────────────────────────
@router.put("/{session_id}/end")
def end_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session)
):
    session = db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    session.status = "completed"
    session.end_time = datetime.utcnow()
    db.add(session)
    db.commit()

    return {"message": "Session ended"}


# ───────────────────────────────────────────────
# Rating after call
# ───────────────────────────────────────────────
@router.post("/{session_id}/rating")
def rate_session(
    session_id: int,
    rating: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session)
):
    session = db.get(SessionModel, session_id)
    if not session or session.status != "completed":
        raise HTTPException(404, "Session not found or not completed yet")

    if rating < 1 or rating > 5:
        raise HTTPExceptio
