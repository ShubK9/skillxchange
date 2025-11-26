# backend/database.py
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
import os

# ──────────────────────────────────────────────────────────────
# Get DATABASE_URL from environment (Render injects it automatically)
# Fallback to SQLite for local development
# ──────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

# Local fallback if no env var (great for running locally)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./skillxchange.db"

# Render/Railway give: postgres://user:pass@host:port/db
# SQLModel + SQLAlchemy needs: postgresql+psycopg2://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

# SQLite needs this, PostgreSQL does NOT allow it
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Create engine with best production settings
engine = create_engine(
    DATABASE_URL,
    echo=False,                    # Set True only when debugging SQL
    connect_args=connect_args,
    pool_pre_ping=True,            # Critical for Render (detects dead connections)
    pool_size=10,
    max_overflow=20,
    future=True,                   # SQLAlchemy 2.0+ mode
)

def get_session() -> Generator[Session, None, None]:
    """Dependency for FastAPI routes"""
    with Session(engine) as session:
        yield session

def init_db():
    """Create all tables — called on startup"""
    SQLModel.metadata.create_all(engine)