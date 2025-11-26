# backend/routes/sessions.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Annotated
from datetime import datetime

from database import get_session
from auth import get_current_user
from models import Session as SModel, User
from schemas import SessionCreate, SessionOut

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("/", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: SessionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    """Learner books a session with a teacher."""
    if payload.teacher_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot book yourself")

    teacher = db.get(User, payload.teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # Check credits
    if current_user.credit_points < 5:
        raise HTTPException(status_code=400, detail="Not enough credits (requires 5)")

    # Deduct credits immediately
    current_user.credit_points -= 5
    db.add(current_user)

    session = SModel(
        teacher_id=payload.teacher_id,
        learner_id=current_user.id,
        topic=payload.topic or "Skill Exchange Session",
        status="pending",  # user joins → becomes active
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
    """Get all past + active sessions for current user."""
    sessions = db.exec(
        select(SModel)
        .where((SModel.teacher_id == current_user.id) | (SModel.learner_id == current_user.id))
        .order_by(SModel.start_time.desc())
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


@router.put("/{session_id}/activate", response_model=SessionOut)
def activate_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    """Mark session as active when WebRTC starts."""
    session = db.get(SModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status != "pending":
        raise HTTPException(status_code=400, detail="Session is already active or ended")

    session.status = "active"
    
    db.add(session)
    db.commit()
    db.refresh(session)

    return session


@router.put("/{session_id}/end", response_model=SessionOut)
def end_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    """End a session — award credits to teacher, enable rating."""
    session = db.get(SModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status not in ["active", "pending"]:
        raise HTTPException(status_code=400, detail="Session already ended")

    if session.teacher_id != current_user.id and session.learner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    session.status = "completed"
    session.end_time = datetime.utcnow()

    teacher = db.get(User, session.teacher_id)

    # Award teacher 10 credits
    if teacher:
        teacher.credit_points = (teacher.credit_points or 0) + 10
        db.add(teacher)

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.put("/{session_id}/cancel", response_model=SessionOut)
def cancel_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    """Cancel session - refund learner, no penalty."""
    session = db.get(SModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.learner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the learner can cancel the session")

    if session.status not in ["pending"]:
        raise HTTPException(status_code=400, detail="Cannot cancel after activation")

    session.status = "cancelled"
    session.end_time = datetime.utcnow()

    # Refund credits
    current_user.credit_points += 5

    db.add(current_user)
    db.add(session)
    db.commit()
    db.refresh(session)

    return session
