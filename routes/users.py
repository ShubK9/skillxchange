# backend/routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel, select  # Added SQLModel import
from typing import List, Optional
from database import get_session
from models import User
from sqlmodel.ext.asyncio.session import AsyncSession


router = APIRouter(prefix="/users", tags=["users"])


# ───────────────────────────────────────────────
# SAFE USER MODEL FOR FRONTEND (Explore + Chat)
# ───────────────────────────────────────────────
class UserRead(SQLModel):
    id: int
    name: str
    email: str
    username: Optional[str] = None
    role: str = "both"  # Default value
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    teaching_skills: List[str] = []
    learning_interests: List[str] = []
    rating: Optional[float] = None
    sessions_completed: Optional[int] = None

    class Config:
        from_attributes = True  # Required for SQLModel → Pydantic conversion


# ───────────────────────────────────────────────
# GET ALL USERS — EXPLORE PAGE (Your original logic, just safer)
# ───────────────────────────────────────────────
@router.get("/", response_model=List[UserRead])
async def get_all_users(db: AsyncSession = Depends(get_session)):
    """
    Returns all users with safe fields.
    Used by Explore page and chat.
    """
    result = await db.exec(select(User))
    users = result.all()

    user_list = []
    for user in users:
        # Build correct profile picture URL
        profile_pic = None
        if user.avatar:
            filename = user.avatar.split("/")[-1] if "/" in user.avatar else user.avatar
            profile_pic = f"/uploads/profile-pics/{filename}"

        user_list.append({
            "id": user.id,
            "name": user.name or user.email.split("@")[0],
            "email": user.email,
            "username": user.username,
            "role": user.role or "both",
            "bio": user.bio,
            "profile_picture": profile_pic,
            "teaching_skills": user.teaching_skills or [],
            "learning_interests": user.learning_interests or [],
            "rating": float(user.rating) if user.rating else 4.8,
            "sessions_completed": user.sessions_completed or 0,
        })

    return user_list


# ───────────────────────────────────────────────
# GET SINGLE USER BY ID (Your original + fixed)
# ───────────────────────────────────────────────
@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_session)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile_pic = None
    if user.avatar:
        filename = user.avatar.split("/")[-1] if "/" in user.avatar else user.avatar
        profile_pic = f"/uploads/profile-pics/{filename}"

    return {
        "id": user.id,
        "name": user.name or user.email.split("@")[0],
        "email": user.email,
        "username": user.username,
        "role": user.role or "both",
        "bio": user.bio,
        "profile_picture": profile_pic,
        "teaching_skills": user.teaching_skills or [],
        "learning_interests": user.learning_interests or [],
        "rating": float(user.rating) if user.rating else 4.8,
        "sessions_completed": user.sessions_completed or 0,
    }