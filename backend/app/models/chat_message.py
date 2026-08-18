from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Column, DateTime


class ChatMessage(SQLModel, table=True):
    """Persisted chat message for an analysis session."""

    __tablename__ = "chat_messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[int] = Field(default=None, foreign_key="analysis_sessions.id")
    role: str = Field(max_length=16)  # "user" | "assistant"
    content: str = Field(default="")
    status: Optional[str] = Field(default=None, max_length=32)  # thinking, coding, executing, done
    status_label: Optional[str] = Field(default=None, max_length=64)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    # Relationships
    session: Optional["AnalysisSession"] = Relationship(back_populates="messages")
