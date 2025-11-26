# backend/schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ADD THIS LINE — fixes the Pylance error
from sqlmodel import SQLModel


# ───────────────────────────────────────────────
# AUTH
# ───────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: Optional[str] = None
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    identifier: str  # email or username
    password: str


# ───────────────────────────────────────────────
# USER OUTPUT
# ───────────────────────────────────────────────
class UserOut(BaseModel):
    id: int
    username: Optional[str]
    email: EmailStr
    name: Optional[str]
    role: str
    learning_interests: List[str] = []
    teaching_skills: List[str] = []
    credit_points: int
    profile_pic: Optional[str] = None  # ← added default

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):  # ← CHANGE FROM SQLModel TO BaseModel
    name: Optional[str] = None
    role: str
    learning_interests: List[str] = []   # ← default empty list
    teaching_skills: List[str] = []      # ← default empty list

# ───────────────────────────────────────────────
# SESSION
# ───────────────────────────────────────────────
class SessionCreate(BaseModel):
    teacher_id: int
    topic: Optional[str] = None


class SessionOut(BaseModel):
    id: int
    teacher_id: int
    learner_id: int
    topic: Optional[str]
    status: str
    start_time: datetime
    end_time: Optional[datetime]

    model_config = {"from_attributes": True}


# ───────────────────────────────────────────────
# RATING
# ───────────────────────────────────────────────
class RatingCreate(BaseModel):
    session_id: int
    score: int  # 1–5
    comment: Optional[str] = None


class RatingOut(BaseModel):
    id: int
    session_id: int
    reviewer_id: int
    reviewee_id: int
    score: int
    comment: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}