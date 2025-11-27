# backend/routes/__init__.py  ← THIS IS THE FINAL ONE

from .auth import router as auth_router
from .users import router as users_router
from .profile import router as profile_router
from .sessions import router as sessions_router
from .ratings import router as ratings_router
from .signaling import router as signaling_router
from .teachers import router as teachers_router         # ← THIS LINE WAS MISSING OR WRONG

__all__ = [
    "auth_router",
    "users_router",
    "profile_router",
    "sessions_router",
    "ratings_router",
    "signaling_router",
    "teachers_router",                    # ← THIS MUST BE HERE
]