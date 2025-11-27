# backend/auth.py

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from sqlmodel import Session

from config import settings
from database import get_session
from models import User

# ───────────────────────────────────────────────
# Password Hashing
# ───────────────────────────────────────────────
password_hash = PasswordHash.recommended()

# ⚠ tokenUrl MUST be a string (cannot be None) otherwise Render crashes
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",    # only for docs schema — JWT login still works
    auto_error=False               # allows us to manually raise 401
)

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

# ───────────────────────────────────────────────
# JWT Token Creation
# ───────────────────────────────────────────────
def create_access_token(user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

# ───────────────────────────────────────────────
# Get Current User — PRIMARY AUTH FUNCTION
# ───────────────────────────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError()
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

# ───────────────────────────────────────────────
# Optional current user (for public routes)
# ───────────────────────────────────────────────
async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
) -> Optional[User]:
    if not token:
        return None
    try:
        return await get_current_user(token, db)
    except Exception:
        return None

# ───────────────────────────────────────────────
# Allow pending users (onboarding)
# ───────────────────────────────────────────────
async def get_current_user_allow_pending(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_session)
) -> User:
    user = await get_current_user(token, db)
    return user  # pending users allowed by design

# ──────────────────────────────────────────────────────
# GET /auth/me — Return full profile with correct pic URL
# ──────────────────────────────────────────────────────
async def get_current_user_profile(
    current_user: User = Depends(get_current_user_allow_pending)
) -> dict:
    profile_pic = None
    if getattr(current_user, "profilePic", None):
        filename = current_user.profilePic.split("/")[-1]
        profile_pic = f"/uploads/profile-pics/{filename}"

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name or "",
        "gender": current_user.gender,
        "role": current_user.role or "both",
        "learning_interests": current_user.learning_interests or [],
        "teaching_skills": current_user.teaching_skills or [],
        "profilePic": profile_pic,
        "creditPoints": getattr(current_user, "creditPoints", 0) or 0,
        "rating": getattr(current_user, "rating", 4.8) or 4.8,
        "sessionsCompleted": getattr(current_user, "sessionsCompleted", 0) or 0,
    }
