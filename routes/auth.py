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
    # Check email
    if db.exec(select(User).where(User.email == payload.email)).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check username if provided
    if payload.username:
        if db.exec(select(User).where(User.username == payload.username)).first():
            raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    user = User(
        email=payload.email,
        username=payload.username or None,
        name=payload.name or payload.email.split("@")[0],
        password_hash=hash_password(payload.password),
        role="both",  # Default role
        credit_points=50,
        learning_interests=[],
        teaching_skills=[],
        rating=4.8,
        sessions_completed=0,
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
    # Find user by email or username
    user = (
        db.exec(select(User).where(User.email == payload.identifier)).first()
        or (payload.identifier.startswith("@") and db.exec(select(User).where(User.username == payload.identifier[1:])).first())
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
# GET CURRENT USER — PERFECT FOR FRONTEND
# ───────────────────────────────────────────────
@router.get("/me")
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    # Build profile picture URL (your frontend expects this format)
    profile_pic_url = None
    if current_user.avatar:
        filename = current_user.avatar.split("/")[-1] if "/" in current_user.avatar else current_user.avatar
        profile_pic_url = f"/uploads/profile-pics/{filename}"

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name or current_user.email.split("@")[0],
        "username": current_user.username,
        "gender": getattr(current_user, "gender", None),
        "role": current_user.role or "both",
        "learning_interests": current_user.learning_interests or [],
        "teaching_skills": current_user.teaching_skills or [],
        "profilePic": profile_pic_url,           # ← Frontend uses this key
        "creditPoints": current_user.credit_points or 0,
        "rating": float(current_user.rating) if current_user.rating else 4.8,
        "sessionsCompleted": current_user.sessions_completed or 0,
    }


# ───────────────────────────────────────────────
# UPDATE PROFILE (Onboarding + Regular Updates)
# ───────────────────────────────────────────────
@router.put("/me")
def update_profile(
    updates: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_session),
):
    updated = False

    # First-time onboarding (role was "pending")
    if current_user.role == "pending":
        if not updates.role:
            raise HTTPException(status_code=400, detail="Role is required")
        if not updates.learning_interests:
            raise HTTPException(status_code=400, detail="Select at least one learning interest")
        if not updates.teaching_skills:
            raise HTTPException(status_code=400, detail="Select at least one teaching skill")

        current_user.role = updates.role
        current_user.learning_interests = updates.learning_interests
        current_user.teaching_skills = updates.teaching_skills
        updated = True

    # Regular profile updates
    if updates.name is not None:
        current_user.name = updates.name.strip() or current_user.name
        updated = True

    if updates.gender is not None:
        current_user.gender = updates.gender
        updated = True

    if updated:
        db.add(current_user)
        db.commit()
        db.refresh(current_user)

    # Return same format as /me
    profile_pic_url = None
    if current_user.avatar:
        filename = current_user.avatar.split("/")[-1] if "/" in current_user.avatar else current_user.avatar
        profile_pic_url = f"/uploads/profile-pics/{filename}"

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name or current_user.email.split("@")[0],
        "username": current_user.username,
        "gender": current_user.gender,
        "role": current_user.role or "both",
        "learning_interests": current_user.learning_interests or [],
        "teaching_skills": current_user.teaching_skills or [],
        "profilePic": profile_pic_url,
        "creditPoints": current_user.credit_points or 0,
        "rating": float(current_user.rating) if current_user.rating else 4.8,
        "sessionsCompleted": current_user.sessions_completed or 0,
    }