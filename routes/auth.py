# backend/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Annotated

from database import get_session
from schemas import (
    UserCreate,
    UserLogin,
    TokenResponse,
    UserOut,
    ProfileUpdate,
)
from models import User
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ───────────────────────────────────────────────
# SIGNUP
# ───────────────────────────────────────────────
@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_session)):
    if db.exec(select(User).where(User.email == payload.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.username and db.exec(select(User).where(User.username == payload.username)).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    if len(payload.password) > 72:
        raise HTTPException(status_code=400, detail="Password too long (max 72 characters)")

    user = User(
        email=payload.email,
        username=payload.username or None,
        name=payload.name or payload.email.split("@")[0],
        password_hash=hash_password(payload.password),
        role="both",
        credit_points=50,
        learning_interests=[],
        teaching_skills=[],
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id))


# ───────────────────────────────────────────────
# LOGIN
# ───────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_session)):
    user = (
        db.exec(select(User).where(User.email == payload.identifier)).first()
        or db.exec(select(User).where(User.username == payload.identifier)).first()
    )

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user.id))


# ───────────────────────────────────────────────
# GET CURRENT USER — CORRECT FOR YOUR DB
# ───────────────────────────────────────────────
@router.get("/me")
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    profile_pic_url = None
    if getattr(current_user, "avatar", None):  # Your actual column name is "avatar"
        filename = current_user.avatar.split("/")[-1] if "/" in current_user.avatar else current_user.avatar
        profile_pic_url = f"/uploads/profile-pics/{filename}"

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name or "",
        "gender": getattr(current_user, "gender", None),
        "role": current_user.role or "both",
        "learning_interests": current_user.learning_interests or [],
        "teaching_skills": current_user.teaching_skills or [],
        "profilePic": profile_pic_url,        # This is what your frontend expects
        "creditPoints": getattr(current_user, "credit_points", 0),
        "rating": getattr(current_user, "rating", 4.8),
        "sessionsCompleted": getattr(current_user, "sessionsCompleted", 0),
    }


# ───────────────────────────────────────────────
# UPDATE PROFILE — ALSO FIXED
# ───────────────────────────────────────────────
@router.put("/me")
def update_profile(
    updates: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    # Onboarding flow (first time completing profile)
    if current_user.role == "pending":
        if not updates.role:
            raise HTTPException(status_code=400, detail="Role is required")
        if not updates.learning_interests or len(updates.learning_interests) == 0:
            raise HTTPException(status_code=400, detail="Select at least one learning interest")
        if not updates.teaching_skills or len(updates.teaching_skills) == 0:
            raise HTTPException(status_code=400, detail="Select at least one teaching skill")

        current_user.role = updates.role
        current_user.learning_interests = updates.learning_interests
        current_user.teaching_skills = updates.teaching_skills

    # Regular updates
    if updates.name:
        current_user.name = updates.name.strip()

    current_user.name = (updates.name or current_user.name or "").strip()

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    # Return consistent format with correct profile pic URL
    profile_pic_url = None
    if getattr(current_user, "avatar", None):
        filename = current_user.avatar.split("/")[-1] if "/" in current_user.avatar else current_user.avatar
        profile_pic_url = f"/uploads/profile-pics/{filename}"

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name or "",
        "gender": getattr(current_user, "gender", None),
        "role": current_user.role or "both",
        "learning_interests": current_user.learning_interests or [],
        "teaching_skills": current_user.teaching_skills or [],
        "profilePic": profile_pic_url,        # Frontend expects "profilePic"
        "creditPoints": getattr(current_user, "credit_points", 0),
        "rating": getattr(current_user, "rating", 4.8),
        "sessionsCompleted": getattr(current_user, "sessionsCompleted", 0),
    }