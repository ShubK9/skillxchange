# backend/routes/sessions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Annotated
from datetime import datetime
import uuid

from database import get_session
from auth import get_current_user
from models import Session as SModel, User
from schemas import SessionCreate, SessionOut

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# ==================== EXISTING ENDPOINTS (unchanged) ====================

@router.post("/", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    if payload.teacher_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot book yourself")

    teacher = db.get(User, payload.teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    if current_user.credit_points < 5:
        raise HTTPException(status_code=400, detail="Not enough credits (need 5)")

    session = SModel(
        teacher_id=payload.teacher_id,
        learner_id=current_user.id,
        topic=payload.topic or "Skill Exchange Session",
        status="active",
        start_time=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.get("/history", response_model=list[SessionOut])
def get_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    sessions = db.exec(
        select(SModel).where(
            (SModel.teacher_id == current_user.id)
            | (SModel.learner_id == current_user.id)
        ).order_by(SModel.start_time.desc())
    ).all()
    return sessions


@router.get("/{session_id}", response_model=SessionOut)
def get_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    session = db.get(SModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.teacher_id != current_user.id and session.learner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return session


@router.put("/{session_id}/end")
def end_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    session = db.get(SModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "active":
        raise HTTPException(status_code=400, detail="Session already ended")

    if session.teacher_id != current_user.id and session.learner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    session.status = "completed"
    session.end_time = datetime.utcnow()

    teacher = db.get(User, session.teacher_id)
    learner = db.get(User, session.learner_id)

    if teacher and learner:
        teacher.credit_points = (teacher.credit_points or 0) + 10
        learner.credit_points = max(0, (learner.credit_points or 0) - 5)

    db.add(session)
    db.add(teacher)
    db.add(learner)
    db.commit()

    return {"message": "Session ended successfully", "session_id": session.id}


# ==================== NEW: SESSION REQUEST FLOW (added below) ====================

@router.post("/request")
async def request_session(
    teacher_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    """Learner sends a live session request to teacher"""
    learner_id = current_user.id

    if learner_id == teacher_id:
        raise HTTPException(status_code=400, detail="Cannot request session with yourself")

    teacher = db.get(User, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # teacher not found")

    # Optional: check if already has pending request
    existing = db.exec(
        select(SModel).where(
            SModel.teacher_id == teacher_id,
            SModel.learner_id == learner_id,
            SModel.status == "pending_request"
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending request")

    # Create pending session
    session = SModel(
        teacher_id=teacher_id,
        learner_id=learner_id,
        topic="Live Session Request",
        status="pending_request",
        start_time=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    room_name = f"skillxchange_{session.id}_{uuid.uuid4().hex[:10]}"

    return {
        "success": True,
        "session_id": session.id,
        "room_name": room_name,
        "message": "Request sent! Waiting for teacher to accept..."
    }


@router.post("/accept/{session_id}")
async def accept_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    """Teacher accepts the live session request → session becomes active"""
    session = db.get(SModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the teacher can accept this request")

    if session.status != "pending_request":
        raise HTTPException(status_code=400, detail="This request was already handled")

    # Activate the session
    session.status = "active"
    db.add(session)
    db.commit()

    room_name = f"skillxchange_{session.id}_{uuid.uuid4().hex[:10]}"

    return {
        "success": True,
        "room_name": room_name,
        "message": "Session started! Joining room..."
    }
@router.get("/pending-count")
async def get_pending_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    if current_user.role != "teach":
        return {"count": 0}
    
    count = db.exec(
        select(func.count()).select_from(SModel)
        .where(
            SModel.teacher_id == current_user.id,
            SModel.status == "pending_request"
        )
    ).scalar() or 0
    
    return {"count": count}
