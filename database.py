# backend/database.py
from typing import Generator
from sqlmodel import SQLModel, create_engine, Session
from config import settings
import os

# ──────────────────────────────────────────────────────────────
# FIX: Railway/Render use postgres:// but SQLAlchemy requires
# postgresql+psycopg2:// for sync driver
# ──────────────────────────────────────────────────────────────
database_url = settings.DATABASE_URL

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)

# SQLite uses different threading rules
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

# Create SQLAlchemy engine
engine = create_engine(
    database_url,
    echo=False,            # change to True only while debugging SQL
    connect_args=connect_args,
    pool_pre_ping=True,   # prevent stale connections on Render/Railway
    pool_size=10,         # safe defaults for production
    max_overflow=20,
)

def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency injection for DB session."""
    with Session(engine) as session:
        yield session

def init_db():
    """Create tables on app startup."""
    SQLModel.metadata.create_all(engine)
