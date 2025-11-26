# backend/routes/ratings.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Annotated

from database import get_session
from auth import get_current_user
from models import Rating, Session as SModel, User
from schemas import RatingCreate, RatingOut

router = APIRouter(prefix="/api/ratings", tags=["ratings"])


@router.post("/", response_model=RatingOut, status_code=status.HTTP_201_CREATED)
def submit_rating(
    payload: RatingCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    """Submit rating after a session is completed."""

    # 1. Validate session
    session = db.get(SModel, payload.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Session must be completed
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Can only rate completed sessions")

    # 3. Must be part of session
    if current_user.id not in (session.teacher_id, session.learner_id):
        raise HTTPException(status_code=403, detail="You were not part of this session")

    # 4. Prevent duplicate rating
    existing = db.exec(
        select(Rating).where(Rating.session_id == payload.session_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="This session is already rated")

    # 5. Determine reviewee
    reviewee_id = (
        session.teacher_id
        if current_user.id == session.learner_id
        else session.learner_id
    )

    # 6. Save rating
    rating = Rating(
        session_id=payload.session_id,
        reviewer_id=current_user.id,
        reviewee_id=reviewee_id,
        score=payload.score,
        comment=payload.comment,
    )

    db.add(rating)
    db.commit()
    db.refresh(rating)

    return rating
