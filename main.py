# backend/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db

# ──────────────────────────────
# 1. Create app FIRST
# ──────────────────────────────
app = FastAPI(
    title="SkillXchange",
    description="Real-time skill exchange platform with WebRTC video calls, credit economy, and ratings",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ──────────────────────────────
# 2. CORS (must be BEFORE routers)
# ──────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        # Add production frontend when ready:
        # "https://skillxchange.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────
# 3. Uploads folder (before routers OK)
# ──────────────────────────────
if not os.path.exists("uploads"):
    os.makedirs("uploads")

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ──────────────────────────────
# 4. Import routers (AFTER app + CORS exist)
# ──────────────────────────────
from routes import (
    auth_router,
    users_router,
    profile_router,
    sessions_router,
    ratings_router,
    signaling_router,
    teachers_router,
    chat_router,
)

# ──────────────────────────────
# 5. Register routers
# ──────────────────────────────
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profile_router)
app.include_router(sessions_router)
app.include_router(ratings_router)
app.include_router(signaling_router)
app.include_router(teachers_router)
app.include_router(chat_router)

# ──────────────────────────────
# 6. Startup tasks
# ──────────────────────────────
@app.on_event("startup")
def on_startup():
    init_db()
    print("🚀 SkillXchange Backend Online")

@app.on_event("startup")
async def create_message_table():
    from database import engine
    from models import Message
    Message.metadata.create_all(bind=engine, checkfirst=True)
    print("💬 Message table ready")

# ──────────────────────────────
# 7. Health / root
# ──────────────────────────────
@app.get("/")
def root():
    return {
        "message": "SkillXchange Backend is LIVE",
        "status": "success",
        "demo_ready": True,
    }

@app.get("/health")
def health():
    return {"status": "ok"}
