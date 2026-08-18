from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlmodel import SQLModel, Field, Relationship, Column, DateTime


class AnalysisSession(SQLModel, table=True):
    __tablename__ = "analysis_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(default="未命名分析", max_length=255)
    status: str = Field(default="active", max_length=32)  # active, completed, error
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    # Relationships
    files: List["UploadedFile"] = Relationship(back_populates="session")
    messages: List["ChatMessage"] = Relationship(back_populates="session")
