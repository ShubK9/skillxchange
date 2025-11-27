# backend/routes/sessions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from typing import Annotated
from datetime import datetime

from database import get_session
from auth import get_current_user
from models import Session as SModel, User

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# ==================== REQUEST SESSION ====================
@router.post("/request")
async def request_session(
    request_body: dict,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    # Accept both camelCase and snake_case from frontend
    teacher_id = (
        request_body.get("teacherId")
        or request_body.get("teacher_id")
        or request_body.get("teacherID")
    )

    if not teacher_id:
        raise HTTPException(status_code=422, detail="Missing teacherId")

    try:
        teacher_id = int(teacher_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="teacherId must be a valid number")

    if current_user.id == teacher_id:
        raise HTTPException(status_code=400, detail="Cannot request session with yourself")

    teacher = db.get(User, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Prevent duplicate pending requests
    existing = db.exec(
        select(SModel).where(
            SModel.teacher_id == teacher_id,
            SModel.learner_id == current_user.id,
            SModel.status == "pending_request"
        )
    ).first()

    if existing:
        return {
            "sessionId": existing.id,
            "roomName": f"skillxchange_{existing.id}",
            "status": existing.status
        }

    # Create new session
    session = SModel(
        teacher_id=teacher_id,
        learner_id=current_user.id,
        topic="Live Session",
        status="pending_request",
        start_time=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    room_name = f"skillxchange_{session.id}"

    return {
        "sessionId": session.id,
        "roomName": room_name,
        "status": "pending_request"
    }


# ==================== GET SESSION STATUS ====================
@router.get("/{session_id}")
async def get_session_status(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    session = db.get(SModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Optional: security check (only participants can see status)
    if session.teacher_id != current_user.id and session.learner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return {
        "sessionId": session.id,
        "status": session.status,
        "roomName": f"skillxchange_{session.id}"
    }


# ==================== ACCEPT SESSION ====================
@router.post("/accept/{session_id}")
async def accept_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    session = db.get(SModel, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    if session.teacher_id != current_user.id:
        raise HTTPException(403, "Only the teacher can accept")

    if session.status != "pending_request":
        raise HTTPException(400, "Session is not pending")

    session.status = "active"
    db.add(session)
    db.commit()

    return {
        "roomName": f"skillxchange_{session.id}",
        "message": "Session accepted! Joining room..."
    }


# ==================== PENDING COUNT ====================
@router.get("/pending-count")
async def get_pending_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    if current_user.role not in ["teach", "both"]:
        return {"count": 0}

    count = (
        db.exec(
            select(func.count())
            .select_from(SModel)
            .where(
                SModel.teacher_id == current_user.id,
                SModel.status == "pending_request"
            )
        ).scalar()
        or 0
    )

    return {"count": count}