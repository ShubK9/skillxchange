# backend/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from typing import List

from database import get_session
from models import User, UserRead
from sqlmodel.ext.asyncio.session import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])

# READABLE USER MODEL (safe for frontend)
class UserRead(SQLModel):
    id: int
    name: str
    email: str
    username: str | None = None
    role: str
    bio: str | None = None
    profile_picture: str | None = None
    teaching_skills: List[str] = []
    rating: float | None = None
    created_at: str | None = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[UserRead])
async def get_all_users(db: AsyncSession = Depends(get_session)):
    """Get all users — used by Explore page"""
    result = await db.exec(select(User))
    users = result.all()
    
    # Convert to list of dicts and ensure teaching_skills is always list
    user_list = []
    for u in users:
        user_data = u.dict()
        user_data["teaching_skills"] = u.teaching_skills or []
        user_list.append(user_data)
    
    return user_list