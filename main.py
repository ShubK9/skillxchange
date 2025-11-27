# backend/main.py
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
    chat_router,          # ← ADDED
)

# Create uploads folder if missing
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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Startup: Initialize DB + create message table automatically
@app.on_event("startup")
def on_startup():
    init_db()
    print("SkillXchange Backend — LAUNCHED — Ready for Tomorrow's Demo")

# Auto-create Message table (import inside so no circular error)
@app.on_event("startup")
async def create_message_table():
    from database import engine
    from models import Message        # ← Imported here = NO IMPORT ERROR
    Message.metadata.create_all(bind=engine, checkfirst=True)
    print("Message table ready (created automatically if missing)")

# Mount all routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(profile_router)
app.include_router(sessions_router)
app.include_router(ratings_router)
app.include_router(signaling_router)
app.include_router(teachers_router)
app.include_router(chat_router)          # ← ADDED

# Health & root
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