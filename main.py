# backend/main.py
import os  # ← ONLY NEW LINE ADDED HERE

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles   # ← NEW IMPORT (only this)

from config import settings
from database import init_db

# Import all routers
from routes import (
    auth_router,
    users_router,
    profile_router,
    sessions_router,
    ratings_router,
    signaling_router,
    teachers_router,
)

# ← CREATE UPLOADS DIRECTORY IF IT DOESN'T EXIST (this fixes the error)
if not os.path.exists("uploads"):
    os.makedirs("uploads")

app = FastAPI(
    title="SkillXchange",
    description="Real-time skill exchange platform with WebRTC video calls, credit economy, and ratings",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ───────────────────────────────────────────────
# CORS — FIXED 100% (keeps your settings + fallback to everything)
# ───────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://skillxchange-w3h2.onrender.com",
        # Keep your settings if they exist, otherwise allow all
    ] + (settings.ALLOWED_ORIGINS if hasattr(settings, "ALLOWED_ORIGINS") else ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────────────────────────────
# NEW: Serve uploaded profile pictures
# ───────────────────────────────────────────────
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ───────────────────────────────────────────────
# Startup: Initialize Database
# ───────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()
    print("SkillXchange Backend — LAUNCHED — Ready for Tomorrow's Demo")

# ───────────────────────────────────────────────
# Mount All API Routes
# ───────────────────────────────────────────────
app.include_router(auth_router)        # /api/auth
app.include_router(users_router)       # /api/users
app.include_router(profile_router)     # /api/profile
app.include_router(sessions_router)    # /api/sessions
app.include_router(ratings_router)     # /api/ratings
app.include_router(signaling_router)   # /ws/signaling/.
app.include_router(teachers_router)    # /api/teachers

# ───────────────────────────────────────────────
# Health & Root
# ───────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "SkillXchange Backend is LIVE",
        "status": "success",
        "demo_ready": True,
        "founder": "legend"
    }

@app.get("/health")
def health():
    return {"status": "ok"}