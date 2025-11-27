# backend/models.py
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, JSON
from datetime import datetime


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: Optional[str] = Field(default=None, unique=True, index=True)
    email: str = Field(unique=True, index=True)
    name: str
    password_hash: str
    role: str = Field(default="pending")
    credit_points: int = Field(default=20)
    bio: Optional[str] = None
    avatar: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    learning_interests: List[str] = Field(default=[], sa_type=JSON)
    teaching_skills: List[str] = Field(default=[], sa_type=JSON)

    sessions_as_teacher: List["Session"] = Relationship(
        back_populates="teacher",
        sa_relationship_kwargs={"foreign_keys": "Session.teacher_id"}
    )
    sessions_as_learner: List["Session"] = Relationship(
        back_populates="learner",
        sa_relationship_kwargs={"foreign_keys": "Session.learner_id"}
    )
    ratings_given: List["Rating"] = Relationship(
        back_populates="rater",
        sa_relationship_kwargs={"foreign_keys": "Rating.rater_id"}
    )
    ratings_received: List["Rating"] = Relationship(
        back_populates="ratee",
        sa_relationship_kwargs={"foreign_keys": "Rating.ratee_id"}
    )


class Session(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    scheduled_at: datetime
    duration_minutes: int = Field(default=30)
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    teacher_id: int = Field(foreign_key="user.id")
    learner_id: Optional[int] = Field(default=None, foreign_key="user.id")

    teacher: User = Relationship(back_populates="sessions_as_teacher")
    learner: Optional[User] = Relationship(back_populates="sessions_as_learner")
    ratings: List["Rating"] = Relationship(back_populates="session")


class Rating(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    rating: int = Field(ge=1, le=5)
    review: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    rater_id: int = Field(foreign_key="user.id")
    ratee_id: int = Field(foreign_key="user.id")
    session_id: int = Field(foreign_key="session.id")

    rater: User = Relationship(back_populates="ratings_given")
    ratee: User = Relationship(back_populates="ratings_received")
    session: Session = Relationship(back_populates="ratings")


# ← MESSAGE MODEL — ADDED AT THE END
class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender_id: int = Field(foreign_key="user.id")
    receiver_id: int = Field(foreign_key="user.id")
    text: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)