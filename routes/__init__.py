# backend/routes/__init__.py
from .auth import router as auth_router
from .users import router as users_router
from .profile import router as profile_router
from .sessions import router as sessions_router
from .ratings import router as ratings_router
from .signaling import router as signaling_router
from .teachers import router as teachers_router
from .chat import chat_router  

__all__ = [
    "auth_router",
    "users_router",
    "profile_router",
    "sessions_router",
    "ratings_router",
    "signaling_router",
    "teachers_router",
    "chat_router",  
]


