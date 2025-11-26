# backend/routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Annotated

from database import get_session
from models import User
from schemas import UserOut
from auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
def list_users(
    current_user: Annotated[User, Depends(get_current_user)],  # ← non-default first
    db: Session = Depends(get_session),                        # ← default second
):
    """Get all users — protected route (login required)"""
    users = db.exec(select(User)).all()
    return users


@router.get("/{user_id}", response_model=UserOut)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_session),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user